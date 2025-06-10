# utils/field_mapper.py
"""
Utility to ensure consistent field mapping between APIs and database
"""

def map_token_fields(token_data, source="birdeye"):
    """
    Map token fields from various sources to database schema
    
    :param token_data: Raw token data from API
    :param source: Data source (birdeye, dexscreener, etc.)
    :return: Mapped token data
    """
    # Common mapping for all sources
    mapped = {
        "contract_address": token_data.get("address") or token_data.get("contract_address", ""),
        "symbol": token_data.get("symbol", "UNKNOWN"),
        "name": token_data.get("name", token_data.get("symbol", "Unknown")),
        "decimals": int(token_data.get("decimals", 9)),
        "price": float(token_data.get("price", 0) or token_data.get("value", 0) or 0),
        "price_usd": float(token_data.get("price", 0) or token_data.get("value", 0) or 0),
        "volume_24h": float(token_data.get("v24hUSD", 0) or token_data.get("volume24h", 0) or 0),
        "liquidity": float(token_data.get("liquidity", 0) or token_data.get("liquidityUSD", 0) or 0),
        "liquidity_usd": float(token_data.get("liquidity", 0) or token_data.get("liquidityUSD", 0) or 0),
        "market_cap": float(token_data.get("mc", 0) or token_data.get("marketCap", 0) or 0),
        "price_change_24h": float(token_data.get("v24hChangePercent", 0) or token_data.get("priceChange24h", 0) or 0),
        "holders": int(token_data.get("holder", 0) or token_data.get("holders", 0) or 0),
        "source": source
    }
    
    # Source-specific mappings
    if source == "dexscreener":
        mapped["price_change_24h"] = float(token_data.get("priceChange", {}).get("h24", 0) or 0)
        mapped["volume_24h"] = float(token_data.get("volume", {}).get("h24", 0) or 0)
        mapped["liquidity_usd"] = float(token_data.get("liquidity", {}).get("usd", 0) or 0)
    
    return mapped

def ensure_required_fields(token_data):
    """Ensure all required fields are present"""
    required_fields = {
        "contract_address": "",
        "symbol": "UNKNOWN",
        "name": "Unknown Token",
        "price": 0.0,
        "price_usd": 0.0,
        "volume_24h": 0.0,
        "liquidity_usd": 0.0,
        "market_cap": 0.0,
        "price_change_24h": 0.0,
        "holders": 0,
        "decimals": 9
    }
    
    for field, default in required_fields.items():
        if field not in token_data:
            token_data[field] = default
            
    return token_data
