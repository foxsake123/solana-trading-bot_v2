#!/usr/bin/env python3
"""
Fix the encoding and indentation issues
"""
import os
import shutil

def fix_trading_bot_indentation():
    """Fix the indentation error in trading_bot.py"""
    
    # Find the trading bot file
    bot_path = "core/trading/trading_bot.py"
    
    if not os.path.exists(bot_path):
        print(f"❌ {bot_path} not found!")
        return False
    
    # First, restore from backup if available
    backup_path = f"{bot_path}.backup_positions"
    if os.path.exists(backup_path):
        print(f"Found backup at {backup_path}")
        response = input("Restore from backup? (y/n): ")
        if response.lower() == 'y':
            shutil.copy2(backup_path, bot_path)
            print(f"✅ Restored {bot_path} from backup")
            return True
    
    # If no backup or user said no, try to fix the indentation
    print(f"Attempting to fix indentation in {bot_path}...")
    
    with open(bot_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Look for the problematic line
    fixed = False
    for i, line in enumerate(lines):
        if 'tx_hash = await self.trader.buy_token(address, amount)' in line:
            # Check the indentation of surrounding lines
            if i > 0:
                # Get indentation from previous line
                prev_line = lines[i-1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                
                # Fix the current line's indentation
                current_line = line.lstrip()
                lines[i] = ' ' * prev_indent + current_line
                fixed = True
                print(f"Fixed indentation at line {i+1}")
    
    if fixed:
        # Save the fixed file
        with open(bot_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ Fixed indentation in {bot_path}")
        return True
    else:
        print("❌ Could not find the problematic line")
        return False

def create_simple_position_checker():
    """Create a simple position size checker without emojis"""
    checker_code = '''#!/usr/bin/env python3
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
    print(f"\\nAfter loading from control file:")
    print(f"MAX_INVESTMENT_PER_TOKEN: {BotConfiguration.TRADING_PARAMETERS.get('MAX_INVESTMENT_PER_TOKEN')}")
    
except Exception as e:
    print(f"Error loading BotConfiguration: {e}")

# Check control files directly
print("\\nDirect file check:")
with open('config/bot_control.json', 'r') as f:
    control = json.load(f)
    print(f"bot_control.json - min_investment_per_token: {control.get('min_investment_per_token')}")
    print(f"bot_control.json - max_investment_per_token: {control.get('max_investment_per_token')}")
    print(f"bot_control.json - min_position_size_sol: {control.get('min_position_size_sol')}")
    print(f"bot_control.json - max_position_size_sol: {control.get('max_position_size_sol')}")
'''
    
    with open("check_position_sizes.py", "w", encoding='utf-8') as f:
        f.write(checker_code)
    print("✅ Created check_position_sizes.py")

def check_current_config():
    """Check current configuration values"""
    import json
    
    print("\n📋 Current Configuration Values:")
    
    # Check bot_control.json
    with open("config/bot_control.json", "r") as f:
        bot_control = json.load(f)
    
    print("\nPosition Sizes in bot_control.json:")
    print(f"  min_investment_per_token: {bot_control.get('min_investment_per_token')}")
    print(f"  max_investment_per_token: {bot_control.get('max_investment_per_token')}")
    print(f"  min_position_size_sol: {bot_control.get('min_position_size_sol')}")
    print(f"  max_position_size_sol: {bot_control.get('max_position_size_sol')}")
    
    # Check trading_params.json
    if os.path.exists("config/trading_params.json"):
        with open("config/trading_params.json", "r") as f:
            trading_params = json.load(f)
        
        print("\nPosition Sizes in trading_params.json:")
        print(f"  min_position_size_sol: {trading_params.get('min_position_size_sol')}")
        print(f"  max_position_size_sol: {trading_params.get('max_position_size_sol')}")

def main():
    print("🔧 FIXING BOT ISSUES")
    print("="*60)
    
    # Fix trading bot indentation
    print("\n1. Fixing trading_bot.py indentation error...")
    if fix_trading_bot_indentation():
        print("✅ Fixed indentation issue")
    else:
        print("❌ Could not fix automatically")
        print("   You may need to manually edit core/trading/trading_bot.py")
        print("   Look for line 145 and fix the indentation")
    
    # Create position checker
    print("\n2. Creating position size checker...")
    create_simple_position_checker()
    
    # Check current config
    print("\n3. Checking current configuration...")
    check_current_config()
    
    print("\n" + "="*60)
    print("✅ Fixes applied!")
    print("\nNext steps:")
    print("1. Run: python check_position_sizes.py")
    print("2. Start bot: python start_bot.py simulation")
    print("3. Monitor: python enhanced_monitor.py")
    
    print("\n⚠️  Important: Position sizes are now set to 0.3-0.5 SOL")
    print("   If they're still small, we need to check the actual")
    print("   position calculation logic in the bot.")

if __name__ == "__main__":
    main()
