#!/usr/bin/env python3
"""
Emergency fix for bot configuration to prevent overspending
"""
import json
import shutil
from datetime import datetime

def fix_bot_configuration():
    """Emergency fix for bot configuration"""
    print("🚨 APPLYING EMERGENCY CONFIGURATION FIXES...")
    
    # Backup current configs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Fix trading_params.json
    trading_params_file = 'config/trading_params.json'
    shutil.copy(trading_params_file, f'config/trading_params_BACKUP_{timestamp}.json')
    
    with open(trading_params_file, 'r') as f:
        params = json.load(f)
    
    # CRITICAL FIXES
    params['max_open_positions'] = 3  # Was 10, too many!
    params['min_position_size_pct'] = 1.0  # Was 2-3%
    params['default_position_size_pct'] = 1.5  # Was 3-4%
    params['max_position_size_pct'] = 2.0  # Was 5%
    params['absolute_min_sol'] = 0.01  # Was 0.02
    params['absolute_max_sol'] = 0.02  # Was 0.05, CRITICAL to limit this!
    params['max_portfolio_risk_pct'] = 10.0  # Was 30%, way too high
    params['ml_confidence_threshold'] = 0.80  # Was 0.65, increase for safety
    params['min_volume_24h'] = 100000.0  # Was 30000, increase quality
    params['stop_loss_pct'] = 0.03  # Was 0.05, tighter stop
    
    with open(trading_params_file, 'w') as f:
        json.dump(params, f, indent=2)
    
    print(f"✅ Fixed trading_params.json (backup: trading_params_BACKUP_{timestamp}.json)")
    
    # Fix bot_control_real.json
    real_config_file = 'config/bot_control_real.json'
    try:
        shutil.copy(real_config_file, f'config/bot_control_real_BACKUP_{timestamp}.json')
        
        with open(real_config_file, 'r') as f:
            config = json.load(f)
        
        # CRITICAL FIXES
        config['max_open_positions'] = 3
        config['max_position_size_sol'] = 0.02  # HARD LIMIT
        config['max_daily_loss_percentage'] = 0.03  # 3% max daily loss
        config['pause_on_daily_loss'] = True
        config['ml_confidence_threshold'] = 0.80
        config['require_high_confidence'] = True
        config['starting_balance'] = 0.0015  # Update to current balance
        
        with open(real_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Fixed bot_control_real.json (backup: bot_control_real_BACKUP_{timestamp}.json)")
    except:
        print("❌ No bot_control_real.json found")
    
    # Create safety override file
    safety_override = {
        "EMERGENCY_MODE": True,
        "max_position_sol": 0.02,
        "max_positions": 3,
        "require_balance_check": True,
        "min_balance_sol": 0.001,
        "block_duplicate_tokens": True,
        "cooldown_seconds": 300  # 5 minute cooldown between trades
    }
    
    with open('config/SAFETY_OVERRIDE.json', 'w') as f:
        json.dump(safety_override, f, indent=2)
    
    print("✅ Created SAFETY_OVERRIDE.json for extra protection")
    
    # Show what changed
    print("\n📋 CONFIGURATION CHANGES APPLIED:")
    print("- Max positions: 10 → 3")
    print("- Position size: 3-5% → 1-2% (max 0.02 SOL)")
    print("- ML threshold: 0.65 → 0.80")
    print("- Min volume: $30k → $100k")
    print("- Max daily loss: 5% → 3%")
    print("- Added duplicate token blocking")
    print("- Added 5-minute trade cooldown")
    
    print("\n⚠️  IMPORTANT NEXT STEPS:")
    print("1. Check your tokens on Solscan")
    print("2. Sell any tokens manually if needed to recover SOL")
    print("3. Add more SOL to wallet before restarting bot")
    print("4. Start bot with monitoring:")
    print("   python start_bot.py real")
    print("   python real_trade_monitor.py (in another terminal)")

if __name__ == "__main__":
    fix_bot_configuration()
