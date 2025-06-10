#!/usr/bin/env python3
"""
Fix BirdeyeAPI headers attribute
"""
import os
import re

def fix_birdeye_headers():
    """Add headers attribute to BirdeyeAPI __init__"""
    
    market_file = 'core/data/market_data.py'
    with open(market_file, 'r') as f:
        content = f.read()
    
    # Find the __init__ method of BirdeyeAPI
    init_pattern = r'(class BirdeyeAPI.*?def __init__\(self.*?\):.*?)(self\.session = aiohttp\.ClientSession\(\))'
    
    match = re.search(init_pattern, content, re.DOTALL)
    if match:
        # Add headers before session creation
        replacement = match.group(1) + 'self.headers = {"X-API-KEY": self.api_key}\n        ' + match.group(2)
        content = content[:match.start()] + replacement + content[match.end():]
        
        with open(market_file, 'w') as f:
            f.write(content)
        
        print("[OK] Fixed headers attribute in BirdeyeAPI")
    else:
        # Alternative approach - add after self.api_key
        if 'self.api_key = api_key' in content and 'self.headers' not in content:
            content = content.replace(
                'self.api_key = api_key',
                'self.api_key = api_key\n        self.headers = {"X-API-KEY": self.api_key}'
            )
            with open(market_file, 'w') as f:
                f.write(content)
            print("[OK] Added headers attribute to BirdeyeAPI")

if __name__ == "__main__":
    fix_birdeye_headers()
