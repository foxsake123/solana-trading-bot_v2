#!/usr/bin/env python3
"""
Quick fix to adjust position sizing for your current balance
"""
import json
from colorama import init, Fore, Style

init()

def quick_fix_positions():
    """Quickly adjust position settings for low balance"""
    
    print(f"{Fore.YELLOW}QUICK POSITION SIZING FIX{Style.RESET_ALL}")
    print("="*50)
    
    # Load current config
    with open('config/trading_params.json', 'r') as f:
        params = json.load(f)
    
    current_balance = float(input("Enter your current balance in SOL: "))
    
    print(f"\n{Fore.CYAN}Current Settings:{Style.RESET_ALL}")
    print(f"Default position: {params['default_position_size_pct']}% = {current_balance * params['default_position_size_pct'] / 100:.4f} SOL")
    print(f"Absolute minimum: {params['absolute_min_sol']} SOL")
    
    if params['absolute_min_sol'] > current_balance * 0.1:
        print(f"\n{Fore.RED}⚠️  Problem: Minimum position ({params['absolute_min_sol']} SOL) is too large!{Style.RESET_ALL}")
        print(f"This is {params['absolute_min_sol'] / current_balance * 100:.1f}% of your balance!")
    
    print(f"\n{Fore.YELLOW}Recommended Settings for {current_balance} SOL balance:{Style.RESET_ALL}")
    
    if current_balance < 2.0:
        # Very low balance - use aggressive percentages
        recommended = {
            'min_position_size_pct': 8.0,
            'default_position_size_pct': 10.0,
            'max_position_size_pct': 12.0,
            'absolute_min_sol': 0.05,  # Lower minimum
            'absolute_max_sol': current_balance * 0.15
        }
        mode = "LOW BALANCE MODE"
    elif current_balance < 5.0:
        # Low balance - use moderate percentages
        recommended = {
            'min_position_size_pct': 5.0,
            'default_position_size_pct': 7.0,
            'max_position_size_pct': 9.0,
            'absolute_min_sol': 0.1,
            'absolute_max_sol': current_balance * 0.12
        }
        mode = "MODERATE MODE"
    else:
        # Normal balance
        recommended = {
            'min_position_size_pct': 3.0,
            'default_position_size_pct': 4.0,
            'max_position_size_pct': 5.0,
            'absolute_min_sol': 0.1,
            'absolute_max_sol': 2.0
        }
        mode = "NORMAL MODE"
    
    print(f"\n{mode}:")
    print(f"Position sizes: {recommended['min_position_size_pct']}-{recommended['default_position_size_pct']}-{recommended['max_position_size_pct']}%")
    print(f"Default position: {current_balance * recommended['default_position_size_pct'] / 100:.4f} SOL")
    print(f"Absolute minimum: {recommended['absolute_min_sol']} SOL")
    print(f"Absolute maximum: {recommended['absolute_max_sol']:.4f} SOL")
    
    apply = input(f"\n{Fore.YELLOW}Apply these settings? (y/n): {Style.RESET_ALL}").lower()
    
    if apply == 'y':
        # Update params
        for key, value in recommended.items():
            params[key] = value
        
        # Save
        with open('config/trading_params.json', 'w') as f:
            json.dump(params, f, indent=4)
        
        print(f"\n{Fore.GREEN}✅ Settings updated successfully!{Style.RESET_ALL}")
        print(f"\nWith {current_balance} SOL balance:")
        print(f"- Each position will be ~{current_balance * recommended['default_position_size_pct'] / 100:.4f} SOL")
        print(f"- You can open ~{int(current_balance / (current_balance * recommended['default_position_size_pct'] / 100))} positions")
        print(f"- This leaves room for fees and flexibility")
    else:
        print(f"\n{Fore.YELLOW}Settings not changed.{Style.RESET_ALL}")

if __name__ == "__main__":
    quick_fix_positions()
