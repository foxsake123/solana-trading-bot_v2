# birdeye_fix.py
"""
Fix for Birdeye API v3 integration
Optimized for Starter package (100 requests/minute)
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BirdeyeAPIv3:
    """Birdeye API v3 implementation for Starter package"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so"
        self.headers = {
            "X-API-KEY": api_key,
            "Accept": "application/json"
        }
        self.rate_limit = 100  # Starter package: 100 requests/minute
        self.request_count = 0
        self.last_reset = datetime.now()
        
    async def _rate_limit_check(self):
        """Ensure we don't exceed rate limits"""
        now = datetime.now()
        if (now - self.last_reset).seconds >= 60:
            self.request_count = 0
            self.last_reset = now
        
        if self.request_count >= self.rate_limit - 5:  # Safety margin
            wait_time = 60 - (now - self.last_reset).seconds
            logger.warning(f"Rate limit approaching, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.last_reset = datetime.now()
    
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens using v3 API"""
        await self._rate_limit_check()
        
        url = f"{self.base_url}/defi/v3/token/list"
        params = {
            "sort_by": "volume24hUSD",
            "sort_type": "desc",
            "limit": min(limit, 50),  # Max 50 per request
            "offset": 0
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    self.request_count += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        tokens = data.get('data', {}).get('items', [])
                        
                        # Filter for quality tokens
                        quality_tokens = []
                        for token in tokens:
                            if (token.get('volume24hUSD', 0) > 10000 and
                                token.get('liquidity', 0) > 25000 and
                                token.get('priceChange24h', 0) > 5):
                                quality_tokens.append({
                                    'contract_address': token['address'],
                                    'symbol': token.get('symbol', 'UNKNOWN'),
                                    'name': token.get('name', ''),
                                    'price': token.get('price', 0),
                                    'volume_24h': token.get('volume24hUSD', 0),
                                    'liquidity_usd': token.get('liquidity', 0),
                                    'price_change_24h': token.get('priceChange24h', 0),
                                    'mcap': token.get('marketCap', 0),
                                    'holders': token.get('holder', 0)
                                })
                        
                        logger.info(f"Found {len(quality_tokens)} quality tokens from Birdeye")
                        return quality_tokens
                    else:
                        logger.error(f"Birdeye API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
            return []
    
    async def get_token_security(self, token_address: str) -> Dict:
        """Get token security info"""
        await self._rate_limit_check()
        
        url = f"{self.base_url}/defi/v3/token/security"
        params = {"address": token_address}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    self.request_count += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    return {}
        except Exception as e:
            logger.error(f"Error fetching token security: {e}")
            return {}

# Update function to replace BirdeyeAPI in your code
def update_birdeye_api():
    """Replace BirdeyeAPI with fixed version"""
    
    print("To fix Birdeye integration:")
    print("1. Replace BirdeyeAPI class in core/data/market_data.py with BirdeyeAPIv3")
    print("2. Update TokenScanner to use the new get_trending_tokens method")
    print("3. Add rate limiting to respect Starter package limits")
    
    # Example TokenScanner update:
    example = '''
    # In token_scanner.py
    if self.birdeye_api:
        tokens = await self.birdeye_api.get_trending_tokens(limit=20)
        return tokens
    '''
    print(f"\nExample update:\n{example}")

if __name__ == "__main__":
    update_birdeye_api()
