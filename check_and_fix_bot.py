# check_and_fix_bot.py
import os
import json

# 1. Check actual file structure
print("📁 Checking bot structure...")

trader_files = [
    "core/blockchain/solana_trader.py",
    "core/blockchain/simplified_solana_trader.py",
    "simplified_solana_trader.py",
    "core/trading/solana_trader.py"
]

actual_trader = None
for f in trader_files:
    if os.path.exists(f):
        print(f"✓ Found: {f}")
        actual_trader = f
        break

if not actual_trader:
    print("❌ No trader file found!")

# 2. Fix bot to use basic trading
with open('config/trading_params.json', 'r') as f:
    config = json.load(f)

# Ultra-simple config
config.update({
    "min_token_score": 0.0,
    "min_ml_confidence": 0.0,
    "use_citadel_strategy": False,
    "min_price_change_24h": -100.0,  # Accept any price change
    "min_volume_24h": 0,  # No volume requirement
    "position_size_min": 0.05,
    "position_size_max": 0.10,
    "stop_loss_percentage": 10.0,
    "take_profit_percentage": 20.0
})

with open('config/trading_params.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ Config updated - ALL thresholds removed")
print("\n🎯 The bot should execute trades now")
print("   Run: python start_bot.py")
print("\nIf still no trades after 2 minutes, the analyze_and_trade_token")
print("method is not being called properly in your bot.")