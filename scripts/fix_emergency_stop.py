# fix_emergency_stop.py
import os

emergency_stop = '''#!/usr/bin/env python3
"""EMERGENCY STOP - Immediately halt all trading"""
import json

print("EMERGENCY STOP ACTIVATED!")
print("="*30)

with open('config/bot_control.json', 'r') as f:
    config = json.load(f)

config['running'] = False
config['emergency_stop'] = True

with open('config/bot_control.json', 'w') as f:
    json.dump(config, f, indent=4)

print("Bot stopped")
print("Check positions manually")
'''

os.makedirs("scripts", exist_ok=True)

with open("scripts/EMERGENCY_STOP.py", "w", encoding="utf-8") as f:
    f.write(emergency_stop)

print("Created scripts/EMERGENCY_STOP.py")

# Also create a minimal real_trading_setup.py
with open("scripts/real_trading_setup.py", "w", encoding="utf-8") as f:
    f.write("# Real trading setup script\n# Run this before starting real trading\n")

print("Created scripts/real_trading_setup.py")