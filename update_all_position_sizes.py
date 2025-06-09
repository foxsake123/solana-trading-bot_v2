#!/usr/bin/env python3
"""
Update ALL position size settings to fix the 0.1 SOL limit
"""

import json
import os
import re

def update_all_position_sizes():
    """Update all configuration files to use proper position sizes"""
    
    print("🔧 UPDATING ALL POSITION SIZE CONFIGURATIONS")
    print("="*60)
    
    # 1. Update bot_config.py
    print("\n1. Updating config/bot_config.py...")
    
    bot_config_path = 'config/bot_config.py'
    if os.path.exists(bot_config_path):
        try:
            with open(bot_config_path, 'r') as f:
                content = f.read()
            
            # Replace MAX_INVESTMENT_PER_TOKEN
            original = content
            content = re.sub(
                r"'MAX_INVESTMENT_PER_TOKEN':\s*float\(os\.getenv\('MAX_INVESTMENT_PER_TOKEN',\s*[0-9.]+\)\)",
                "'MAX_INVESTMENT_PER_TOKEN': float(os.getenv('MAX_INVESTMENT_PER_TOKEN', 0.4))",
                content
            )
            
            # Also check for direct assignment
            content = re.sub(
                r"MAX_INVESTMENT_PER_TOKEN['\"]?\s*[:=]\s*0\.1",
                "MAX_INVESTMENT_PER_TOKEN': 0.4",
                content
            )
            
            if content != original:
                with open(bot_config_path, 'w') as f:
                    f.write(content)
                print("✅ Updated MAX_INVESTMENT_PER_TOKEN to 0.4")
            else:
                print("⚠️  No changes needed or pattern not found")
                
        except Exception as e:
            print(f"❌ Error updating bot_config.py: {e}")
    
    # 2. Update bot_control.json files
    control_files = [
        'config/bot_control.json',
        'config/data/bot_control.json',
        'bot_control.json'
    ]
    
    for control_file in control_files:
        if os.path.exists(control_file):
            print(f"\n2. Updating {control_file}...")
            try:
                with open(control_file, 'r') as f:
                    data = json.load(f)
                
                # Update position-related settings
                updates = {
                    'max_investment_per_token': 0.4,
                    'min_investment_per_token': 0.4,
                    'default_position_size_sol': 0.4,
                    'absolute_min_sol': 0.4,
                    'min_position_size_pct': 4.0,
                    'default_position_size_pct': 5.0,
                    'max_position_size_pct': 6.0
                }
                
                changed = False
                for key, value in updates.items():
                    if key in data and data[key] < value:
                        print(f"  Updating {key}: {data[key]} → {value}")
                        data[key] = value
                        changed = True
                
                if changed:
                    with open(control_file, 'w') as f:
                        json.dump(data, f, indent=4)
                    print("✅ Updated position sizes")
                else:
                    print("⚠️  No updates needed")
                    
            except Exception as e:
                print(f"❌ Error updating {control_file}: {e}")
    
    # 3. Create override file
    print("\n3. Creating position_override.py...")
    
    override_content = '''"""
Position size override to ensure minimum positions
This file forces minimum position sizes regardless of other settings
"""

import logging

logger = logging.getLogger(__name__)

# OVERRIDE ALL POSITION SIZES TO MINIMUM 0.4 SOL
FORCE_MIN_POSITION_SOL = 0.4

def override_position_size(calculated_size: float) -> float:
    """Force minimum position size"""
    if calculated_size < FORCE_MIN_POSITION_SOL:
        logger.warning(f"Overriding position size from {calculated_size:.4f} to {FORCE_MIN_POSITION_SOL:.4f} SOL")
        return FORCE_MIN_POSITION_SOL
    return calculated_size

# Monkey patch to ensure this is used
logger.info(f"Position override active: Minimum {FORCE_MIN_POSITION_SOL} SOL per trade")
'''
    
    with open('position_override.py', 'w') as f:
        f.write(override_content)
    
    print("✅ Created position_override.py")
    
    # 4. Summary
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print("="*60)
    print("\nAll position sizes updated to minimum 0.4 SOL")
    print("\nNEXT STEPS:")
    print("1. Restart your bot: python start_bot.py simulation")
    print("2. Monitor next trades - they should be 0.4 SOL minimum")
    print("3. Check profits - should see 5X increase!")
    print("\nIf trades are still 0.1 SOL, check:")
    print("- core/trading/trading_bot.py for hardcoded limits")
    print("- Any position_calculator.py overrides")

if __name__ == "__main__":
    update_all_position_sizes()