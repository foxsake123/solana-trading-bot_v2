# birdeye_correct_implementation.py
"""
Corrected Birdeye API implementation based on actual API responses
"""
import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BirdeyeAPI:
    """
    Corrected Birdeye API implementation for the Starter package
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so"
        self.session = None
        self.is_available = bool(self.api_key)
        
        # Rate limiting for Starter package
        self.rate_limit = 100
        self.request_times = []
        self.min_interval = 0.6
        
        # Cache
        self.cache = {}
        self.cache_ttl = 300
        
        if not self.is_available:
            logger.warning("BirdeyeAPI key not found")
        else:
            logger.info("BirdeyeAPI initialized")
    
    async def __aenter__(self):
        if self.is_available and not self.session:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def _rate_limit_check(self):
        current_time = time.time()
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        if len(self.request_times) >= self.rate_limit:
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        if self.request_times:
            time_since_last = current_time - self.request_times[-1]
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
                
        self.request_times.append(current_time)
        
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        if not self.is_available:
            return None
            
        await self._rate_limit_check()
        
        # Check cache
        cache_key = f"{endpoint}:{json.dumps(params or {})}"
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
                
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            await self._ensure_session()
            
            async with self.session.get(url, headers=headers, params=params, timeout=30) as response:
                text = await response.text()
                
                if response.status == 200:
                    data = json.loads(text)
                    self.cache[cache_key] = (data, time.time())
                    return data
                else:
                    logger.error(f"API error {response.status}: {text}")
                    
        except Exception as e:
            logger.error(f"Request failed: {e}")
            
        return None
        
    async def get_token_list(self, offset: int = 0, limit: int = 50, 
                           sort_by: str = "v24hChangePercent", 
                           sort_type: str = "desc") -> List[Dict]:
        """
        Get list of tokens sorted by various criteria
        
        :param offset: Starting position
        :param limit: Number of results (max 50 for Starter)
        :param sort_by: v24hChangePercent, v24hUSD, liquidity, mc
        :param sort_type: asc or desc
        :return: List of tokens
        """
        endpoint = "/defi/tokenlist"
        params = {
            "sort_by": sort_by,
            "sort_type": sort_type,
            "offset": offset,
            "limit": min(limit, 50)
        }
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            tokens = response["data"].get("tokens", [])
            logger.info(f"Found {len(tokens)} tokens")
            return tokens
        return []
        
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens based on 24h change"""
        tokens = await self.get_token_list(
            limit=limit,
            sort_by="v24hChangePercent",
            sort_type="desc"
        )
        return self._format_tokens(tokens)
        
    async def get_top_volume(self, limit: int = 20) -> List[Dict]:
        """Get tokens with highest volume"""
        tokens = await self.get_token_list(
            limit=limit,
            sort_by="v24hUSD",
            sort_type="desc"
        )
        return self._format_tokens(tokens)
        
    async def get_token_price(self, address: str) -> Optional[Dict]:
        """Get token price information"""
        endpoint = "/defi/price"
        params = {"address": address}
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            return response["data"]
        return None
        
    async def get_token_overview(self, address: str) -> Optional[Dict]:
        """Get token overview"""
        endpoint = "/defi/token_overview"
        params = {"address": address}
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            return response["data"]
        return None
        
    def _format_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Format tokens for bot compatibility"""
        formatted = []
        for token in tokens:
            try:
                # Calculate price from volume and amount if needed
                price = 0
                if token.get("v24hUSD") and token.get("v24hVolume"):
                    # This is an approximation
                    price = float(token.get("lastTradeUnixTime", 0)) / 1e9 if token.get("lastTradeUnixTime") else 0
                
                # Get actual price if available
                if token.get("price"):
                    price = float(token["price"])
                
                formatted_token = {
                    "contract_address": token.get("address", ""),
                    "symbol": token.get("symbol", "UNKNOWN"),
                    "name": token.get("name", token.get("symbol", "Unknown")),
                    "price": price,
                    "price_change_24h": float(token.get("v24hChangePercent", 0)),
                    "volume_24h": float(token.get("v24hUSD", 0)),
                    "liquidity": float(token.get("liquidity", 0)),
                    "market_cap": float(token.get("mc", 0)),
                    "holders": int(token.get("holder", 0)),
                    "source": "birdeye"
                }
                
                # Skip invalid tokens
                if not formatted_token["contract_address"]:
                    continue
                    
                formatted.append(formatted_token)
            except Exception as e:
                logger.error(f"Error formatting token: {e}")
                continue
                
        return formatted
        
    async def discover_tokens(self, strategies: List[str] = None, max_tokens: int = 30) -> List[Dict]:
        """Discover tokens using multiple strategies"""
        if not self.is_available:
            return []
            
        if strategies is None:
            strategies = ["trending", "volume"]
            
        discovered = {}
        tokens_per_strategy = max(10, max_tokens // len(strategies))
        
        for strategy in strategies:
            try:
                if strategy == "trending":
                    tokens = await self.get_trending_tokens(limit=tokens_per_strategy)
                elif strategy == "volume":
                    tokens = await self.get_top_volume(limit=tokens_per_strategy)
                else:
                    continue
                    
                for token in tokens:
                    if token.get("contract_address"):
                        discovered[token["contract_address"]] = token
                        
            except Exception as e:
                logger.error(f"Error in {strategy}: {e}")
                
        result = list(discovered.values())[:max_tokens]
        
        # Get prices for tokens if missing
        for token in result:
            if token["price"] == 0 and token.get("contract_address"):
                price_data = await self.get_token_price(token["contract_address"])
                if price_data:
                    token["price"] = float(price_data.get("value", 0))
                    
        logger.info(f"Discovered {len(result)} unique tokens")
        return result


# Test the corrected implementation
async def test_corrected_api():
    """Test the corrected Birdeye API"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('BIRDEYE_API_KEY')
    if not api_key:
        print("Please set BIRDEYE_API_KEY in .env file")
        return
        
    print("Testing corrected Birdeye API...")
    
    async with BirdeyeAPI(api_key) as api:
        # Test token list
        print("\n1. Testing token list...")
        tokens = await api.get_token_list(limit=5)
        if tokens:
            print(f"Found {len(tokens)} tokens")
            for token in tokens[:3]:
                print(f"  - {token.get('symbol')}: Vol ${token.get('v24hUSD', 0):,.0f}")
        
        # Test trending
        print("\n2. Testing trending tokens...")
        trending = await api.get_trending_tokens(limit=5)
        if trending:
            print(f"Found {len(trending)} trending tokens")
            for token in trending[:3]:
                print(f"  - {token['symbol']}: {token['price_change_24h']:+.2f}%")
                
        # Test discovery
        print("\n3. Testing token discovery...")
        discovered = await api.discover_tokens(max_tokens=10)
        if discovered:
            print(f"Discovered {len(discovered)} tokens")
            
        # Test token details
        if discovered:
            token = discovered[0]
            print(f"\n4. Testing token details for {token['symbol']}...")
            details = await api.get_token_overview(token['contract_address'])
            if details:
                print(f"  Liquidity: ${details.get('liquidity', 0):,.2f}")
                print(f"  Holders: {details.get('holder', 0):,}")


if __name__ == "__main__":
    asyncio.run(test_corrected_api())