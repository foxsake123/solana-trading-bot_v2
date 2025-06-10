#!/usr/bin/env python3
"""
Check what position sizes the bot is actually using
"""
import json
import sys
import os

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.bot_config import BotConfiguration
    
    print("Checking BotConfiguration values:")
    print(f"MAX_INVESTMENT_PER_TOKEN: {BotConfiguration.TRADING_PARAMETERS.get('MAX_INVESTMENT_PER_TOKEN')}")
    print(f"MIN_INVESTMENT: {BotConfiguration.TRADING_PARAMETERS.get('MIN_INVESTMENT', 'NOT SET')}")
    
    # Load control file
    BotConfiguration.load_trading_parameters()
    print(f"\nAfter loading from control file:")
    print(f"MAX_INVESTMENT_PER_TOKEN: {BotConfiguration.TRADING_PARAMETERS.get('MAX_INVESTMENT_PER_TOKEN')}")
    
except Exception as e:
    print(f"Error loading BotConfiguration: {e}")

# Check control files directly
print("\nDirect file check:")
with open('config/bot_control.json', 'r') as f:
    control = json.load(f)
    print(f"bot_control.json - min_investment_per_token: {control.get('min_investment_per_token')}")
    print(f"bot_control.json - max_investment_per_token: {control.get('max_investment_per_token')}")
    print(f"bot_control.json - min_position_size_sol: {control.get('min_position_size_sol')}")
    print(f"bot_control.json - max_position_size_sol: {control.get('max_position_size_sol')}")
