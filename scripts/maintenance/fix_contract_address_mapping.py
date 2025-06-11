# fix_contract_address_mapping.py
"""
Fix for contract_address field mapping issue in Birdeye API integration
"""
import json
import os

def fix_market_data_file():
    """Update market_data.py to ensure proper field mapping"""
    
    # Path to market_data.py
    market_data_path = "core/data/market_data.py"
    
    print("Fixing contract_address mapping in market_data.py...")
    
    # Read the file
    with open(market_data_path, 'r') as f:
        content = f.read()
    
    # Backup the original
    with open(market_data_path + '.backup', 'w') as f:
        f.write(content)
    
    # Key fix: In the get_token_list method, ensure proper mapping
    # Find the line that returns tokens and add mapping
    fix_needed = False
    
    # Check if the get_token_list method properly maps fields
    if 'return tokens' in content and 'get_token_list' in content:
        # Replace the simple return with proper mapping
        old_return = 'return tokens'
        new_return = '''# Ensure proper field mapping
            mapped_tokens = []
            for token in tokens:
                mapped_token = {
                    "address": token.get("address", ""),
                    "contract_address": token.get("address", ""),  # Map for database
                    "symbol": token.get("symbol", ""),
                    "name": token.get("name", ""),
                    "price": float(token.get("price", 0) or 0),
                    "v24hChangePercent": float(token.get("v24hChangePercent", 0) or 0),
                    "v24hUSD": float(token.get("v24hUSD", 0) or 0),
                    "liquidity": float(token.get("liquidity", 0) or 0),
                    "mc": float(token.get("mc", 0) or 0),
                    "holder": int(token.get("holder", 0) or 0)
                }
                mapped_tokens.append(mapped_token)
            return mapped_tokens'''
        
        if old_return in content:
            content = content.replace(old_return, new_return, 1)
            fix_needed = True
    
    # Write the fixed content
    if fix_needed:
        with open(market_data_path, 'w') as f:
            f.write(content)
        print("✓ Fixed market_data.py")
    else:
        print("✓ market_data.py already has proper mapping")

def verify_database_schema():
    """Check if database expects contract_address field"""
    models_path = "data/models"
    
    if os.path.exists(models_path):
        print("\nChecking database models...")
        for file in os.listdir(models_path):
            if file.endswith('.py'):
                file_path = os.path.join(models_path, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'contract_address' in content:
                        print(f"✓ Found contract_address field in {file}")
                    elif 'address' in content and 'token' in content.lower():
                        print(f"⚠ {file} might need updating - uses 'address' instead of 'contract_address'")

def create_field_mapper():
    """Create a utility function to ensure consistent field mapping"""
    mapper_code = '''# utils/field_mapper.py
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
'''
    
    # Create utils directory if it doesn't exist
    os.makedirs("utils", exist_ok=True)
    
    # Write the mapper file
    with open("utils/field_mapper.py", 'w') as f:
        f.write(mapper_code)
    
    print("\n✓ Created utils/field_mapper.py")

def main():
    print("=== Fixing Contract Address Field Mapping ===\n")
    
    # Fix the main issue in market_data.py
    fix_market_data_file()
    
    # Check database schema
    verify_database_schema()
    
    # Create field mapper utility
    create_field_mapper()
    
    print("\n=== Fix Complete ===")
    print("\nNext steps:")
    print("1. Import field_mapper in your market_data.py:")
    print("   from utils.field_mapper import map_token_fields")
    print("2. Use it when processing tokens:")
    print("   mapped_token = map_token_fields(raw_token, source='birdeye')")
    print("3. Restart your bot to apply changes")

if __name__ == "__main__":
    main()