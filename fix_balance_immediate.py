#!/usr/bin/env python3
"""
Immediately fix the balance tracking issue
"""
import os
import json
import shutil
from datetime import datetime

def fix_balance_now():
    """Fix the balance tracking issue immediately"""
    
    print("🔧 IMMEDIATE BALANCE FIX")
    print("="*60)
    
    # Step 1: Update bot_control.json
    print("\n1. Checking bot_control.json...")
    config_files = [
        'config/bot_control.json',
        'bot_control.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Ensure starting balance is set
                if config.get('starting_simulation_balance', 0) != 10.0:
                    config['starting_simulation_balance'] = 10.0
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    print(f"✅ Updated {config_file}: starting_simulation_balance = 10.0")
                else:
                    print(f"✅ {config_file} already has starting_simulation_balance = 10.0")
                    
            except Exception as e:
                print(f"Error updating {config_file}: {e}")
    
    # Step 2: Fix solana_client.py
    print("\n2. Fixing core/blockchain/solana_client.py...")
    
    solana_file = 'core/blockchain/solana_client.py'
    
    if not os.path.exists(solana_file):
        print(f"❌ {solana_file} not found!")
        return False
    
    # Create backup
    backup_file = f"{solana_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(solana_file, backup_file)
    print(f"✅ Created backup: {backup_file}")
    
    # Read the file
    with open(solana_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it needs fixing
    if 'self.wallet_balance = 1.0' in content:
        print("❌ Found hardcoded balance = 1.0 SOL")
        
        # Replace the problematic line
        content = content.replace(
            'self.wallet_balance = 1.0  # Default to 1 SOL for simulation',
            '''# Load starting balance from config
        if simulation_mode:
            try:
                import json
                with open('config/bot_control.json', 'r') as f:
                    config = json.load(f)
                self.wallet_balance = config.get('starting_simulation_balance', 10.0)
                logger.info(f"Loaded starting balance: {self.wallet_balance} SOL")
            except:
                self.wallet_balance = 10.0  # Default fallback
        else:
            self.wallet_balance = 0.0  # Will be set from actual wallet'''
        )
        
        # Write the fixed content
        with open(solana_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed solana_client.py!")
        
    else:
        # Try alternative fix
        print("⚠️  Standard fix pattern not found, applying alternative fix...")
        
        # Find the __init__ method and replace it
        import re
        
        # Pattern to find the __init__ method
        init_pattern = r'def __init__\(self, db=None, simulation_mode=True\):\s*"""[^"]*"""\s*self\.db = db\s*self\.simulation_mode = simulation_mode\s*self\.wallet_balance = [^#\n]+'
        
        if re.search(init_pattern, content, re.DOTALL):
            # Replace with fixed version
            fixed_init = '''def __init__(self, db=None, simulation_mode=True):
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
                logger.info(f"Loaded starting balance: {self.wallet_balance} SOL")
            except:
                self.wallet_balance = 10.0  # Default fallback
        else:
            self.wallet_balance = 0.0  # Will be set from actual wallet'''
            
            # Find where to insert the rest of the __init__ method
            # Look for the line after wallet_balance assignment
            remaining_init = '''
        self.wallet_address = "SIMULATED_WALLET_ADDRESS"
        self.private_key = None
        self.sol_price = 170.0  # Default SOL price
        self.token_prices = {}  # Cache for token prices
        
        logger.info(f"Initialized SolanaTrader (simulation_mode={simulation_mode}, balance={self.wallet_balance} SOL)")'''
            
            # Create the full replacement
            full_replacement = fixed_init + remaining_init
            
            # Replace the entire __init__ method
            content = re.sub(
                r'def __init__\(self, db=None, simulation_mode=True\):.*?logger\.info\(f"Initialized SolanaTrader.*?\)"?\)',
                full_replacement,
                content,
                flags=re.DOTALL
            )
            
            # Write the fixed content
            with open(solana_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Applied alternative fix to solana_client.py!")
    
    # Step 3: Verify the fix
    print("\n3. Verifying the fix...")
    
    # Check if the file now contains the fix
    with open(solana_file, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    if 'starting_simulation_balance' in new_content:
        print("✅ Balance fix successfully applied!")
        print("\n💰 The bot will now start with 10.0 SOL")
        print("🚀 Restart the bot to see the changes:")
        print("   python start_bot.py simulation")
        return True
    else:
        print("❌ Fix may not have been applied correctly")
        print("   Please check the backup and apply manually if needed")
        return False

if __name__ == "__main__":
    fix_balance_now()