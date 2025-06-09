#!/usr/bin/env python3
"""
Find where 0.1 SOL limit might be hardcoded
"""

import os
import re

def find_position_limits():
    """Search for hardcoded position limits in Python files"""
    
    print("Searching for hardcoded position limits...")
    print("="*60)
    
    # Patterns to search for
    patterns = [
        r'0\.1\s*(?:#.*SOL|.*position|.*amount)',  # 0.1 with SOL/position/amount in comment
        r'amount.*=.*0\.1',  # amount = 0.1
        r'max.*0\.1',  # max(..., 0.1)
        r'min.*0\.1',  # min(..., 0.1)
        r'position.*0\.1',  # position ... 0.1
        r'MAX_INVESTMENT_PER_TOKEN.*0\.1',  # specific config
        r'max_investment_per_token.*0\.1',  # specific config
    ]
    
    # Files to check
    files_to_check = [
        'core/trading/trading_bot.py',
        'enhanced_trading_bot.py',
        'config/bot_config.py',
        'position_calculator.py',
        'core/blockchain/solana_client.py',
        'main.py',
        'start_bot.py'
    ]
    
    # Also check all Python files in core directory
    for root, dirs, files in os.walk('core'):
        for file in files:
            if file.endswith('.py'):
                files_to_check.append(os.path.join(root, file))
    
    # Remove duplicates
    files_to_check = list(set(files_to_check))
    
    findings = []
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for i, line in enumerate(lines):
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                'file': filepath,
                                'line_num': i + 1,
                                'line': line.strip()
                            })
                            
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    # Display findings
    if findings:
        print("\n🔍 FOUND POTENTIAL POSITION LIMITS:")
        print("-"*60)
        
        for finding in findings:
            print(f"\nFile: {finding['file']}")
            print(f"Line {finding['line_num']}: {finding['line']}")
    else:
        print("\nNo obvious hardcoded 0.1 SOL limits found.")
    
    # Check config files
    print("\n\n📄 CHECKING CONFIG FILES:")
    print("-"*60)
    
    config_files = [
        'config/bot_config.py',
        'config/bot_control.json',
        'config/trading_params.json',
        'config/data/bot_control.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                # Look for investment/position settings
                if 'max_investment' in content.lower() or 'position' in content.lower():
                    print(f"\n{config_file}:")
                    
                    # For JSON files
                    if config_file.endswith('.json'):
                        import json
                        data = json.loads(content)
                        for key, value in data.items():
                            if 'investment' in key.lower() or 'position' in key.lower():
                                print(f"  {key}: {value}")
                    else:
                        # For Python files, find relevant lines
                        for line in content.split('\n'):
                            if 'investment' in line.lower() or 'position' in line.lower():
                                if '=' in line and not line.strip().startswith('#'):
                                    print(f"  {line.strip()}")
                                    
            except Exception as e:
                print(f"Error reading {config_file}: {e}")
    
    print("\n\n💡 SOLUTION:")
    print("-"*60)
    print("The issue is likely in one of these places:")
    print("1. MAX_INVESTMENT_PER_TOKEN in config/bot_config.py")
    print("2. max_investment_per_token in bot_control.json")
    print("3. A hardcoded limit in the trading bot")
    print("\nRun this command to update all configs:")
    print("python update_all_position_sizes.py")

if __name__ == "__main__":
    find_position_limits()