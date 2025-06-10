#!/usr/bin/env python3
"""
Direct fix for Birdeye API headers issue
"""

# Open core/data/market_data.py and add this line after self.api_key = api_key:
# self.headers = {"X-API-KEY": self.api_key}

# Here's a simple script to do it:
import fileinput

with fileinput.FileInput('core/data/market_data.py', inplace=True) as file:
    for line in file:
        print(line, end='')
        if 'self.api_key = api_key' in line and 'self.headers' not in line:
            indent = len(line) - len(line.lstrip())
            print(' ' * indent + 'self.headers = {"X-API-KEY": self.api_key}')

print("Fixed headers in BirdeyeAPI")
