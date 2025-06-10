# core/data/birdeye_top_traders.py
"""
Birdeye Top Traders API Integration
Tracks whale movements and smart money activity
"""

import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class BirdeyeTopTraders:
    """Birdeye API integration for whale tracking"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {
            "X-API-KEY": api_key,
            "Accept": "application/json"
        }
        
        # Cache for API calls
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    async def get_top_traders_activity(self, token_address: str) -> Dict:
        """Get top traders' recent activity for a token"""
        
        # Check cache
        cache_key = f"traders_{token_address}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            # Get token holders
            holders_data = await self._get_token_holders(token_address)
            
            # Get recent transactions
            txn_data = await self._get_recent_transactions(token_address)
            
            # Analyze whale movements
            analysis = self._analyze_whale_movements(holders_data, txn_data)
            
            # Cache result
            self.cache[cache_key] = (datetime.now(), analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting top traders activity: {e}")
            return self._empty_analysis()
    
    async def _get_token_holders(self, token_address: str) -> Dict:
        """Get top token holders"""
        
        url = f"{self.base_url}/defi/token_holders"
        params = {
            "address": token_address,
            "limit": 50,
            "offset": 0
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.error(f"Birdeye API error: {response.status}")
                    return {}
    
    async def _get_recent_transactions(self, token_address: str) -> List:
        """Get recent large transactions"""
        
        url = f"{self.base_url}/defi/token_transaction"
        params = {
            "address": token_address,
            "limit": 100,
            "tx_type": "swap",
            "sort_type": "desc",
            "sort_by": "blockUnixTime"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('items', [])
                else:
                    return []
    
    def _analyze_whale_movements(self, holders_data: Dict, transactions: List) -> Dict:
        """Analyze whale buy/sell patterns"""
        
        # Get top holders
        holders = holders_data.get('items', [])
        if not holders:
            return self._empty_analysis()
        
        # Calculate total supply held by top holders
        top_10_supply = sum(h.get('uiAmount', 0) for h in holders[:10])
        top_20_supply = sum(h.get('uiAmount', 0) for h in holders[:20])
        
        # Analyze recent whale transactions
        whale_buys = 0
        whale_sells = 0
        whale_volume = 0
        
        # Track unique whale addresses
        whale_addresses = {h['address'] for h in holders[:20]}
        
        for tx in transactions:
            # Check if transaction involves a whale
            from_address = tx.get('from', {}).get('address', '')
            to_address = tx.get('to', {}).get('address', '')
            
            if from_address in whale_addresses or to_address in whale_addresses:
                amount_usd = tx.get('uiAmountUSD', 0)
                whale_volume += amount_usd
                
                # Determine if buy or sell
                if to_address in whale_addresses:
                    whale_buys += 1
                else:
                    whale_sells += 1
        
        # Calculate whale score (0-1)
        if whale_buys + whale_sells > 0:
            buy_ratio = whale_buys / (whale_buys + whale_sells)
        else:
            buy_ratio = 0.5
        
        # Adjust score based on concentration
        concentration_penalty = min(top_10_supply / 100, 0.3)  # Max 30% penalty
        whale_score = buy_ratio * (1 - concentration_penalty)
        
        # Determine signals
        whale_accumulation = whale_score > 0.7 and whale_buys > whale_sells * 1.5
        whale_distribution = whale_score < 0.3 and whale_sells > whale_buys * 1.5
        
        return {
            'whale_accumulation': whale_accumulation,
            'whale_distribution': whale_distribution,
            'whale_score': whale_score,
            'top_10_concentration': top_10_supply,
            'top_20_concentration': top_20_supply,
            'whale_transactions': {
                'buys': whale_buys,
                'sells': whale_sells,
                'volume_usd': whale_volume,
                'buy_ratio': buy_ratio
            },
            'holder_count': len(holders),
            'analysis_timestamp': datetime.now()
        }
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'whale_accumulation': False,
            'whale_distribution': False,
            'whale_score': 0.5,
            'top_10_concentration': 0,
            'top_20_concentration': 0,
            'whale_transactions': {
                'buys': 0,
                'sells': 0,
                'volume_usd': 0,
                'buy_ratio': 0.5
            },
            'holder_count': 0,
            'analysis_timestamp': datetime.now()
        }
    
    async def get_market_leaders(self, limit: int = 10) -> List[Dict]:
        """Get tokens with highest smart money activity"""
        
        url = f"{self.base_url}/defi/token_trending"
        params = {
            "sort_by": "volume24hUSD",
            "sort_type": "desc",
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        leaders = []
                        for token in data.get('data', {}).get('items', []):
                            # Get whale activity for each
                            whale_data = await self.get_top_traders_activity(
                                token['address']
                            )
                            
                            if whale_data['whale_accumulation']:
                                leaders.append({
                                    'symbol': token.get('symbol', 'UNKNOWN'),
                                    'address': token['address'],
                                    'whale_score': whale_data['whale_score'],
                                    'volume_24h': token.get('volume24hUSD', 0),
                                    'price_change_24h': token.get('priceChange24h', 0)
                                })
                        
                        # Sort by whale score
                        leaders.sort(key=lambda x: x['whale_score'], reverse=True)
                        return leaders[:limit]
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting market leaders: {e}")
            return []
    
    async def check_smart_money_flow(self, token_address: str) -> Dict:
        """Check if smart money is flowing in or out"""
        
        # Get historical holder data (if available)
        analysis = await self.get_top_traders_activity(token_address)
        
        # Classify the flow
        if analysis['whale_accumulation']:
            flow = 'INFLOW'
            strength = analysis['whale_score']
            signal = f"Smart money accumulating - {analysis['whale_transactions']['buys']} whale buys"
        elif analysis['whale_distribution']:
            flow = 'OUTFLOW'
            strength = 1 - analysis['whale_score']
            signal = f"Smart money exiting - {analysis['whale_transactions']['sells']} whale sells"
        else:
            flow = 'NEUTRAL'
            strength = 0.5
            signal = "No clear smart money direction"
        
        return {
            'flow': flow,
            'strength': strength,
            'signal': signal,
            'details': analysis
        }
