#!/usr/bin/env python3
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
