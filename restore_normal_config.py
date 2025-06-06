#!/usr/bin/env python3
import shutil
import os

print("Restoring normal configuration...")

try:
    shutil.copy('config/bot_control_normal.json', 'config/bot_control.json')
    print("Normal config restored")
except:
    print("No backup found, please manually restore your config")

print("Done! You can now run 'python start_bot.py simulation' with normal settings")
