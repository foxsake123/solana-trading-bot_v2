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
        self.db = None # This should be initialized properly, e.g., via a setup method
        
        # Track analyzed tokens to avoid duplicates
        self.analyzed_tokens: Set[str] = set()
        self.last_scan_time = 0
        self.scan_interval = config.get('scan_interval', 300)  # Default to 300 seconds from your log
        
        # Initialize Birdeye API if key provided
        if self.birdeye_api_key:
            self.birdeye_api = BirdeyeAPI(self.birdeye_api_key)
            logger.info(f"TokenScanner initialized with Birdeye API.")
        else:
            logger.warning("TokenScanner initialized without Birdeye API key")

    def set_db(self, db):
        """Set the database instance for the scanner."""
        self.db = db
        logger.info("Database instance set for TokenScanner.")

    async def start_scanning(self):
        """Start the token scanning loop"""
        logger.info(f"Token scanner started - scanning every {self.scan_interval} seconds.")

        # Use the more robust MarketDataAggregator for all scanning
        aggregator = MarketDataAggregator(self.birdeye_api_key)

        while True:
            try:
                logger.info("Scanning for new tokens using MarketDataAggregator...")

                # Discover new tokens using the aggregator
                # This method is more robust and has fallbacks.
                discovered_tokens = await aggregator.discover_tokens(max_tokens=100)

                if discovered_tokens:
                    logger.info(f"Discovered {len(discovered_tokens)} tokens from aggregator.")

                    # Analyze each token
                    for token in discovered_tokens:
                        try:
                            # Skip if already processed in this session to avoid redundant work
                            address = token.get('address')
                            if not address or address in self.analyzed_tokens:
                                continue

                            # Add to the set of analyzed tokens for this session
                            self.analyzed_tokens.add(address)

                            # Analyze the token using your existing analyzer
                            # Ensure your TokenAnalyzer can handle the data structure from Birdeye
                            analysis_result = await self.token_analyzer.analyze(token)

                            # Check if the token is promising based on your score
                            # The score threshold is from your config
                            min_score = self.config.get('min_token_score', 0.7)
                            if analysis_result and analysis_result.get('score', 0) > min_score:
                                logger.info(f"Found promising token: {token.get('symbol')} (Score: {analysis_result.get('score', 0):.2f}). Storing in DB.")
                                # The trading_bot logic will pick it up from the DB
                                if self.db:
                                    self.db.store_token(token_data={**token, **analysis_result})
                                else:
                                    logger.error("Database not initialized in TokenScanner. Cannot store token.")

                        except Exception as e:
                            logger.error(f"Error analyzing token {token.get('symbol', 'N/A')}: {e}", exc_info=True)

                else:
                    logger.warning("Token scanner did not receive any tokens from market data source.")

                # Wait for the next scan interval
                await asyncio.sleep(self.scan_interval)

            except Exception as e:
                logger.critical(f"A critical error occurred in the main scanner loop: {e}", exc_info=True)
                # Wait longer on critical errors to prevent rapid-fire failures
                await asyncio.sleep(60)

    def _should_analyze_token(self, token: Dict) -> bool:
        """
        Check if a token should be analyzed based on basic criteria
        
        :param token: Token data dictionary
        :return: True if token should be analyzed
        """
        # Check minimum volume
        min_volume = self.config.get('min_volume_24h', 10000)
        if token.get('v24hUSD', 0) < min_volume: # Adjusted to a common Birdeye field name
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
            # This method might need to be part of your BirdeyeAPI class
            tokens = await self.birdeye_api.get_trending_tokens(limit=20)
            return tokens
        except Exception as e:
            logger.error(f"Error getting trending tokens: {e}")
            return []
            
    async def get_token_details(self, contract_address: str) -> Optional[Dict]:
        """Get detailed information about a specific token"""
        if not self.birdeye_api:
            return None
            
        try:
            # These methods might need to be part of your BirdeyeAPI class
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