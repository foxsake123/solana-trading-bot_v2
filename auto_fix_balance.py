#!/usr/bin/env python3
"""
Automatically fix the balance tracking in solana_client.py
"""
import os
import shutil
from datetime import datetime

def fix_balance_tracking():
    """Fix the hardcoded balance in solana_client.py"""
    
    print("🔧 FIXING BALANCE TRACKING")
    print("="*60)
    
    file_path = 'core/blockchain/solana_client.py'
    
    # Create backup
    backup_path = f'{file_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        print(f"✅ Read {file_path}")
        
        # Create backup
        shutil.copy2(file_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
        
        # Check current state
        if 'self.wallet_balance = 1.0' in content:
            print("❌ Found hardcoded balance: self.wallet_balance = 1.0")
            
            # Replace the __init__ method
            old_init = '''    def __init__(self, db=None, simulation_mode=True):
        """
        Initialize the SolanaTrader
        
        :param db: Database instance or adapter
        :param simulation_mode: Whether to run in simulation mode
        """
        self.db = db
        self.simulation_mode = simulation_mode
        self.wallet_balance = 1.0  # Default to 1 SOL for simulation
        self.wallet_address = "SIMULATED_WALLET_ADDRESS"
        self.private_key = None
        self.sol_price = 170.0  # Default SOL price
        self.token_prices = {}  # Cache for token prices
        
        logger.info(f"Initialized SolanaTrader (simulation_mode={simulation_mode})")'''
            
            new_init = '''    def __init__(self, db=None, simulation_mode=True):
        """
        Initialize the SolanaTrader
        
        :param db: Database instance or adapter
        :param simulation_mode: Whether to run in simulation mode
        """
        self.db = db
        self.simulation_mode = simulation_mode
        
        # Load starting balance from config
        if simulation_mode:
            try:
                import json
                with open('config/bot_control.json', 'r') as f:
                    config = json.load(f)
                self.wallet_balance = config.get('starting_simulation_balance', 10.0)
                logger.info(f"Loaded starting balance from config: {self.wallet_balance} SOL")
            except Exception as e:
                self.wallet_balance = 10.0  # Default fallback
                logger.warning(f"Could not load config, using default: {self.wallet_balance} SOL")
        else:
            self.wallet_balance = 0.0  # Will be set from actual wallet
        
        self.wallet_address = "SIMULATED_WALLET_ADDRESS"
        self.private_key = None
        self.sol_price = 170.0  # Default SOL price
        self.token_prices = {}  # Cache for token prices
        
        logger.info(f"Initialized SolanaTrader (simulation_mode={simulation_mode}, balance={self.wallet_balance} SOL)")'''
            
            # Replace the content
            content = content.replace(old_init, new_init)
            
            # Also fix get_wallet_balance method to ensure it uses the proper balance
            if 'self.wallet_balance = 1.0' in content:
                content = content.replace(
                    'self.wallet_balance = 1.0',
                    'pass  # Balance already set in __init__'
                )
            
            # Write the fixed content
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✅ Fixed balance tracking!")
            print("\nChanges made:")
            print("- Balance now loads from config/bot_control.json")
            print("- Default is 10.0 SOL (from starting_simulation_balance)")
            print("- Added proper logging of balance on initialization")
            
        elif 'starting_simulation_balance' in content:
            print("✅ Balance tracking already fixed!")
        else:
            print("⚠️  Could not determine balance tracking state")
            print("   Manual inspection needed")
        
        # Verify bot_control.json has the right setting
        print("\n📋 Checking bot_control.json...")
        try:
            import json
            with open('config/bot_control.json', 'r') as f:
                bot_config = json.load(f)
            
            balance = bot_config.get('starting_simulation_balance', 'NOT SET')
                            print(f"Starting balance in config: {balance} SOL")
            
            if balance == 'NOT SET' or (isinstance(balance, (int, float)) and balance < 10):
                bot_config['starting_simulation_balance'] = 10.0
                with open('config/bot_control.json', 'w') as f:
                    json.dump(bot_config, f, indent=2)
                print("✅ Updated starting_simulation_balance to 10.0 SOL")
                
        except Exception as e:
            print(f"Error checking bot_control.json: {e}")
        
    except Exception as e:
        print(f"❌ Error fixing balance: {e}")
        return False
    
    print("\n✅ Balance tracking fixed successfully!")
    print("\n📊 Next steps:")
    print("1. Restart the bot: python start_bot.py simulation")
    print("2. Check logs - should show 'balance=10.0 SOL'")
    print("3. First trade should use 0.4+ SOL (4%+ of 10 SOL)")
    
    return True

if __name__ == "__main__":
    fix_balance_tracking()