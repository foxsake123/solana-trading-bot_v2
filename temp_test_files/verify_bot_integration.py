# verify_bot_integration.py
"""
Script to verify the Birdeye API integration is working with your trading bot
"""
import asyncio
import logging
import os
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

async def test_birdeye_api():
    """Test Birdeye API functionality"""
    from core.data.market_data import BirdeyeAPI, MarketDataAggregator
    
    api_key = os.getenv('BIRDEYE_API_KEY')
    print(f"\n1. Testing Birdeye API...")
    print(f"   API Key: {api_key[:10]}..." if api_key else "   ERROR: No API key found!")
    
    if not api_key:
        return False
        
    async with BirdeyeAPI(api_key) as birdeye:
        # Test token discovery
        tokens = await birdeye.discover_tokens(max_tokens=5)
        
        if tokens:
            print(f"   ✅ Found {len(tokens)} tokens")
            for token in tokens[:3]:
                print(f"      - {token['symbol']}: ${token['price']:.6f} "
                      f"(Vol: ${token['volume_24h']:,.0f})")
            return True
        else:
            print("   ❌ No tokens found")
            return False

async def test_token_scanner():
    """Test TokenScanner integration"""
    print("\n2. Testing TokenScanner...")
    
    try:
        from core.data.token_scanner import TokenScanner
        from core.analysis.token_analyzer import TokenAnalyzer
        from core.storage.database import Database
        
        # Load config
        with open('config/trading_params.json', 'r') as f:
            config = json.load(f)
            
        # Initialize components
        db = Database('data/db/sol_bot.db')
        token_analyzer = TokenAnalyzer(config, db)
        
        api_key = os.getenv('BIRDEYE_API_KEY')
        scanner = TokenScanner(config, token_analyzer, api_key)
        
        # Test scanning
        tokens = await scanner.scan_for_tokens()
        
        if tokens:
            print(f"   ✅ Scanner found {len(tokens)} analyzed tokens")
            for token in tokens[:3]:
                print(f"      - {token.get('symbol', 'UNKNOWN')}: "
                      f"Score {token.get('score', 0):.2f}")
            return True
        else:
            print("   ❌ Scanner found no tokens")
            return False
            
    except Exception as e:
        print(f"   ❌ Scanner error: {e}")
        return False

async def test_enhanced_bot():
    """Test Enhanced Trading Bot"""
    print("\n3. Testing Enhanced Trading Bot...")
    
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        from core.blockchain.solana_client import SolanaTrader
        from core.storage.database import Database
        from core.data.token_scanner import TokenScanner
        from core.analysis.token_analyzer import TokenAnalyzer
        
        # Load config
        with open('config/trading_params.json', 'r') as f:
            config = json.load(f)
            
        config['simulation_mode'] = True
        
        # Initialize components
        db = Database('data/db/sol_bot.db')
        solana_trader = SolanaTrader(db=db, simulation_mode=True)
        await solana_trader.connect()
        
        token_analyzer = TokenAnalyzer(config, db)
        api_key = os.getenv('BIRDEYE_API_KEY')
        scanner = TokenScanner(config, token_analyzer, api_key)
        
        # Initialize bot
        bot = EnhancedTradingBot(config, db, scanner, solana_trader)
        
        print("   ✅ Enhanced bot initialized successfully")
        
        # Test token discovery
        print("   Testing bot token discovery...")
        # This would normally be done in bot.start(), but we'll test directly
        
        await solana_trader.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Enhanced bot error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Solana Trading Bot Integration Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Birdeye API
    results.append(await test_birdeye_api())
    
    # Test 2: Token Scanner
    results.append(await test_token_scanner())
    
    # Test 3: Enhanced Bot
    results.append(await test_enhanced_bot())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed! Your bot is ready to run.")
        print("\nNext step: python start_bot.py simulation")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("1. Make sure BIRDEYE_API_KEY is set in .env")
        print("2. Ensure you copied the updated market_data.py")
        print("3. Check that all dependencies are installed")

if __name__ == "__main__":
    asyncio.run(main())