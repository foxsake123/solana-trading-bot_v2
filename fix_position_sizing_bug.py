#!/usr/bin/env python3
"""
Fix the position sizing calculation bug
"""
import json

def fix_position_sizing():
    """Fix the position sizing that's calculating 47+ SOL positions"""
    
    print("FIXING POSITION SIZING BUG")
    print("=" * 60)
    
    # First, let's check the current config
    print("\n1. Checking current configuration...")
    
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    print(f"Current max_position_size_pct: {config.get('max_position_size_pct', 'NOT SET')}%")
    print(f"Current base_size_pct: {config.get('position_size_rules', {}).get('base_size_pct', 'NOT SET')}%")
    
    # The issue: position sizing is using wrong calculation
    # 47.8492 SOL on 6.8356 SOL balance = 700% position!
    
    # Fix the configuration
    print("\n2. Fixing configuration...")
    
    # Ensure reasonable limits
    config['max_position_size_pct'] = 8.0  # Maximum 8% of balance
    config['min_position_size_pct'] = 4.0  # Minimum 4% of balance  
    config['default_position_size_pct'] = 5.0  # Default 5% of balance
    
    # Fix absolute limits
    config['absolute_min_sol'] = 0.4
    config['absolute_max_sol'] = 0.8  # Maximum 0.8 SOL per position
    
    # Fix position size rules
    if 'position_size_rules' in config:
        config['position_size_rules']['base_size_pct'] = 5.0  # 5% base size
        
    # Ensure Kelly safety factor is reasonable
    config['kelly_safety_factor'] = 0.25  # Use only 25% of Kelly criterion
    
    # Save the fixed config
    with open('config/trading_params.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("✅ Fixed position sizing configuration")
    
    # Create a position size override file
    print("\n3. Creating position size safety check...")
    
    safety_check = '''"""
Position size safety check to prevent oversized positions
"""
import logging

logger = logging.getLogger(__name__)

def safe_position_size(calculated_size: float, balance: float, config: dict) -> float:
    """
    Ensure position size is reasonable
    
    :param calculated_size: The calculated position size
    :param balance: Current balance
    :param config: Configuration dict
    :return: Safe position size
    """
    # Get limits from config
    min_pct = config.get('min_position_size_pct', 4.0) / 100
    max_pct = config.get('max_position_size_pct', 8.0) / 100
    abs_min = config.get('absolute_min_sol', 0.4)
    abs_max = config.get('absolute_max_sol', 0.8)
    
    # Calculate percentage of balance
    if balance > 0:
        pct_of_balance = calculated_size / balance
        
        # Log if position is unreasonable
        if pct_of_balance > 0.5:  # More than 50% of balance
            logger.warning(f"Position size {calculated_size:.2f} is {pct_of_balance*100:.1f}% of balance!")
            logger.warning(f"Capping at {max_pct*100}% = {balance * max_pct:.2f} SOL")
            calculated_size = balance * max_pct
    
    # Apply percentage limits
    min_size = max(abs_min, balance * min_pct)
    max_size = min(abs_max, balance * max_pct)
    
    # Ensure within bounds
    safe_size = max(min_size, min(max_size, calculated_size))
    
    if safe_size != calculated_size:
        logger.info(f"Adjusted position size from {calculated_size:.4f} to {safe_size:.4f} SOL")
    
    return safe_size
'''
    
    with open('position_size_safety.py', 'w') as f:
        f.write(safety_check)
    
    print("✅ Created position_size_safety.py")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. The config has been fixed")
    print("2. Restart the bot: python start_bot.py simulation")
    print("3. Position sizes should now be 0.4-0.8 SOL (not 47 SOL!)")
    
    return True

def reset_simulation_balance():
    """Reset the simulation to fresh start"""
    
    print("\nRESETTING SIMULATION BALANCE")
    print("=" * 60)
    
    # Clear the active orders that are affecting balance calculation
    import sqlite3
    
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        cursor = conn.cursor()
        
        # Check how many old trades we have
        cursor.execute("SELECT COUNT(*) FROM trades WHERE amount = 0.1")
        old_trades = cursor.fetchone()[0]
        
        print(f"Found {old_trades} old trades with 0.1 SOL positions")
        
        # Option to clear old simulation data
        print("\nTo start fresh with 10.0 SOL balance:")
        print("1. Delete old trades: DELETE FROM trades WHERE amount = 0.1;")
        print("2. Or ignore them in balance calculation")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_position_sizing()
    # reset_simulation_balance()  # Uncomment to see reset options