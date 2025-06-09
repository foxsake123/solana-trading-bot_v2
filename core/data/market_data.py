import time
import logging
import aiohttp
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, UTC

logger = logging.getLogger('trading_bot.birdeye_api')

class BirdeyeAPI:
    """
    Birdeye API client for token data
    """
    
    def __init__(self):
        from config.bot_config import BotConfiguration
        self.api_key = BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY', '')
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {"X-API-KEY": self.api_key}
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Rate limiting
        self.last_request = 0
        self.min_request_interval = 0.5  # 500ms between requests (Starter plan limit)
        
        logger.info(f"BirdeyeAPI initialized with API key: {'*' * 8}{self.api_key[-4:]}")
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request
        
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        self.last_request = time.time()
    
    def _is_fake_token(self, address: str) -> bool:
        """Simple fake token check"""
        if not address or not isinstance(address, str):
            return True
        
        lower_address = address.lower()
        
        # Check for suspicious patterns
        suspicious_terms = ['scam', 'fake', 'test', 'demo']
        for term in suspicious_terms:
            if term in lower_address:
                return True
        
        return False
    
    async def get_token_list(self, sort_by='v24hUSD', sort_type='desc', offset=0, limit=50):
        """Get trending tokens from Birdeye"""
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/defi/v3/token/list"
        params = {
            'sort_by': sort_by,
            'sort_type': sort_type,
            'offset': offset,
            'limit': limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Birdeye API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    tokens = data.get('data', {}).get('items', [])
                    
                    # Convert Birdeye format to our standard format
                    formatted_tokens = []
                    for token in tokens:
                        if self._is_fake_token(token.get('address', '')):
                            continue
                            
                        formatted_token = self._format_birdeye_token(token)
                        formatted_tokens.append(formatted_token)
                    
                    logger.info(f"Retrieved {len(formatted_tokens)} tokens from Birdeye")
                    return formatted_tokens
                    
        except Exception as e:
            logger.error(f"Error fetching token list: {e}")
            return []
    
    def _format_birdeye_token(self, token: Dict) -> Dict:
        """Convert Birdeye token format to standard format"""
        return {
            'address': token.get('address', ''),
            'contract_address': token.get('address', ''),
            'symbol': token.get('symbol', 'UNKNOWN'),
            'ticker': token.get('symbol', 'UNKNOWN'),
            'name': token.get('name', 'UNKNOWN'),
            'decimals': token.get('decimals', 9),
            'price': {'value': float(token.get('price', 0))},
            'price_usd': float(token.get('price', 0)),
            'volume': {'value': float(token.get('v24hUSD', 0))},
            'volume_24h': float(token.get('v24hUSD', 0)),
            'liquidity': {'value': float(token.get('liquidity', 0))},
            'liquidity_usd': float(token.get('liquidity', 0)),
            'priceChange': {
                '24H': float(token.get('v24hChangePercent', 0)),
                '1H': float(token.get('v1hChangePercent', 0)),
                '6H': 0  # Not provided by Birdeye in list endpoint
            },
            'price_change_24h': float(token.get('v24hChangePercent', 0)),
            'price_change_1h': float(token.get('v1hChangePercent', 0)),
            'price_change_6h': 0,
            'mc': {'value': float(token.get('mc', 0))},
            'market_cap': float(token.get('mc', 0)),
            'mcap': float(token.get('mc', 0)),
            'holders': token.get('holder', 0),
            'holdersCount': token.get('holder', 0)
        }
    
    async def get_token_info(self, contract_address: str) -> Optional[Dict]:
        """Get detailed token information"""
        if not contract_address or not isinstance(contract_address, str):
            return None
        
        if self._is_fake_token(contract_address):
            return None
        
        # Check cache
        cache_key = f"token_info_{contract_address}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_duration:
                return cache_entry['data']
        
        try:
            await self._wait_for_rate_limit()
            
            url = f"{self.base_url}/defi/v3/token/overview"
            params = {'address': contract_address}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    token_data = data.get('data', {})
                    
                    if not token_data:
                        return None
                    
                    # Format the detailed token info
                    token_info = self._format_birdeye_token(token_data)
                    
                    # Add additional fields from overview endpoint
                    token_info['price_change_6h'] = float(token_data.get('v6hChangePercent', 0))
                    token_info['priceChange']['6H'] = float(token_data.get('v6hChangePercent', 0))
                    
                    # Cache the result
                    self.cache[cache_key] = {
                        'timestamp': time.time(),
                        'data': token_info
                    }
                    
                    return token_info
        
        except Exception as e:
            logger.error(f"Error getting token info for {contract_address}: {e}")
            return None
    
    async def get_token_security_info(self, contract_address: str) -> Optional[Dict]:
        """Get token security information"""
        await self._wait_for_rate_limit()
        
        try:
            url = f"{self.base_url}/defi/v3/token/security"
            params = {'address': contract_address}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    security_data = data.get('data', {})
                    
                    return {
                        'securityScore': 100 - (security_data.get('risks', 0) * 10),  # Simple scoring
                        'liquidityLocked': security_data.get('isLpLocked', False),
                        'mintingDisabled': security_data.get('isMintable', True) == False,
                        'isMemeToken': security_data.get('isMeme', False),
                        'risks': security_data.get('risks', 0)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting security info: {e}")
            return None
    
    async def get_top_gainers(self, timeframe: str = '24h', limit: int = 10) -> List[Dict]:
        """Get top gaining tokens"""
        cache_key = f"top_gainers_{timeframe}_{limit}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_duration:
                return cache_entry['data']
        
        # Map timeframe to sort_by parameter
        sort_by_map = {
            '1h': 'v1hChangePercent',
            '24h': 'v24hChangePercent'
        }
        sort_by = sort_by_map.get(timeframe, 'v24hChangePercent')
        
        tokens = await self.get_token_list(sort_by=sort_by, limit=limit * 2)
        
        # Filter for positive gainers with volume
        gainers = []
        for token in tokens:
            price_change_key = f'price_change_{timeframe[:-1]}h'
            price_change = token.get(price_change_key, 0)
            
            if price_change > 1 and token.get('volume_24h', 0) > 5000:
                gainers.append(token)
        
        result = gainers[:limit]
        
        # Cache result
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': result
        }
        
        logger.info(f"Found {len(result)} top gainers for {timeframe}")
        return result
    
    async def get_trending_tokens(self, limit: int = 10) -> List[Dict]:
        """Get trending tokens by volume"""
        cache_key = f"trending_tokens_{limit}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_duration:
                return cache_entry['data']
        
        # Get by volume
        tokens = await self.get_token_list(sort_by='v24hUSD', limit=limit * 2)
        
        # Filter by volume and liquidity thresholds
        trending = []
        for token in tokens:
            if (token.get('volume_24h', 0) > 10000 and 
                token.get('liquidity_usd', 0) > 10000):
                trending.append(token)
        
        result = trending[:limit]
        
        # Cache result
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'data': result
        }
        
        logger.info(f"Found {len(result)} trending tokens")
        return result
    
    async def get_token_price(self, contract_address: str) -> Optional[float]:
        """Get token price"""
        token_info = await self.get_token_info(contract_address)
        if token_info:
            return token_info.get('price_usd', 0)
        return None
    
    async def get_token_volume(self, contract_address: str) -> Optional[float]:
        """Get 24h volume"""
        token_info = await self.get_token_info(contract_address)
        if token_info:
            return token_info.get('volume_24h', 0)
        return None
    
    async def get_token_liquidity(self, contract_address: str) -> Optional[float]:
        """Get liquidity"""
        token_info = await self.get_token_info(contract_address)
        if token_info:
            return token_info.get('liquidity_usd', 0)
        return None
    
    async def get_holders_count(self, contract_address: str) -> Optional[int]:
        """Get holders count"""
        token_info = await self.get_token_info(contract_address)
        if token_info:
            return token_info.get('holders', 0)
        return 0
    
    async def get_market_cap(self, contract_address: str) -> Optional[float]:
        """Get market cap"""
        token_info = await self.get_token_info(contract_address)
        if token_info:
            return token_info.get('market_cap', 0)
        return None
    
    async def get_price_change(self, contract_address: str, timeframe: str) -> Optional[float]:
        """Get price change"""
        token_info = await self.get_token_info(contract_address)
        if not token_info:
            return None
        
        if timeframe == '1h':
            return token_info.get('price_change_1h', 0)
        elif timeframe == '6h':
            return token_info.get('price_change_6h', 0)
        elif timeframe == '24h':
            return token_info.get('price_change_24h', 0)
        
        return None