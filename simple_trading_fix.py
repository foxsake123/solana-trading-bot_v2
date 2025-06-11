# simple_trading_fix.py
"""
Simple fix to get your bot trading immediately
"""

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_simple_fix():
    """Apply minimal changes to start trading"""
    
    # 1. Update trading_params.json
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    # Simplify to use basic strategy without Citadel blocking
    config.update({
        # Disable Citadel temporarily
        "use_citadel_strategy": False,
        
        # Lower all thresholds
        "min_token_score": 0.3,
        "min_ml_confidence": 0.3,
        
        # Ensure we have criteria that will trigger
        "min_price_change_24h": 5.0,   # 5% minimum
        "min_volume_24h": 5000,         # $5k volume
        
        # Position sizing
        "position_size_min": 0.04,      # 4%
        "position_size_max": 0.07,      # 7%
        
        # Risk management
        "stop_loss_percentage": 5.0,
        "take_profit_percentage": 50.0,
        
        # Ensure simulation mode
        "simulation_mode": True,
        "initial_balance": 10.0
    })
    
    with open('config/trading_params.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("✅ Applied simple trading fix")
    logger.info("Bot will now use basic scoring without Citadel blocking")
    logger.info("Thresholds lowered to enable trades")
    
    # 2. Create bot control file to ensure running
    bot_control = {
        "bot_running": True,
        "last_updated": "2025-06-10T19:45:00Z"
    }
    
    with open('config/bot_control.json', 'w') as f:
        json.dump(bot_control, f, indent=2)
    
    logger.info("✅ Bot control file updated")
    
    return config

if __name__ == "__main__":
    config = apply_simple_fix()
    
    print("\n🚀 READY TO TRADE!")
    print("Run: python start_bot.py")
    print(f"Min score threshold: {config['min_token_score']}")
    print(f"Position size: {config['position_size_min']*100:.0f}-{config['position_size_max']*100:.0f}%")
    print(f"Citadel strategy: {'Enabled' if config['use_citadel_strategy'] else 'Disabled'}")