#!/usr/bin/env python3
import shutil
import os
import time

print("Starting aggressive simulation...")

# Backup current config
try:
    shutil.copy('config/bot_control.json', 'config/bot_control_normal.json')
    print("Backed up normal config")
except:
    print("No existing config to backup")

# Use aggressive config
shutil.copy('config/bot_control_aggressive.json', 'config/bot_control.json')

print("Aggressive config loaded")
print("\nStarting bot with aggressive settings...")
print("This will make many more trades quickly!")
print("\nPress Ctrl+C to stop")

# Start the bot
os.system('python start_bot.py simulation')
