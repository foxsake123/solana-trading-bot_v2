# force_trade_now.py
import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.storage.database import Database
from core.blockchain.simplified_solana_trader import SolanaTrader
from core.data.token_scanner import TokenScanner
from core.data.market_data import BirdeyeAPI

async def force_trade():
    """Force a trade execution to test the system"""
    
    # Load config
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    # Initialize components
    db = Database()
    trader = SolanaTrader(config)
    
    # Create a test token to trade
    test_token = {
        'contract_address': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
        'symbol': 'SOL',
        'name': 'Wrapped SOL',
        'price_usd': 100.0,
        'price_change_24h': 15.5,
        'volume_24h': 1000000,
        'liquidity': 500000
    }
    
    print("🚀 Forcing trade execution...")
    print(f"Token: {test_token['symbol']}")
    print(f"Price change: {test_token['price_change_24h']}%")
    
    # Execute buy
    amount = 0.5  # 0.5 SOL
    result = await trader.buy_token(test_token['contract_address'], amount)
    
    if result['success']:
        print(f"✅ Trade executed!")
        print(f"   Amount: {amount} SOL")
        print(f"   TX: {result['transaction_id']}")
        print(f"   New balance: {trader.balance} SOL")
    else:
        print(f"❌ Trade failed: {result.get('error')}")
    
    # Check database
    trades = db.get_recent_trades(limit=1)
    if trades:
        print(f"\n📊 Trade recorded in database")
        print(f"   ID: {trades[0]['id']}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(force_trade())