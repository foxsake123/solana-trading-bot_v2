# core/data/token_scanner.py
"""
Token scanner module for discovering and analyzing potential trading opportunities
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from core.data.market_data import BirdeyeAPI, MarketDataAggregator
from core.analysis.token_analyzer import TokenAnalyzer
from utils.helpers import fetch_with_retries

logger = logging.getLogger(__name__)


class TokenScanner:
    """
    Scans for potential tokens using multiple data sources
    """
    
    async def start_scanning(self):
        """Start the token scanning loop"""
        logger.info("Token scanner started - scanning every %d seconds", self.scan_interval)
        
        while True:
            try:
                # Discover new tokens
                logger.info("Scanning for new tokens...")
                
                # Get top gainers
                if hasattr(self, 'birdeye_api') and self.birdeye_api:
                    try:
                        tokens = await self.birdeye_api.get_token_list(limit=10)
                        if tokens:
                            logger.info(f"Found {len(tokens)} tokens from Birdeye")
                            
                            # Analyze each token
                            for token in tokens:
                                try:
                                    # Skip if already processing
                                    address = token.get('address', '')
                                    if not address:
                                        continue
                                    
                                    # Analyze token
                                    if self.token_analyzer:
                                        analysis = await self.token_analyzer.analyze(token)
                                        
                                        # Store in database if good
                                        if analysis.get('score', 0) > 0.5:
                                            if self.db:
                                                self.db.store_token(token)
                                            logger.info(f"Found promising token: {token.get('symbol')} (score: {analysis.get('score', 0):.2f})")
                                    
                                except Exception as e:
                                    logger.error(f"Error analyzing token: {e}")
                                    
                    except Exception as e:
                        logger.error(f"Error getting tokens: {e}")
                
                # Wait before next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(10)  # Wait 10 seconds on error

    def __init__(self, config: Dict, token_analyzer: TokenAnalyzer, birdeye_api_key: Optional[str] = None):
        """
        Initialize the TokenScanner
        
        :param config: Bot configuration dictionary
        :param token_analyzer: TokenAnalyzer instance for token analysis
        :param birdeye_api_key: Birdeye API key (optional)
        """
        self.config = config
        self.token_analyzer = token_analyzer
        self.birdeye_api_key = birdeye_api_key
        self.birdeye_api = None
        
        # Track analyzed tokens to avoid duplicates
        self.analyzed_tokens: Set[str] = set()
        self.last_scan_time = 0
        self.scan_interval = config.get('scan_interval', 60)  # seconds
        
        # Initialize Birdeye API if key provided
        if self.birdeye_api_key:
            self.birdeye_api = BirdeyeAPI(self.birdeye_api_key)
            logger.info(f"TokenScanner initialized with Birdeye API: {self.birdeye_api.is_available}")
        else:
            logger.warning("TokenScanner initialized without Birdeye API key")
            
    async def scan_for_tokens(self) -> List[Dict]:
        """Scan for potential tokens using Birdeye v3 API and fallbacks"""
        logger.info("Scanning for tokens...")
        
        try:
            # Use MarketDataAggregator for better reliability
            aggregator = MarketDataAggregator(self.birdeye_api_key)
            discovered_tokens = await aggregator.discover_tokens(max_tokens=50)
            
            if not discovered_tokens:
                logger.warning("No tokens found from primary sources")
                return []
                
            logger.info(f"Found {len(discovered_tokens)} tokens to analyze")
            
            # Analyze tokens
            analyzed_tokens = []
            for token in discovered_tokens:
                try:
                    # Skip if we've seen this recently
                    if token.get('contract_address') in self.analyzed_tokens:
                        continue
                        
                    # Basic filtering
                    if not self._should_analyze_token(token):
                        continue
                        
                    # Analyze with token_analyzer
                    analysis = await self.token_analyzer.analyze(token)
                    
                    if analysis.get('score', 0) >= self.config.get('min_token_score', 0.7):
                        token_with_analysis = {**token, **analysis}
                        analyzed_tokens.append(token_with_analysis)
                        self.analyzed_tokens.add(token['contract_address'])
                        
                except Exception as e:
                    logger.error(f"Error analyzing token {token.get('symbol')}: {e}")
                    continue
                    
            logger.info(f"Analyzed {len(analyzed_tokens)} tokens successfully")
            return analyzed_tokens
            
        except Exception as e:
            logger.error(f"Token scanning error: {e}")
            return []
            
    def _should_analyze_token(self, token: Dict) -> bool:
        """
        Check if a token should be analyzed based on basic criteria
        
        :param token: Token data dictionary
        :return: True if token should be analyzed
        """
        # Check minimum volume
        min_volume = self.config.get('min_volume_24h', 10000)
        if token.get('volume_24h', 0) < min_volume:
            return False
            
        # Check minimum liquidity
        min_liquidity = self.config.get('min_liquidity', 5000)
        if token.get('liquidity', 0) < min_liquidity:
            return False
            
        # Skip stablecoins if configured
        if not self.config.get('trade_stablecoins', False):
            stable_symbols = ['USDC', 'USDT', 'DAI', 'BUSD', 'UST']
            if token.get('symbol', '').upper() in stable_symbols:
                return False
                
        # Skip if price is 0 or missing
        if not token.get('price') or token['price'] == 0:
            return False
            
        return True
        
    async def get_trending_tokens(self) -> List[Dict]:
        """Get trending tokens from Birdeye"""
        if not self.birdeye_api:
            logger.warning("Birdeye API not available")
            return []
            
        try:
            async with self.birdeye_api:
                tokens = await self.birdeye_api.get_trending_tokens(limit=20)
                return tokens
        except Exception as e:
            logger.error(f"Error getting trending tokens: {e}")
            return []
            
    async def get_top_gainers(self) -> List[Dict]:
        """Get top gaining tokens"""
        if not self.birdeye_api:
            return []
            
        try:
            async with self.birdeye_api:
                tokens = await self.birdeye_api.get_top_gainers(limit=20)
                return tokens
        except Exception as e:
            logger.error(f"Error getting top gainers: {e}")
            return []
            
    async def get_token_details(self, contract_address: str) -> Optional[Dict]:
        """Get detailed information about a specific token"""
        if not self.birdeye_api:
            return None
            
        try:
            async with self.birdeye_api:
                overview = await self.birdeye_api.get_token_overview(contract_address)
                security = await self.birdeye_api.get_token_security(contract_address)
                
                if overview:
                    if security:
                        overview['security'] = security
                    return overview
                    
        except Exception as e:
            logger.error(f"Error getting token details: {e}")
            
        return None
        
    def clear_analyzed_tokens(self):
        """Clear the set of analyzed tokens (call periodically)"""
        self.analyzed_tokens.clear()
        logger.info("Cleared analyzed tokens cache")
        
    async def continuous_scan(self, callback=None):
        """
        Continuously scan for tokens at specified intervals
        
        :param callback: Optional callback function to call with discovered tokens
        """
        logger.info(f"Starting continuous token scanning (interval: {self.scan_interval}s)")
        
        while True:
            try:
                current_time = time.time()
                
                # Check if enough time has passed
                if current_time - self.last_scan_time >= self.scan_interval:
                    tokens = await self.scan_for_tokens()
                    
                    if tokens and callback:
                        await callback(tokens)
                        
                    self.last_scan_time = current_time
                    
                    # Clear analyzed tokens periodically (every hour)
                    if len(self.analyzed_tokens) > 1000:
                        self.clear_analyzed_tokens()
                        
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in continuous scan: {e}")
                await asyncio.sleep(30)  # Wait longer on error