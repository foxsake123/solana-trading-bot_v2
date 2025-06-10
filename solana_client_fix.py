#!/usr/bin/env python3
"""
Quick fix for SolanaTrader _starting_balance issue
"""
import os

def fix_solana_client():
    """Fix the _starting_balance attribute error"""
    
    # Read the current solana_client.py
    with open('core/blockchain/solana_client.py', 'r') as f:
        content = f.read()
    
    # Fix the issue by properly initializing _starting_balance
    # Find the line with the problematic code
    old_code = """        # Load starting balance from config
        if simulation_mode:
            try:
                import json
                with open('config/bot_control.json', 'r') as f:
                    config = json.load(f)
                self.wallet_balance = config.get('starting_simulation_balance', 10.0)
                logger.info(f"Loaded starting balance: {self.wallet_balance} SOL")
            except:
                # Use the initial balance instead of hardcoding
                if not hasattr(self, '_starting_balance'):
                    self._starting_balance = self.wallet_balance  # Store the initial balance
                    starting_balance = self._starting_balance
        else:
            self.wallet_balance = 0.0  # Will be set from actual wallet"""
    
    new_code = """        # Load starting balance from config
        if simulation_mode:
            try:
                import json
                with open('config/bot_control.json', 'r') as f:
                    config = json.load(f)
                self.wallet_balance = config.get('starting_simulation_balance', 10.0)
                self._starting_balance = self.wallet_balance  # Store initial balance
                logger.info(f"Loaded starting balance: {self.wallet_balance} SOL")
            except:
                self.wallet_balance = 10.0  # Default fallback
                self._starting_balance = self.wallet_balance
        else:
            self.wallet_balance = 0.0  # Will be set from actual wallet
            self._starting_balance = 0.0"""
    
    # Replace the code
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("[OK] Fixed the _starting_balance initialization")
    else:
        # Alternative fix - look for the get_wallet_balance method
        if "self._starting_balance - invested_amount" in content:
            # Add initialization after self.wallet_balance line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "self.wallet_balance = " in line and "config.get('starting_simulation_balance'" in line:
                    # Add the _starting_balance initialization on the next line
                    lines.insert(i + 1, "                self._starting_balance = self.wallet_balance  # Store initial balance")
                    break
            content = '\n'.join(lines)
            print("[OK] Added _starting_balance initialization")
    
    # Save the fixed file
    with open('core/blockchain/solana_client.py', 'w') as f:
        f.write(content)
    
    print("[OK] Fixed solana_client.py")

if __name__ == "__main__":
    fix_solana_client()
