#!/usr/bin/env python3
"""
Create aggressive simulation configuration for faster results
"""
import json
import shutil
from datetime import datetime

def create_aggressive_config():
    """Create config for aggressive simulation trading"""
    
    print("Creating aggressive simulation configuration...")
    
    # Backup current configs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy('config/bot_control.json', f'config/bot_control_backup_{timestamp}.json')
        print(f"Backed up current config to bot_control_backup_{timestamp}.json")
    except:
        print("No existing config to backup, creating new one")
    
    # Create aggressive bot control
    aggressive_control = {
        "simulation_mode": True,
        "starting_simulation_balance": 10.0,
        "running": True,
        "use_machine_learning": True,
        "ml_confidence_threshold": 0.50,  # Lower threshold
        "filter_fake_tokens": False,
        "use_birdeye_api": True,
        
        # Aggressive settings
        "max_open_positions": 10,  # More positions
        "scan_interval": 30,  # Scan every 30 seconds
        "take_profit_target": 1.10,  # 10% take profit
        "stop_loss_percentage": 0.03,  # 3% stop loss
        "trailing_stop_enabled": False,  # Disable for faster trades
        
        # Lower requirements for more trades
        "MIN_SAFETY_SCORE": 0.0,
        "MIN_VOLUME": 10000.0,
        "MIN_LIQUIDITY": 5000.0,
        "MIN_MCAP": 10000.0,
        "MIN_HOLDERS": 10,
        "MIN_PRICE_CHANGE_1H": -50.0,
        "MIN_PRICE_CHANGE_6H": -50.0,
        "MIN_PRICE_CHANGE_24H": -50.0,
        "MAX_PRICE_CHANGE_24H": 10000.0,
        
        # Position sizing
        "position_sizing_config": "See config/trading_params.json",
        "use_percentage_sizing": True
    }
    
    # Save aggressive control
    with open('config/bot_control_aggressive.json', 'w', encoding='utf-8') as f:
        json.dump(aggressive_control, f, indent=2)
    
    print("Created config/bot_control_aggressive.json")
    
    # Create start script with proper encoding
    start_script = """#!/usr/bin/env python3
import shutil
import os
import time

print("Starting aggressive simulation...")

# Backup current config
try:
    shutil.copy('config/bot_control.json', 'config/bot_control_normal.json')
    print("Backed up normal config")
except:
    print("No existing config to backup")

# Use aggressive config
shutil.copy('config/bot_control_aggressive.json', 'config/bot_control.json')

print("Aggressive config loaded")
print("\\nStarting bot with aggressive settings...")
print("This will make many more trades quickly!")
print("\\nPress Ctrl+C to stop")

# Start the bot
os.system('python start_bot.py simulation')
"""
    
    with open('start_aggressive_sim.py', 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    print("Created start_aggressive_sim.py")
    
    # Also update trading params for bigger positions
    try:
        with open('config/trading_params.json', 'r', encoding='utf-8') as f:
            params = json.load(f)
    except:
        print("Creating new trading_params.json")
        params = {}
    
    # Aggressive position sizing
    params['min_position_size_pct'] = 3.0  # 3% minimum
    params['default_position_size_pct'] = 4.0  # 4% default  
    params['max_position_size_pct'] = 5.0  # 5% maximum
    params['absolute_min_sol'] = 0.3  # 0.3 SOL minimum
    params['absolute_max_sol'] = 0.5  # 0.5 SOL maximum
    
    # Faster exits
    params['take_profit_pct'] = 0.10  # 10% take profit
    params['stop_loss_pct'] = 0.03  # 3% stop loss
    params['trailing_stop_enabled'] = False
    
    # Lower requirements
    params['ml_confidence_threshold'] = 0.50
    params['min_volume_24h'] = 10000.0
    params['min_liquidity'] = 5000.0
    params['min_holders'] = 50
    params['min_market_cap'] = 50000.0
    
    # More aggressive ML settings
    params['use_ml_predictions'] = True
    params['ml_weight_in_decision'] = 0.3  # Lower weight, more trades
    
    with open('config/trading_params_aggressive.json', 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2)
    
    print("Created config/trading_params_aggressive.json")
    
    # Create a restore script too
    restore_script = """#!/usr/bin/env python3
import shutil
import os

print("Restoring normal configuration...")

try:
    shutil.copy('config/bot_control_normal.json', 'config/bot_control.json')
    print("Normal config restored")
except:
    print("No backup found, please manually restore your config")

print("Done! You can now run 'python start_bot.py simulation' with normal settings")
"""
    
    with open('restore_normal_config.py', 'w', encoding='utf-8') as f:
        f.write(restore_script)
    
    print("Created restore_normal_config.py")
    
    print("\n" + "="*60)
    print("AGGRESSIVE SETTINGS CREATED:")
    print("="*60)
    print("- Position sizes: 3-5% (0.3-0.5 SOL)")
    print("- Take profit: 10% (faster)")
    print("- Stop loss: 3% (tighter)")
    print("- ML threshold: 50% (more trades)")
    print("- Scan interval: 30 seconds")
    print("- Max positions: 10")
    print("- Lower volume/liquidity requirements")
    
    print("\n" + "="*60)
    print("TO START AGGRESSIVE SIMULATION:")
    print("="*60)
    print("1. Stop current bot (Ctrl+C)")
    print("2. Run: python start_aggressive_sim.py")
    print("3. Monitor with: python scripts/monitoring/ultra_monitor_mode_aware.py")
    
    print("\nTO RESTORE NORMAL SETTINGS:")
    print("Run: python restore_normal_config.py")
    
    print("\nWARNING: This will trade much more frequently!")
    print("You should see 50+ trades within 1-2 hours")
    print("\nNOTE: Higher frequency = more chances to learn patterns")
    print("but also more transaction costs in real trading")

if __name__ == "__main__":
    create_aggressive_config()
