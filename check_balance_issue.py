#!/usr/bin/env python3
"""
Quick script to check why balance is showing as 0.0 SOL
"""
import asyncio
import json
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

async def check_balance_issue():
    """Check what's causing the balance issue"""
    
    print("🔍 BALANCE ISSUE DIAGNOSIS")
    print("="*60)
    
    # Check config
    print("\n1. Checking configuration...")
    try:
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
        
        starting_balance = config.get('starting_simulation_balance', 'NOT SET')
        print(f"   starting_simulation_balance: {starting_balance}")
        
        if starting_balance == 'NOT SET':
            print("   ❌ Missing starting_simulation_balance in config!")
        elif starting_balance != 10.0:
            print(f"   ⚠️  Balance is {starting_balance}, should be 10.0")
        else:
            print("   ✅ Config looks correct")
            
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
    
    # Check SolanaTrader initialization
    print("\n2. Testing SolanaTrader initialization...")
    try:
        db = Database('data/db/sol_bot.db')
        trader = SolanaTrader(db=db, simulation_mode=True)
        
        print(f"   Initial wallet_balance: {trader.wallet_balance}")
        
        if trader.wallet_balance == 1.0:
            print("   ❌ Balance is hardcoded to 1.0 SOL!")
        elif trader.wallet_balance == 0.0:
            print("   ❌ Balance is 0.0 - config not loading!")
        elif trader.wallet_balance == 10.0:
            print("   ✅ Balance correctly set to 10.0 SOL")
        else:
            print(f"   ⚠️  Unexpected balance: {trader.wallet_balance}")
        
        # Test get_wallet_balance
        await trader.connect()
        balance_sol, balance_usd = await trader.get_wallet_balance()
        
        print(f"\n3. get_wallet_balance() result:")
        print(f"   SOL: {balance_sol}")
        print(f"   USD: {balance_usd}")
        
        if balance_sol == 0.0:
            print("   ❌ get_wallet_balance returning 0!")
            print("   This explains why bot shows 'Balance: 0.0000 SOL'")
            
        await trader.close()
        
    except Exception as e:
        print(f"   ❌ Error testing SolanaTrader: {e}")
        import traceback
        traceback.print_exc()
    
    # Check the source code
    print("\n4. Checking source code...")
    try:
        with open('core/blockchain/solana_client.py', 'r') as f:
            content = f.read()
        
        if 'self.wallet_balance = 1.0' in content:
            print("   ❌ Found hardcoded: self.wallet_balance = 1.0")
            print("   This needs to be fixed!")
        elif 'starting_simulation_balance' in content:
            print("   ✅ Code appears to use config")
        else:
            print("   ⚠️  Can't determine how balance is set")
            
        # Check get_wallet_balance method
        if 'self.wallet_balance = 1.0' in content and 'get_wallet_balance' in content:
            print("\n   ❌ get_wallet_balance() has hardcoded assignment!")
            print("   Line 80: self.wallet_balance = 1.0")
            print("   This overwrites any initial balance!")
            
    except Exception as e:
        print(f"   ❌ Error checking source: {e}")
    
    print("\n" + "="*60)
    print("📋 DIAGNOSIS COMPLETE")
    print("="*60)
    print("\nTo fix: run `python fix_balance_immediate.py`")

if __name__ == "__main__":
    asyncio.run(check_balance_issue())