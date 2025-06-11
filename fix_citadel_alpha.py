# fix_citadel_alpha.py
"""
Fix Citadel strategy to generate actual trading signals
"""

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_citadel_config():
    """Update config to make Citadel strategy generate signals"""
    
    # Load current config
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    # Citadel-specific parameters for signal generation
    citadel_updates = {
        # Lower alpha thresholds
        "citadel_min_alpha": 0.05,          # Down from 0.1
        "citadel_alpha_threshold": 0.1,     # Down from 0.15
        "alpha_decay_halflife_hours": 48,   # Longer decay
        
        # Adjust signal weights for better alpha
        "signal_weights": {
            "momentum": 0.4,         # Increase momentum weight
            "mean_reversion": 0.2,
            "volume_breakout": 0.3,  # Increase volume weight
            "ml_prediction": 0.1     # Reduce ML weight if not trained
        },
        
        # Factor constraints
        "max_factor_exposure": 3.0,  # Allow more exposure
        "target_idiosyncratic_ratio": 0.5,  # Lower requirement
        
        # Position sizing adjustments
        "kelly_safety_factor": 0.3,  # Increase from 0.25
        "volatility_scalar_max": 1.5,  # Allow larger positions
        
        # More aggressive for testing
        "use_citadel_strategy": True,
        "citadel_aggressive_mode": True  # New flag for testing
    }
    
    # Apply updates
    config.update(citadel_updates)
    
    # Save updated config
    with open('config/trading_params.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("Updated Citadel configuration for better signal generation")
    for key, value in citadel_updates.items():
        logger.info(f"  {key}: {value}")

def create_citadel_patch():
    """Create a temporary patch for the Citadel strategy"""
    
    patch_code = '''# citadel_strategy_patch.py
"""
Temporary patch to fix Citadel alpha generation
Add this to your citadel_barra_strategy.py
"""

def calculate_alpha_signals_fixed(self, token_data: Dict, factors: BarraFactors) -> Dict[str, float]:
    """Fixed alpha calculation that generates actual signals"""
    
    alpha_signals = {}
    
    # 1. Momentum Alpha (simplified but working)
    price_change = token_data.get('price_change_24h', 0) / 100
    volume_change = token_data.get('volume_change_24h', 0) / 100
    
    momentum_alpha = 0.0
    if price_change > 0.1:  # 10% price increase
        momentum_alpha = min(price_change * 0.5, 0.3)  # Cap at 0.3
        if volume_change > 0.5:  # 50% volume increase
            momentum_alpha *= 1.5  # Boost for volume confirmation
    
    alpha_signals['momentum'] = momentum_alpha
    
    # 2. Volume Breakout Alpha
    volume_24h = token_data.get('volume_24h', 0)
    liquidity = token_data.get('liquidity', 1)
    
    volume_ratio = volume_24h / max(liquidity, 1)
    volume_alpha = 0.0
    
    if volume_ratio > 2.0:  # Volume > 2x liquidity
        volume_alpha = min((volume_ratio - 2.0) * 0.1, 0.2)
    
    alpha_signals['volume_breakout'] = volume_alpha
    
    # 3. Mean Reversion Alpha (for oversold)
    if price_change < -0.2:  # 20% drop
        mean_reversion_alpha = min(abs(price_change) * 0.3, 0.15)
        alpha_signals['mean_reversion'] = mean_reversion_alpha
    else:
        alpha_signals['mean_reversion'] = 0.0
    
    # 4. ML Prediction (use simple heuristic if no ML)
    ml_alpha = 0.0
    if factors.volume_stability > 0.5 and factors.holder_quality > 0.3:
        ml_alpha = 0.1
    
    alpha_signals['ml_prediction'] = ml_alpha
    
    return alpha_signals

# Replace the method in CitadelBarraStrategy class
'''
    
    # Save patch file
    with open('citadel_strategy_patch.py', 'w') as f:
        f.write(patch_code)
    
    logger.info("Created citadel_strategy_patch.py")
    logger.info("Add the calculate_alpha_signals_fixed method to your CitadelBarraStrategy class")

if __name__ == "__main__":
    update_citadel_config()
    create_citadel_patch()