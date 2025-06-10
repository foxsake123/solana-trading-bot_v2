# test_birdeye_simple.py
"""
Simple test script to verify Birdeye API is working
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_birdeye():
    """Simple test of Birdeye API"""
    # Import the updated market_data module
    from core.data.market_data import BirdeyeAPI, MarketDataAggregator
    
    # Get API key
    api_key = os.getenv('BIRDEYE_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: Please set your BIRDEYE_API_KEY in the .env file!")
        return
        
    print(f"Testing Birdeye API...")
    print(f"API Key: {api_key[:10]}...")
    
    # Test 1: Direct API test
    async with BirdeyeAPI(api_key) as birdeye:
        print("\nTesting trending tokens...")
        tokens = await birdeye.get_trending_tokens(limit=5)
        
        if tokens:
            print(f"SUCCESS: Found {len(tokens)} trending tokens:")
            for i, token in enumerate(tokens[:3], 1):
                print(f"{i}. {token['symbol']}: ${token['price']:.6f} ({token['price_change_24h']:+.2f}%)")
        else:
            print("ERROR: No tokens found. Check your API key.")
            
    # Test 2: Aggregator test
    print("\nTesting Market Data Aggregator...")
    aggregator = MarketDataAggregator(api_key)
    all_tokens = await aggregator.discover_tokens(max_tokens=10)
    
    if all_tokens:
        print(f"SUCCESS: Aggregator found {len(all_tokens)} tokens")
    else:
        print("ERROR: Aggregator failed to find tokens")

if __name__ == "__main__":
    asyncio.run(test_birdeye())