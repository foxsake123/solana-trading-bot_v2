# utils/field_mapper.py
def map_token_fields(token_data, source="birdeye"):
    """Map token fields from APIs to database schema"""
    return {
        "contract_address": token_data.get("address") or token_data.get("contract_address", ""),
        "symbol": token_data.get("symbol", "UNKNOWN"),
        "name": token_data.get("name", "Unknown"),
        "price": float(token_data.get("price", 0) or 0),
        "volume_24h": float(token_data.get("v24hUSD", 0) or 0),
        "liquidity": float(token_data.get("liquidity", 0) or 0),
        "market_cap": float(token_data.get("mc", 0) or 0),
        "price_change_24h": float(token_data.get("v24hChangePercent", 0) or 0),
        "holders": int(token_data.get("holder", 0) or 0),
        "source": source
    }