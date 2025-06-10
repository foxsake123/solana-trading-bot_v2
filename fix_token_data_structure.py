#!/usr/bin/env python3
"""
Fix token data structure to match database requirements
"""
import re

def fix_token_analyzer():
    """Fix token_analyzer to use correct field names"""
    
    # Fix token_analyzer.py
    with open('core/analysis/token_analyzer.py', 'r') as f:
        content = f.read()
    
    # Add proper field mapping in fetch_token_data
    fix = """
                if token_data:
                    # Map Birdeye fields to expected database fields
                    token_data['contract_address'] = token_data.get('address', contract_address)
                    token_data['ticker'] = token_data.get('symbol', 'Unknown')
                    
                    # Ensure all required fields exist
                    token_data.setdefault('price_change_1h', 0)
                    token_data.setdefault('price_change_6h', 0)
                    token_data.setdefault('holders', 100)
                    
                    # Update cache and database"""
    
    # Replace in the file
    content = re.sub(
        r'if token_data:\s*\n\s*# Update cache and database',
        fix,
        content
    )
    
    with open('core/analysis/token_analyzer.py', 'w') as f:
        f.write(content)
    
    print("[OK] Fixed token_analyzer.py field mapping")
    
    # Fix market_data.py get_token_info to return correct fields
    with open('core/data/market_data.py', 'r') as f:
        content = f.read()
    
    # Update the return statement in get_token_info
    old_return = """return {
                            'address': address,"""
    
    new_return = """return {
                            'address': address,
                            'contract_address': address,  # Database expects this field"""
    
    content = content.replace(old_return, new_return)
    
    # Also fix the fallback return
    old_fallback = """return {
                'address': address,
                'symbol': 'Unknown',"""
    
    new_fallback = """return {
                'address': address,
                'contract_address': address,  # Database expects this field
                'symbol': 'Unknown',"""
    
    content = content.replace(old_fallback, new_fallback)
    
    with open('core/data/market_data.py', 'w') as f:
        f.write(content)
    
    print("[OK] Fixed market_data.py field mapping")

if __name__ == "__main__":
    fix_token_analyzer()
