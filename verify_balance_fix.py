#!/usr/bin/env python3
"""
Verify the balance fix worked
"""
import asyncio
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

async def verify_balance():
    """Test if balance is now correct"""
    
    print("VERIFYING BALANCE FIX")
    print("=" * 60)
    
    # Test 1: Check initialization
    print("\n1. Testing SolanaTrader initialization...")
    db = Database('data/db/sol_bot.db')
    trader = SolanaTrader(db=db, simulation_mode=True)
    
    print(f"   Initial wallet_balance: {trader.wallet_balance} SOL")
    
    if trader.wallet_balance == 10.0:
        print("   SUCCESS: Wallet balance is 10.0 SOL")
    elif trader.wallet_balance == 1.0:
        print("   ERROR: Still using old 1.0 SOL default")
    else:
        print(f"   WARNING: Unexpected balance: {trader.wallet_balance}")
    
    # Test 2: Check get_wallet_balance
    print("\n2. Testing get_wallet_balance() method...")
    await trader.connect()
    
    # Store initial balance
    initial = trader.wallet_balance
    
    # Call get_wallet_balance
    balance_sol, balance_usd = await trader.get_wallet_balance()
    
    print(f"   Returned: {balance_sol} SOL (${balance_usd})")
    print(f"   Internal wallet_balance after call: {trader.wallet_balance} SOL")
    
    if balance_sol == 0.0:
        print("   ERROR: get_wallet_balance returned 0!")
        print("   The fix may not have worked properly")
    elif balance_sol == 1.0:
        print("   ERROR: get_wallet_balance using hardcoded 1.0!")
    elif balance_sol >= 10.0 or balance_sol == initial:
        print("   SUCCESS: Balance is correct!")
    else:
        print(f"   INFO: Balance is {balance_sol} (calculated from trades)")
    
    await trader.close()
    
    # Test 3: Check source code
    print("\n3. Checking source code...")
    try:
        with open('core/blockchain/solana_client.py', 'r') as f:
            content = f.read()
        
        issues = []
        
        # Check for problematic patterns
        if 'self.wallet_balance = 1.0' in content and '# FIXED' not in content:
            # Check if it's commented out
            for line in content.split('\n'):
                if 'self.wallet_balance = 1.0' in line and not line.strip().startswith('#'):
                    issues.append("Found uncommented 'self.wallet_balance = 1.0'")
                    break
        
        if issues:
            print("   Issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("   SUCCESS: No hardcoded balance issues found")
            
    except Exception as e:
        print(f"   ERROR reading file: {e}")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    
    if balance_sol >= 6.0:  # Could be 6.8 from your calculated balance
        print("Balance fix appears successful!")
        print("The bot should now be able to trade with 0.4+ SOL positions")
    else:
        print("Balance issue may still exist")
        print("Run 'python simple_balance_fix.py' to fix")

if __name__ == "__main__":
    asyncio.run(verify_balance())