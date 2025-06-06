#!/usr/bin/env python3
"""
Quick fix to create directories and fix config
"""
import os
import json

def fix_config_and_dirs():
    """Fix the wallet address format and create necessary directories"""
    
    # Create necessary directories
    directories = [
        'core/safety',
        'core/alerts',
        'data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Fix bot_control_real.json
    try:
        with open('config/bot_control_real.json', 'r') as f:
            content = f.read()
        
        # Fix the wallet address to be a string
        # Replace the unquoted address with quoted version
        content = content.replace(
            '"real_wallet_address": 16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf',
            '"real_wallet_address": "16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf"'
        )
        
        # Write back
        with open('config/bot_control_real.json', 'w') as f:
            f.write(content)
        
        print("✅ Fixed wallet address format in bot_control_real.json")
        
        # Verify it's valid JSON now
        with open('config/bot_control_real.json', 'r') as f:
            json.load(f)
        print("✅ Config file is valid JSON")
        
    except Exception as e:
        print(f"❌ Error fixing config: {e}")

if __name__ == "__main__":
    fix_config_and_dirs()
    print("\nNow run: python safety_fixes.py")
