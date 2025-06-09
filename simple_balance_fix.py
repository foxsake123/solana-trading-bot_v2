#!/usr/bin/env python3
"""
Simple fix for balance issue without Unicode characters
"""
import os
import shutil
from datetime import datetime

def fix_balance_simple():
    """Fix the balance issue in solana_client.py"""
    
    print("FIXING BALANCE ISSUE")
    print("=" * 60)
    
    file_path = 'core/blockchain/solana_client.py'
    
    if not os.path.exists(file_path):
        print("ERROR: solana_client.py not found!")
        return False
    
    # Create backup
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the problematic line in get_wallet_balance
    fixed = False
    in_get_wallet_balance = False
    
    for i, line in enumerate(lines):
        # Check if we're in get_wallet_balance method
        if 'def get_wallet_balance(self)' in line:
            in_get_wallet_balance = True
            
        # Look for the hardcoded balance line
        if in_get_wallet_balance and 'self.wallet_balance = 1.0' in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            # Comment out the line instead of replacing
            lines[i] = '            # ' + line.lstrip() + '            # FIXED: This was overwriting the balance\n'
            fixed = True
            print("Fixed the line by commenting it out")
            break
            
        # Exit the method when we see another def
        if in_get_wallet_balance and line.strip().startswith('def ') and 'get_wallet_balance' not in line:
            in_get_wallet_balance = False
    
    if fixed:
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("SUCCESS: Fixed solana_client.py!")
        print("\nThe bot will now use the balance from config (10.0 SOL)")
    else:
        print("WARNING: Could not find the problematic line")
        print("Checking for alternative patterns...")
        
        # Alternative fix - look for any wallet_balance = 1.0
        for i, line in enumerate(lines):
            if 'self.wallet_balance = 1.0' in line and 'Default to 1 SOL' not in line:
                print(f"Found balance assignment at line {i+1}")
                lines[i] = '            # ' + line.lstrip() + '            # FIXED: Removed hardcoded balance\n'
                fixed = True
        
        if fixed:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print("Applied alternative fix")
    
    # Also ensure __init__ sets proper balance
    print("\nChecking __init__ method...")
    
    # Read again to check
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'self.wallet_balance = 1.0  # Default to 1 SOL' in content:
        print("Found hardcoded balance in __init__")
        content = content.replace(
            'self.wallet_balance = 1.0  # Default to 1 SOL for simulation',
            'self.wallet_balance = 10.0  # Default to 10 SOL for simulation'
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated default balance to 10.0 SOL")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Restart the bot: python start_bot.py simulation")
    print("2. Check logs for 'Balance: 10.0000 SOL'")
    print("3. Watch for trades with 0.4+ SOL positions")
    
    return True

if __name__ == "__main__":
    fix_balance_simple()