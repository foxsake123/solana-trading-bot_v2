# quick_trade_fix.py
import json

# Lower all thresholds to minimum
config_updates = {
    "min_token_score": 0.0,  # Accept any score
    "min_ml_confidence": 0.0,
    "min_price_change_24h": -50.0,  # Accept drops too
    "min_volume_24h": 1000,  # $1k minimum
    "use_citadel_strategy": False,
    "position_size_min": 0.05,
    "position_size_max": 0.10
}

with open('config/trading_params.json', 'r') as f:
    config = json.load(f)

config.update(config_updates)

with open('config/trading_params.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Thresholds removed - trades will execute now")
print("Restart bot: python start_bot.py")