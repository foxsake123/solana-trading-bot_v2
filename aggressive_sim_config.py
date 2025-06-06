#!/usr/bin/env python3
"""
Create aggressive simulation configuration for faster results
"""
import json
import shutil
from datetime import datetime

def create_aggressive_config():
    """Create config for aggressive simulation trading"""
    
    print("🚀 Creating aggressive simulation configuration...")
    
    # Backup current configs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy('config/bot_control.json', f'config/bot_control_backup_{timestamp}.json')
    
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
    with open('config/bot_control_aggressive.json', 'w') as f:
        json.dump(aggressive_control, f, indent=2)
    
    print("✅ Created config/bot_control_aggressive.json")
    
    # Create start script
    start_script = """#!/usr/bin/env python3
import shutil
import os
import time

print("🚀 Starting aggressive simulation...")

# Backup current config
shutil.copy('config/bot_control.json', 'config/bot_control_normal.json')

# Use aggressive config
shutil.copy('config/bot_control_aggressive.json', 'config/bot_control.json')

print("✅ Aggressive config loaded")
print("\\nStarting bot with aggressive settings...")
print("This will make many more trades quickly!")
print("\\nPress Ctrl+C to stop")

# Start the bot
os.system('python start_bot.py simulation')
"""
    
    with open('start_aggressive_sim.py', 'w') as f:
        f.write(start_script)
    
    print("✅ Created start_aggressive_sim.py")
    
    # Also update trading params for bigger positions
    with open('config/trading_params.json', 'r') as f:
        params = json.load(f)
    
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
    
    with open('config/trading_params_aggressive.json', 'w') as f:
        json.dump(params, f, indent=2)
    
    print("✅ Created config/trading_params_aggressive.json")
    
    print("\n📋 AGGRESSIVE SETTINGS:")
    print("- Position sizes: 3-5% (0.3-0.5 SOL)")
    print("- Take profit: 10% (faster)")
    print("- Stop loss: 3% (tighter)")
    print("- ML threshold: 50% (more trades)")
    print("- Scan interval: 30 seconds")
    print("- Max positions: 10")
    
    print("\n🎯 TO START AGGRESSIVE SIMULATION:")
    print("1. Stop current bot (Ctrl+C)")
    print("2. Run: python start_aggressive_sim.py")
    print("3. Monitor with: python enhanced_sim_monitor.py")
    
    print("\n⚠️  This will trade much more frequently!")
    print("You should see 50+ trades within 1-2 hours")

if __name__ == "__main__":
    create_aggressive_config()
