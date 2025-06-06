#!/usr/bin/env python3
"""
Fix simulation parameters to ensure aggressive settings are applied
"""
import json
import shutil
from datetime import datetime

def fix_aggressive_params():
    """Ensure aggressive parameters are properly set"""
    
    print("Fixing simulation parameters for aggressive trading...")
    print("="*60)
    
    # Backup current files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Update bot_control.json
    try:
        with open('config/bot_control.json', 'r', encoding='utf-8') as f:
            bot_control = json.load(f)
    except:
        bot_control = {}
    
    # Apply aggressive settings
    bot_control.update({
        "simulation_mode": True,
        "starting_simulation_balance": 10.0,
        "current_simulation_balance": 8.9356,  # Your current balance
        "running": True,
        "use_machine_learning": True,
        "ml_confidence_threshold": 0.40,  # Even lower for more trades
        "filter_fake_tokens": False,
        "use_birdeye_api": True,
        
        # Aggressive settings
        "max_open_positions": 15,  # More positions
        "scan_interval": 20,  # Scan every 20 seconds
        "take_profit_target": 1.08,  # 8% take profit
        "stop_loss_percentage": 0.02,  # 2% stop loss
        "trailing_stop_enabled": False,
        
        # Very low requirements
        "MIN_SAFETY_SCORE": 0.0,
        "MIN_VOLUME": 5000.0,  # Lower
        "MIN_LIQUIDITY": 2000.0,  # Lower
        "MIN_MCAP": 5000.0,  # Lower
        "MIN_HOLDERS": 5,  # Lower
        "MIN_PRICE_CHANGE_1H": -90.0,
        "MIN_PRICE_CHANGE_6H": -90.0,
        "MIN_PRICE_CHANGE_24H": -90.0,
        "MAX_PRICE_CHANGE_24H": 50000.0,
        
        # Force percentage sizing
        "use_percentage_sizing": True,
        "position_sizing_config": "AGGRESSIVE - See trading_params.json"
    })
    
    # Save updated bot_control.json
    with open('config/bot_control.json', 'w', encoding='utf-8') as f:
        json.dump(bot_control, f, indent=2)
    
    print("✅ Updated bot_control.json")
    
    # Update trading_params.json with much larger positions
    try:
        with open('config/trading_params.json', 'r', encoding='utf-8') as f:
            params = json.load(f)
    except:
        params = {}
    
    # AGGRESSIVE position sizing - much larger
    params.update({
        # Percentage-based sizing
        "min_position_size_pct": 5.0,      # 5% minimum (0.5 SOL)
        "default_position_size_pct": 8.0,  # 8% default (0.8 SOL)
        "max_position_size_pct": 10.0,     # 10% maximum (1.0 SOL)
        
        # Absolute limits
        "absolute_min_sol": 0.4,   # 0.4 SOL minimum
        "absolute_max_sol": 1.0,   # 1.0 SOL maximum
        
        # Faster exits
        "take_profit_pct": 0.08,   # 8% take profit
        "stop_loss_pct": 0.02,     # 2% stop loss
        "trailing_stop_enabled": False,
        
        # Lower all requirements
        "ml_confidence_threshold": 0.40,
        "min_volume_24h": 5000.0,
        "min_liquidity": 2000.0,
        "min_holders": 5,
        "min_market_cap": 5000.0,
        "min_safety_score": 0.0,
        
        # ML settings
        "use_ml_predictions": True,
        "ml_weight_in_decision": 0.2,  # Lower weight
        
        # Risk settings
        "max_daily_loss_pct": 0.5,  # Allow 50% daily loss in simulation
        "max_drawdown_pct": 0.6,    # Allow 60% drawdown
        "max_portfolio_risk_pct": 100.0,  # No limit in simulation
        
        # More positions
        "max_open_positions": 15
    })
    
    # Save updated trading_params.json
    with open('config/trading_params.json', 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2)
    
    print("✅ Updated trading_params.json")
    
    # Create a quick position size test
    print("\n" + "="*60)
    print("POSITION SIZE CALCULATION TEST:")
    print("="*60)
    
    balance = 8.9356
    min_pct = params['min_position_size_pct']
    default_pct = params['default_position_size_pct']
    max_pct = params['max_position_size_pct']
    
    print(f"Current Balance: {balance:.4f} SOL")
    print(f"\nPosition Sizes:")
    print(f"  Minimum ({min_pct}%): {balance * min_pct / 100:.4f} SOL")
    print(f"  Default ({default_pct}%): {balance * default_pct / 100:.4f} SOL")
    print(f"  Maximum ({max_pct}%): {balance * max_pct / 100:.4f} SOL")
    
    print("\n" + "="*60)
    print("AGGRESSIVE SETTINGS APPLIED:")
    print("="*60)
    print("✅ Position sizes: 5-10% (0.4-1.0 SOL)")
    print("✅ Take profit: 8% (very fast)")
    print("✅ Stop loss: 2% (very tight)")
    print("✅ ML threshold: 40% (many more trades)")
    print("✅ Scan interval: 20 seconds")
    print("✅ Max positions: 15")
    print("✅ Minimal requirements for tokens")
    
    print("\n⚠️  RESTART THE BOT for changes to take effect!")
    print("\n1. Stop the bot: Ctrl+C")
    print("2. Restart: python start_bot.py simulation")
    print("3. Monitor: python scripts/monitoring/enhanced_sim_monitor.py")
    
    print("\n🎯 EXPECTED RESULTS:")
    print("- 5-10 trades per hour")
    print("- Position sizes 0.4-1.0 SOL")
    print("- Many quick profits/losses")
    print("- 50+ trades within 2 hours")

if __name__ == "__main__":
    fix_aggressive_params()
