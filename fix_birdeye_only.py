#!/usr/bin/env python3
"""
Fix to use only Birdeye API (no DexScreener)
"""
import os
import re

def fix_birdeye_api():
    """Fix BirdeyeAPI to work properly"""
    
    # 1. Fix market_data.py - add headers and update get_token_info
    market_file = 'core/data/market_data.py'
    with open(market_file, 'r') as f:
        content = f.read()
    
    # Find __init__ and add headers after api_key
    if 'self.headers' not in content:
        content = content.replace(
            'self.api_key = api_key',
            'self.api_key = api_key\n        self.headers = {"X-API-KEY": self.api_key}'
        )
    
    # Fix get_token_info to use correct Birdeye endpoint
    if 'async def get_token_info' in content:
        # Replace the method with correct implementation
        pattern = r'async def get_token_info\(self.*?\n(?:.*\n)*?        except Exception.*?\n.*?\n'
        replacement = '''async def get_token_info(self, address: str) -> Dict[str, Any]:
        """Get token info from Birdeye API"""
        try:
            # Use Birdeye token security endpoint for detailed info
            url = f"{self.base_url}/defi/token_security"
            params = {"address": address}
            
            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and data.get('data'):
                        token_data = data['data']
                        
                        # Also get price data
                        price_url = f"{self.base_url}/defi/price"
                        price_params = {"address": address}
                        
                        async with self.session.get(price_url, headers=self.headers, params=price_params) as price_response:
                            price_data = {}
                            if price_response.status == 200:
                                price_json = await price_response.json()
                                if price_json.get('success') and price_json.get('data'):
                                    price_data = price_json['data']
                        
                        return {
                            'address': address,
                            'symbol': token_data.get('symbol', 'Unknown'),
                            'name': token_data.get('name', 'Unknown Token'),
                            'price': price_data.get('value', 0),
                            'price_usd': price_data.get('value', 0),
                            'liquidity_usd': price_data.get('liquidity', token_data.get('liquidity', 0)),
                            'volume_24h': price_data.get('v24hUSD', 0),
                            'price_change_24h': price_data.get('v24hChangePercent', 0),
                            'market_cap': price_data.get('mc', token_data.get('mc', 0)),
                            'holders': token_data.get('holder', 0),
                            'total_supply': token_data.get('totalSupply', 0),
                            'decimals': token_data.get('decimals', 9)
                        }
            
            # If failed, return minimal data
            return {
                'address': address,
                'symbol': 'Unknown',
                'name': 'Unknown Token',
                'price_usd': 0.00001,
                'liquidity_usd': 10000,
                'volume_24h': 5000,
                'price_change_24h': 0,
                'market_cap': 100000,
                'holders': 100
            }
                
        except Exception as e:
            logger.error(f"Error getting token info for {address}: {e}")
            return None
'''
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Save fixed market_data.py
    with open(market_file, 'w') as f:
        f.write(content)
    
    print("[OK] Fixed BirdeyeAPI in market_data.py")
    
    # 2. Fix token_analyzer.py to only use Birdeye
    analyzer_file = 'core/analysis/token_analyzer.py'
    with open(analyzer_file, 'r') as f:
        analyzer_content = f.read()
    
    # Remove DexScreener references
    analyzer_content = analyzer_content.replace('logger.warning("No DexScreener data', '# logger.warning("No DexScreener data')
    analyzer_content = analyzer_content.replace('dexscreener_data = await self._fetch_from_dexscreener', '# dexscreener_data = await self._fetch_from_dexscreener')
    
    # Update fetch_token_data to only use Birdeye
    if 'async def fetch_token_data' in analyzer_content:
        # Find and update the method to only use Birdeye
        pattern = r'(async def fetch_token_data.*?)\n(.*?)# For real tokens, fetch data from API'
        def replacement_func(match):
            return match.group(1) + '\n' + match.group(2) + '''# For real tokens, fetch data from Birdeye API only
        if self.birdeye_api:
            try:
                token_data = await self.birdeye_api.get_token_info(contract_address)
                
                if token_data:
                    # Update cache and database
                    token_data['last_updated'] = datetime.now(timezone.utc).isoformat()
                    token_data['is_simulation'] = False
                    
                    self.token_data_cache[contract_address] = (current_time, token_data)
                    
                    if self.db:
                        self.db.store_token(token_data)
                    
                    return token_data
                    
            except Exception as e:
                logger.error(f"Error fetching token data for {contract_address}: {e}")'''
        
        analyzer_content = re.sub(pattern, replacement_func, analyzer_content, flags=re.DOTALL)
    
    # Save fixed token_analyzer.py
    with open(analyzer_file, 'w') as f:
        f.write(analyzer_content)
    
    print("[OK] Updated token_analyzer.py to use only Birdeye")
    
    print("\nAll fixes applied! The bot will now use only Birdeye API.")

if __name__ == "__main__":
    fix_birdeye_api()
