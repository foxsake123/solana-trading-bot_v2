# fix_trading_params.py
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_trading_parameters():
    """Update trading parameters to enable trade execution"""
    
    # Load current parameters
    with open('config/trading_params.json', 'r') as f:
        params = json.load(f)
    
    # Save backup
    backup_name = f"config/trading_params_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_name, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Backed up to {backup_name}")
    
    # Update parameters for better execution
    updates = {
        # Lower thresholds to get trades executing
        "min_token_score": 0.5,  # Down from 0.7
        "min_ml_confidence": 0.5,  # Down from 0.7
        
        # Citadel strategy thresholds
        "citadel_min_alpha": 0.1,  # Lower threshold
        "citadel_alpha_threshold": 0.15,  # For buy signals
        
        # Position sizing (4-7% target)
        "position_size_min": 0.04,  # 4%
        "position_size_max": 0.07,  # 7%
        "absolute_min_sol": 0.4,    # Minimum 0.4 SOL per trade
        
        # Risk parameters
        "max_open_positions": 10,
        "stop_loss_percentage": 5.0,
        "take_profit_percentage": 50.0,
        
        # Ensure simulation mode is on
        "simulation_mode": True,
        "initial_balance": 10.0,
        
        # Volume filters (lower for more opportunities)
        "min_volume_24h": 10000,  # $10k minimum
        "min_liquidity": 5000,    # $5k minimum
    }
    
    # Apply updates
    params.update(updates)
    
    # Save updated parameters
    with open('config/trading_params.json', 'w') as f:
        json.dump(params, f, indent=2)
    
    logger.info("Updated trading parameters:")
    for key, value in updates.items():
        logger.info(f"  {key}: {value}")
    
    return params

if __name__ == "__main__":
    update_trading_parameters()