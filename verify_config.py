#!/usr/bin/env python3
"""
Verify position sizing configuration and fix any issues
"""
import json
import os
from colorama import init, Fore, Style

init()

def verify_and_fix_configs():
    """Check all config files and fix position sizing issues"""
    
    print(f"{Fore.CYAN}{'='*60}")
    print("POSITION SIZING CONFIGURATION CHECKER")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    issues_found = False
    
    # 1. Check bot_control.json
    print(f"{Fore.YELLOW}1. Checking bot_control.json...{Style.RESET_ALL}")
    try:
        with open('config/bot_control.json', 'r') as f:
            bot_control = json.load(f)
        
        # Check for problematic settings
        if 'min_investment_per_token' in bot_control:
            print(f"  {Fore.RED}❌ Found 'min_investment_per_token': {bot_control['min_investment_per_token']} SOL{Style.RESET_ALL}")
            print(f"     This is overriding percentage-based sizing!")
            issues_found = True
            
        if 'max_investment_per_token' in bot_control:
            print(f"  {Fore.RED}❌ Found 'max_investment_per_token': {bot_control['max_investment_per_token']} SOL{Style.RESET_ALL}")
            print(f"     This is overriding percentage-based sizing!")
            issues_found = True
            
        if 'default_position_size_sol' in bot_control:
            print(f"  {Fore.RED}❌ Found 'default_position_size_sol': {bot_control['default_position_size_sol']} SOL{Style.RESET_ALL}")
            print(f"     This should be removed!")
            issues_found = True
            
        if not issues_found:
            print(f"  {Fore.GREEN}✅ No legacy position settings found{Style.RESET_ALL}")
            
    except FileNotFoundError:
        print(f"  {Fore.RED}❌ bot_control.json not found{Style.RESET_ALL}")
        issues_found = True
    
    # 2. Check trading_params.json
    print(f"\n{Fore.YELLOW}2. Checking trading_params.json...{Style.RESET_ALL}")
    try:
        with open('config/trading_params.json', 'r') as f:
            trading_params = json.load(f)
        
        required_fields = [
            'min_position_size_pct',
            'default_position_size_pct', 
            'max_position_size_pct'
        ]
        
        for field in required_fields:
            if field in trading_params:
                print(f"  {Fore.GREEN}✅ {field}: {trading_params[field]}%{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}❌ Missing {field}{Style.RESET_ALL}")
                issues_found = True
                
    except FileNotFoundError:
        print(f"  {Fore.RED}❌ trading_params.json not found{Style.RESET_ALL}")
        issues_found = True
    
    # 3. Fix issues if found
    if issues_found:
        print(f"\n{Fore.YELLOW}3. Fixing issues...{Style.RESET_ALL}")
        
        # Fix bot_control.json
        try:
            with open('config/bot_control.json', 'r') as f:
                bot_control = json.load(f)
            
            # Remove problematic fields
            fields_to_remove = [
                'min_investment_per_token',
                'max_investment_per_token',
                'default_position_size_sol'
            ]
            
            for field in fields_to_remove:
                if field in bot_control:
                    del bot_control[field]
                    print(f"  {Fore.YELLOW}Removed {field} from bot_control.json{Style.RESET_ALL}")
            
            # Add flag to use percentage sizing
            bot_control['use_percentage_sizing'] = True
            
            # Save fixed config
            with open('config/bot_control.json', 'w') as f:
                json.dump(bot_control, f, indent=4)
            print(f"  {Fore.GREEN}✅ Updated bot_control.json{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"  {Fore.RED}Error fixing bot_control.json: {e}{Style.RESET_ALL}")
        
        # Ensure trading_params.json has percentage settings
        try:
            try:
                with open('config/trading_params.json', 'r') as f:
                    trading_params = json.load(f)
            except:
                trading_params = {}
            
            # Set defaults if missing
            if 'min_position_size_pct' not in trading_params:
                trading_params['min_position_size_pct'] = 3.0
            if 'default_position_size_pct' not in trading_params:
                trading_params['default_position_size_pct'] = 4.0
            if 'max_position_size_pct' not in trading_params:
                trading_params['max_position_size_pct'] = 5.0
            
            # Ensure absolute limits exist
            if 'absolute_min_sol' not in trading_params:
                trading_params['absolute_min_sol'] = 0.1
            if 'absolute_max_sol' not in trading_params:
                trading_params['absolute_max_sol'] = 2.0
            
            # Save
            with open('config/trading_params.json', 'w') as f:
                json.dump(trading_params, f, indent=4)
            print(f"  {Fore.GREEN}✅ Updated trading_params.json{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"  {Fore.RED}Error fixing trading_params.json: {e}{Style.RESET_ALL}")
    
    # 4. Show final configuration
    print(f"\n{Fore.CYAN}4. Final Configuration:{Style.RESET_ALL}")
    try:
        with open('config/trading_params.json', 'r') as f:
            trading_params = json.load(f)
        
        min_pct = trading_params.get('min_position_size_pct', 3.0)
        default_pct = trading_params.get('default_position_size_pct', 4.0)
        max_pct = trading_params.get('max_position_size_pct', 5.0)
        
        print(f"\n  Position Sizing (% of balance):")
        print(f"  - Minimum: {min_pct}%")
        print(f"  - Default: {default_pct}%") 
        print(f"  - Maximum: {max_pct}%")
        
        print(f"\n  With 10 SOL balance:")
        print(f"  - Minimum: {10 * min_pct / 100:.2f} SOL")
        print(f"  - Default: {10 * default_pct / 100:.2f} SOL")
        print(f"  - Maximum: {10 * max_pct / 100:.2f} SOL")
        
    except Exception as e:
        print(f"  {Fore.RED}Error reading final config: {e}{Style.RESET_ALL}")
    
    # 5. Important note
    print(f"\n{Fore.YELLOW}{'='*60}")
    print("IMPORTANT: Your trading bot needs to be updated!")
    print(f"{'='*60}{Style.RESET_ALL}")
    print("\nThe trading bot must use the percentage-based sizing from")
    print("trading_params.json, NOT the fixed values from bot_control.json")
    print("\nMake sure your trading_bot.py has a method like this:")
    print(f"{Fore.CYAN}")
    print("def calculate_position_size(self, balance):")
    print("    params = load_trading_params()")
    print("    pct = params['default_position_size_pct']")
    print("    return balance * (pct / 100.0)")
    print(f"{Style.RESET_ALL}")
    
    return not issues_found

if __name__ == "__main__":
    success = verify_and_fix_configs()
    
    if success:
        print(f"\n{Fore.GREEN}✅ Configuration verified and ready!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️  Configuration has been fixed. Please restart your bot.{Style.RESET_ALL}")
    
    print("\nTo easily adjust position sizes in the future, run:")
    print(f"{Fore.CYAN}python adjust_positions.py{Style.RESET_ALL}")
