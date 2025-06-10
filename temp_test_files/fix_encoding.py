# fix_encoding.py
with open('EMERGENCY_STOP.py', 'w', encoding='utf-8') as f:
    f.write('''#!/usr/bin/env python3
"""EMERGENCY STOP - Immediately halt all trading"""
import json

print("EMERGENCY STOP ACTIVATED!")

with open('config/bot_control.json', 'r') as f:
    config = json.load(f)

config['running'] = False
config['emergency_stop'] = True

with open('config/bot_control.json', 'w') as f:
    json.dump(config, f, indent=4)

print("Bot stopped")
print("Review positions manually")
''')
print("Created EMERGENCY_STOP.py")