#!/usr/bin/env python3
"""
Clean up configuration files and ensure percentage-based sizing is used
"""
import json
import shutil
from datetime import datetime
from colorama import init, Fore, Style

init()

def clean_bot_control():
    """Remove legacy position sizing from bot_control.json"""
    print(f"{Fore.YELLOW}Cleaning bot_control.json...{Style.RESET_ALL}")
    
    # Backup first
    shutil.copy('config/bot_control.json', f'config/bot_control.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    with open('config/bot_control.json', 'r') as f:
        bot_control = json.load(f)
    
    # Remove all legacy position sizing fields
    fields_to_remove = [
        'min_investment_per_token',
        'max_investment_per_token', 
        'default_position_size_sol',
        'default_position_size',
        'position_size',
        'investment_per_token'
    ]
    
    removed = []
    for field in fields_to_remove:
        if field in bot_control:
            del bot_control[field]
            removed.append(field)
    
    # Ensure use_percentage_sizing is set
    bot_control['use_percentage_sizing'] = True
    bot_control['position_sizing_config'] = "See config/trading_params.json"
    
    # Save cleaned config
    with open('config/bot_control.json', 'w') as f:
        json.dump(bot_control, f, indent=4)
    
    if removed:
        print(f"{Fore.GREEN}✅ Removed legacy fields: {', '.join(removed)}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✅ No legacy fields found{Style.RESET_ALL}")
    
    return bot_control

def ensure_trading_params():
    """Ensure trading_params.json has all required fields"""
    print(f"\n{Fore.YELLOW}Checking trading_params.json...{Style.RESET_ALL}")
    
    try:
        with open('config/trading_params.json', 'r') as f:
            params = json.load(f)
    except:
        params = {}
    
    # Required fields with defaults
    required = {
        'min_position_size_pct': 3.0,
        'default_position_size_pct': 4.0,
        'max_position_size_pct': 5.0,
        'absolute_min_sol': 0.1,
        'absolute_max_sol': 2.0,
        'max_open_positions': 10,
        'take_profit_pct': 0.5,      # 50% profit target
        'stop_loss_pct': 0.05,       # 5% stop loss
        'trailing_stop_enabled': True,
        'trailing_stop_activation_pct': 0.3,  # Activate at 30% profit
        'trailing_stop_distance_pct': 0.15    # Trail by 15%
    }
    
    added = []
    for field, default in required.items():
        if field not in params:
            params[field] = default
            added.append(f"{field}={default}")
    
    # Save updated params
    with open('config/trading_params.json', 'w') as f:
        json.dump(params, f, indent=4)
    
    if added:
        print(f"{Fore.GREEN}✅ Added missing fields: {', '.join(added)}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✅ All required fields present{Style.RESET_ALL}")
    
    return params

def display_final_config():
    """Display the final configuration"""
    with open('config/trading_params.json', 'r') as f:
        params = json.load(f)
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print("FINAL POSITION SIZING CONFIGURATION")
    print(f"{'='*60}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Position Sizes (% of balance):{Style.RESET_ALL}")
    print(f"  Minimum: {params['min_position_size_pct']}%")
    print(f"  Default: {params['default_position_size_pct']}%")
    print(f"  Maximum: {params['max_position_size_pct']}%")
    
    print(f"\n{Fore.YELLOW}With different balances:{Style.RESET_ALL}")
    for balance in [10, 25, 50, 100]:
        default_size = balance * params['default_position_size_pct'] / 100
        print(f"  {balance} SOL balance → {default_size:.2f} SOL per trade")
    
    print(f"\n{Fore.YELLOW}Exit Strategy:{Style.RESET_ALL}")
    print(f"  Take Profit: {params['take_profit_pct']*100:.0f}%")
    print(f"  Stop Loss: {params['stop_loss_pct']*100:.0f}%")
    if params['trailing_stop_enabled']:
        print(f"  Trailing Stop: Activates at {params['trailing_stop_activation_pct']*100:.0f}%, trails by {params['trailing_stop_distance_pct']*100:.0f}%")

def main():
    print(f"{Fore.CYAN}{'='*60}")
    print("CONFIGURATION CLEANUP & FIX")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Clean bot_control.json
    bot_control = clean_bot_control()
    
    # Ensure trading_params.json has all fields
    params = ensure_trading_params()
    
    # Display final config
    display_final_config()
    
    print(f"\n{Fore.GREEN}✅ Configuration cleaned and ready!{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}IMPORTANT NEXT STEPS:{Style.RESET_ALL}")
    print("1. Replace your trading_bot.py with the fixed version")
    print("2. Restart your bot")
    print("3. Monitor that positions are now 3-5% of balance")
    print(f"\n{Fore.CYAN}To adjust position sizes: python adjust_positions.py{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
