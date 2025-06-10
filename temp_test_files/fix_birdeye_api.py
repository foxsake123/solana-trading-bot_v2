# fix_birdeye_api.py
"""
Quick fix script to resolve Birdeye API issues in your trading bot
Run this to immediately fix the "BirdeyeAPI not available" error
"""
import os
import sys
import json
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backed up {filepath} to {backup_path}")
        return True
    return False

def fix_birdeye_initialization():
    """Fix the Birdeye API initialization in token_scanner.py"""
    token_scanner_path = "core/data/token_scanner.py"
    
    if not os.path.exists(token_scanner_path):
        print(f"❌ {token_scanner_path} not found!")
        return False
        
    # Read the file with UTF-8 encoding
    with open(token_scanner_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Fix 1: Ensure BirdeyeAPI is properly imported and initialized
    if "from core.data.market_data import BirdeyeAPI" not in content:
        # Add import at the top
        lines = content.split('\n')
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                import_index = i + 1
                
        lines.insert(import_index, "from core.data.market_data import BirdeyeAPI, MarketDataAggregator")
        content = '\n'.join(lines)
        
    # Fix 2: Update scan_for_tokens method
    updated_scan_method = '''
    async def scan_for_tokens(self):
        """Scan for potential tokens using Birdeye v3 API and fallbacks"""
        logger.info("Scanning for tokens...")
        
        try:
            # Use MarketDataAggregator for better reliability
            from core.data.market_data import MarketDataAggregator
            
            aggregator = MarketDataAggregator(self.birdeye_api_key)
            discovered_tokens = await aggregator.discover_tokens(max_tokens=50)
            
            if not discovered_tokens:
                logger.warning("No tokens found from primary sources")
                return []
                
            logger.info(f"Found {len(discovered_tokens)} tokens to analyze")
            
            # Analyze tokens
            analyzed_tokens = []
            for token in discovered_tokens:
                try:
                    # Skip if we've seen this recently
                    if token.get('contract_address') in self.analyzed_tokens:
                        continue
                        
                    # Basic filtering
                    if not self._should_analyze_token(token):
                        continue
                        
                    # Analyze with token_analyzer
                    analysis = await self.token_analyzer.analyze(token)
                    
                    if analysis.get('score', 0) >= self.config.get('min_token_score', 0.7):
                        token_with_analysis = {**token, **analysis}
                        analyzed_tokens.append(token_with_analysis)
                        self.analyzed_tokens.add(token['contract_address'])
                        
                except Exception as e:
                    logger.error(f"Error analyzing token {token.get('symbol')}: {e}")
                    continue
                    
            logger.info(f"Analyzed {len(analyzed_tokens)} tokens successfully")
            return analyzed_tokens
            
        except Exception as e:
            logger.error(f"Token scanning error: {e}")
            return []
'''

    # Replace the scan_for_tokens method
    import re
    pattern = r'async def scan_for_tokens\(self\):[^}]+?(?=\n    async def|\n    def|\nclass|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, updated_scan_method.strip(), content, flags=re.DOTALL)
    else:
        # If method not found, add it
        content += f"\n{updated_scan_method}"
        
    # Write back with UTF-8 encoding
    with open(token_scanner_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ Fixed {token_scanner_path}")
    return True

def update_enhanced_bot():
    """Update enhanced_trading_bot.py to properly initialize Birdeye"""
    bot_path = "enhanced_trading_bot.py"
    
    if not os.path.exists(bot_path):
        print(f"⚠️ {bot_path} not found, skipping...")
        return True
        
    backup_file(bot_path)
    
    with open(bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Add proper initialization in __init__
    init_fix = '''
        # Initialize Birdeye API properly
        if hasattr(scanner, 'birdeye_api') and not scanner.birdeye_api:
            from core.data.market_data import BirdeyeAPI
            scanner.birdeye_api = BirdeyeAPI(config.get('BIRDEYE_API_KEY'))
            logger.info(f"Birdeye API initialized: {scanner.birdeye_api.is_available}")
'''
    
    # Find __init__ method and add the fix
    import re
    pattern = r'(def __init__.*?:\n(?:.*?\n)*?)(.*?super\(\).__init__.*?\n)'
    
    def replacer(match):
        return match.group(1) + match.group(2) + init_fix
        
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    with open(bot_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ Updated {bot_path}")
    return True

def check_env_file():
    """Check and update .env file"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print("❌ .env file not found! Creating template...")
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("""# Birdeye API Configuration
BIRDEYE_API_KEY=your_api_key_here

# Other API Keys
HELIUS_API_KEY=
QUICKNODE_RPC_URL=

# Twitter API (optional)
TWITTER_BEARER_TOKEN=
""")
        print("✅ Created .env template. Please add your BIRDEYE_API_KEY!")
        return False
        
    # Check if BIRDEYE_API_KEY exists
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'BIRDEYE_API_KEY' not in content:
        with open(env_path, 'a', encoding='utf-8') as f:
            f.write("\n# Birdeye API Configuration\nBIRDEYE_API_KEY=your_api_key_here\n")
        print("⚠️ Added BIRDEYE_API_KEY to .env - please update with your actual key!")
        return False
    elif 'BIRDEYE_API_KEY=your_api_key_here' in content or 'BIRDEYE_API_KEY=\n' in content:
        print("⚠️ BIRDEYE_API_KEY found but not set! Please update in .env file")
        return False
        
    print("✅ BIRDEYE_API_KEY found in .env")
    return True

def verify_config_files():
    """Verify configuration files have Birdeye settings"""
    config_path = "config/trading_params.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Add Birdeye configuration if missing
        if 'birdeye' not in config:
            config['birdeye'] = {
                "enabled": True,
                "strategies": ["trending", "gainers", "new"],
                "max_tokens_per_scan": 30,
                "cache_ttl": 300
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            print(f"✅ Added Birdeye configuration to {config_path}")
        else:
            print(f"✅ Birdeye configuration found in {config_path}")
    else:
        print(f"⚠️ {config_path} not found")

def main():
    """Run all fixes"""
    print("🔧 Birdeye API Quick Fix Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        return
        
    # Create backups and apply fixes
    print("\n1. Checking environment...")
    env_ok = check_env_file()
    
    print("\n2. Backing up files...")
    backup_file("core/data/market_data.py")
    backup_file("core/data/token_scanner.py")
    
    print("\n3. Fixing Birdeye initialization...")
    fix_birdeye_initialization()
    
    print("\n4. Updating enhanced bot...")
    update_enhanced_bot()
    
    print("\n5. Verifying configuration...")
    verify_config_files()
    
    print("\n" + "=" * 50)
    print("✅ Fixes applied!")
    
    if not env_ok:
        print("\n⚠️ IMPORTANT: Update your BIRDEYE_API_KEY in the .env file!")
        
    print("\n📝 Next steps:")
    print("1. Copy the updated market_data.py from the previous artifact")
    print("2. Ensure your BIRDEYE_API_KEY is set in .env")
    print("3. Run: python birdeye_integration_test.py")
    print("4. Start your bot: python start_bot.py simulation")
    
    print("\n💡 To test immediately:")
    print("python -c \"import asyncio; from core.data.market_data import BirdeyeAPI; asyncio.run(BirdeyeAPI().get_trending_tokens())\"")

if __name__ == "__main__":
    main()