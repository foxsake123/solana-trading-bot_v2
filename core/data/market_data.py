# core/data/market_data.py
"""
Market data module with fully corrected Birdeye API integration
"""
import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from config.bot_config import BotConfiguration

logger = logging.getLogger(__name__)

class BirdeyeAPI:
    """
    Fixed Birdeye API implementation for token discovery and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY', '')
        self.base_url = "https://public-api.birdeye.so"
        self.session = None
        self.is_available = bool(self.api_key)
        
        # Rate limiting for Starter package (100 req/min)
        self.rate_limit = 100
        self.request_times = []
        self.min_interval = 0.6  # 600ms between requests
        
        # Cache configuration
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        if not self.is_available:
            logger.warning("BirdeyeAPI key not found. Limited functionality available.")
        else:
            logger.info("BirdeyeAPI initialized successfully")
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.is_available and not self.session:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def _rate_limit_check(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Clean old requests
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check rate limit
        if len(self.request_times) >= self.rate_limit:
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Minimum interval between requests
        if self.request_times:
            time_since_last = current_time - self.request_times[-1]
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
                
        self.request_times.append(current_time)
        
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with error handling"""
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
                if response.status == 200:
                    data = await response.json()
                    self.cache[cache_key] = (data, time.time())
                    return data
                elif response.status == 429:
                    logger.error("Rate limit exceeded")
                    await asyncio.sleep(60)
                elif response.status == 401:
                    logger.error("Invalid API key")
                    self.is_available = False
                else:
                    text = await response.text()
                    logger.error(f"API error {response.status}: {text}")
                    
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {endpoint}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            
        return None
        
    async def get_token_list(self, offset: int = 0, limit: int = 50, 
                           sort_by: str = "v24hChangePercent", 
                           sort_type: str = "desc") -> List[Dict]:
        """
        Get list of tokens sorted by various criteria
        """
        endpoint = "/defi/tokenlist"
        params = {
            "sort_by": sort_by,
            "sort_type": sort_type,
            "offset": offset,
            "limit": min(limit, 50)  # Starter limit
        }
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            tokens = response["data"].get("tokens", [])
            logger.info(f"Found {len(tokens)} tokens from Birdeye")
            return tokens
        return []
        
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens based on 24h change"""
        if not self.is_available:
            logger.warning("BirdeyeAPI not available, using empty list")
            return []
            
        # Get by volume first (more reliable than extreme percentage changes)
        tokens = await self.get_token_list(
            limit=limit,
            sort_by="v24hUSD",
            sort_type="desc"
        )
        return self._format_tokens(tokens)
        
    async def get_top_gainers(self, limit: int = 20) -> List[Dict]:
        """Get top gaining tokens"""
        if not self.is_available:
            return []
            
        tokens = await self.get_token_list(
            limit=limit,
            sort_by="v24hChangePercent",
            sort_type="desc"
        )
        # Filter out tokens with unrealistic gains
        filtered_tokens = [t for t in tokens if self._is_realistic_gain(t)]
        return self._format_tokens(filtered_tokens)
        
    async def get_new_listings(self, limit: int = 20) -> List[Dict]:
        """Get newly listed tokens by volume"""
        if not self.is_available:
            return []
            
        tokens = await self.get_token_list(
            limit=limit,
            sort_by="v24hUSD",
            sort_type="desc"
        )
        return self._format_tokens(tokens)
        
    def _is_realistic_gain(self, token: Dict) -> bool:
        """Filter out tokens with unrealistic percentage gains"""
        change = token.get("v24hChangePercent", 0)
        # Filter out tokens with gains over 10,000% (100x) as they're likely errors
        return -99 <= change <= 10000
        
    def _format_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Format tokens for compatibility with bot"""
        formatted = []
        for token in tokens:
            try:
                # Get price - need to fetch separately if not available
                price = 0
                if token.get("price"):
                    price = float(token["price"])
                elif token.get("lastTrade"):
                    price = float(token["lastTrade"])
                
                # Ensure we have valid numeric values
                volume = float(token.get("v24hUSD", 0) or 0)
                liquidity = float(token.get("liquidity", 0) or 0)
                market_cap = float(token.get("mc", 0) or 0)
                change_24h = float(token.get("v24hChangePercent", 0) or 0)
                
                # Sanity check on percentage change
                if change_24h > 10000:  # Over 100x gain
                    change_24h = 0  # Reset to 0 as it's likely bad data
                
                formatted_token = {
                    "contract_address": token.get("address", ""),
                    "symbol": token.get("symbol", "UNKNOWN"),
                    "name": token.get("name", token.get("symbol", "Unknown")),
                    "price": price,
                    "price_change_24h": change_24h,
                    "volume_24h": volume,
                    "liquidity": liquidity,
                    "market_cap": market_cap,
                    "holders": int(token.get("holder", 0) or 0),
                    "source": "birdeye"
                }
                
                # Skip tokens with no address or very low volume
                if not formatted_token["contract_address"] or volume < 100:
                    continue
                    
                formatted.append(formatted_token)
            except Exception as e:
                logger.debug(f"Error formatting token {token.get('symbol', 'unknown')}: {e}")
                continue
                
        return formatted
        
    async def get_token_price(self, address: str) -> Optional[Dict]:
        """Get token price information"""
        if not self.is_available:
            return None
            
        endpoint = "/defi/price"
        params = {"address": address}
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            return response["data"]
        return None
        
    async def get_token_overview(self, address: str) -> Optional[Dict]:
        """Get detailed token information"""
        if not self.is_available:
            return None
            
        endpoint = "/defi/token_overview"
        params = {"address": address}
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            return response["data"]
        return None
        
    async def get_token_security(self, address: str) -> Optional[Dict]:
        """Get token security information"""
        if not self.is_available:
            return None
            
        endpoint = "/defi/token_security"
        params = {"address": address}
        
        response = await self._make_request(endpoint, params)
        if response and "data" in response:
            return response["data"]
        return None
        
    async def discover_tokens(self, strategies: List[str] = None, max_tokens: int = 30) -> List[Dict]:
        """Discover tokens using multiple strategies"""
        if not self.is_available:
            logger.warning("BirdeyeAPI not available for token discovery")
            return []
            
        if strategies is None:
            strategies = ["volume", "gainers"]  # Volume first as it's more reliable
            
        discovered = {}
        tokens_per_strategy = max(10, max_tokens // len(strategies))
        
        for strategy in strategies:
            try:
                if strategy == "volume":
                    tokens = await self.get_trending_tokens(limit=tokens_per_strategy)
                elif strategy == "gainers":
                    tokens = await self.get_top_gainers(limit=tokens_per_strategy)
                elif strategy == "new":
                    tokens = await self.get_new_listings(limit=tokens_per_strategy)
                else:
                    continue
                    
                # Deduplicate by address
                for token in tokens:
                    if token.get("contract_address") and token["volume_24h"] > 100:
                        discovered[token["contract_address"]] = token
                        
            except Exception as e:
                logger.error(f"Error in {strategy} discovery: {e}")
                
        result = list(discovered.values())[:max_tokens]
        
        # Get prices for tokens if missing
        for token in result:
            if token["price"] == 0 and token.get("contract_address"):
                try:
                    price_data = await self.get_token_price(token["contract_address"])
                    if price_data and price_data.get("value"):
                        token["price"] = float(price_data["value"])
                except Exception as e:
                    logger.debug(f"Failed to get price for {token['symbol']}: {e}")
                    
        logger.info(f"Discovered {len(result)} unique tokens via Birdeye")
        return result

# Fallback token discovery using DexScreener
class DexScreenerAPI:
    """Fallback API for token discovery when Birdeye is unavailable"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.session = None
        
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens from DexScreener"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/search?q=trending"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    tokens = []
                    seen_addresses = set()
                    
                    for pair in pairs:
                        if pair.get("chainId") != "solana":
                            continue
                            
                        base_token = pair.get("baseToken", {})
                        address = base_token.get("address", "")
                        
                        if not address or address in seen_addresses:
                            continue
                            
                        seen_addresses.add(address)
                        
                        tokens.append({
                            "contract_address": address,
                            "symbol": base_token.get("symbol", ""),
                            "name": base_token.get("name", ""),
                            "price": float(pair.get("priceUsd", 0) or 0),
                            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                            "market_cap": float(pair.get("fdv", 0) or 0),
                            "source": "dexscreener"
                        })
                        
                        if len(tokens) >= limit:
                            break
                            
                    logger.info(f"Found {len(tokens)} tokens from DexScreener")
                    return tokens
                    
        except Exception as e:
            logger.error(f"DexScreener API error: {e}")
            
        return []


# Main market data aggregator
class MarketDataAggregator:
    """Aggregates data from multiple sources"""
    
    def __init__(self, birdeye_api_key: Optional[str] = None):
        self.birdeye = BirdeyeAPI(birdeye_api_key)
        self.dexscreener = DexScreenerAPI()
        
    async def discover_tokens(self, max_tokens: int = 50) -> List[Dict]:
        """Discover tokens from all available sources"""
        all_tokens = {}
        
        # Try Birdeye first
        async with self.birdeye:
            birdeye_tokens = await self.birdeye.discover_tokens(max_tokens=max_tokens)
            for token in birdeye_tokens:
                if token.get("contract_address"):
                    all_tokens[token["contract_address"]] = token
                    
        # If Birdeye didn't return enough, use DexScreener
        if len(all_tokens) < max_tokens // 2:
            async with self.dexscreener:
                dex_tokens = await self.dexscreener.get_trending_tokens(limit=max_tokens)
                for token in dex_tokens:
                    if token.get("contract_address") and token["contract_address"] not in all_tokens:
                        all_tokens[token["contract_address"]] = token
                        
        result = list(all_tokens.values())[:max_tokens]
        
        # Sort by volume
        result.sort(key=lambda x: x.get("volume_24h", 0), reverse=True)
        
        logger.info(f"Aggregated {len(result)} tokens from all sources")
        return result
    # ADD THESE CLASSES TO THE END OF YOUR market_data.py FILE

# Fallback token discovery using DexScreener
class DexScreenerAPI:
    """Fallback API for token discovery when Birdeye is unavailable"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.session = None
        
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """Get trending tokens from DexScreener"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            url = f"{self.base_url}/search?q=trending"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    
                    tokens = []
                    seen_addresses = set()
                    
                    for pair in pairs:
                        if pair.get("chainId") != "solana":
                            continue
                            
                        base_token = pair.get("baseToken", {})
                        address = base_token.get("address", "")
                        
                        if not address or address in seen_addresses:
                            continue
                            
                        seen_addresses.add(address)
                        
                        tokens.append({
                            "contract_address": address,
                            "symbol": base_token.get("symbol", ""),
                            "name": base_token.get("name", ""),
                            "price": float(pair.get("priceUsd", 0) or 0),
                            "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
                            "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                            "market_cap": float(pair.get("fdv", 0) or 0),
                            "source": "dexscreener"
                        })
                        
                        if len(tokens) >= limit:
                            break
                            
                    logger.info(f"Found {len(tokens)} tokens from DexScreener")
                    return tokens
                    
        except Exception as e:
            logger.error(f"DexScreener API error: {e}")
            
        return []


# Main market data aggregator
class MarketDataAggregator:
    """Aggregates data from multiple sources"""
    
    def __init__(self, birdeye_api_key: Optional[str] = None):
        self.birdeye = BirdeyeAPI(birdeye_api_key)
        self.dexscreener = DexScreenerAPI()
        
    async def discover_tokens(self, max_tokens: int = 50) -> List[Dict]:
        """Discover tokens from all available sources"""
        all_tokens = {}
        
        # Try Birdeye first
        async with self.birdeye:
            birdeye_tokens = await self.birdeye.discover_tokens(max_tokens=max_tokens)
            for token in birdeye_tokens:
                if token.get("contract_address"):
                    all_tokens[token["contract_address"]] = token
                    
        # If Birdeye didn't return enough, use DexScreener
        if len(all_tokens) < max_tokens // 2:
            async with self.dexscreener:
                dex_tokens = await self.dexscreener.get_trending_tokens(limit=max_tokens)
                for token in dex_tokens:
                    if token.get("contract_address") and token["contract_address"] not in all_tokens:
                        all_tokens[token["contract_address"]] = token
                        
        result = list(all_tokens.values())[:max_tokens]
        
        # Sort by volume
        result.sort(key=lambda x: x.get("volume_24h", 0), reverse=True)
        
        logger.info(f"Aggregated {len(result)} tokens from all sources")
        return result