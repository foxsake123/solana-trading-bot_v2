#!/usr/bin/env python3
"""
Update real trading configuration with actual wallet balance
"""
import json
import os
from datetime import datetime
from colorama import init, Fore, Style

init()

def update_real_balance():
    """Update the real trading config with actual wallet balance"""
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💰 UPDATING REAL WALLET BALANCE{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Your actual wallet info
    wallet_address = "16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf"
    actual_balance = 1.0014  # From Solscan
    
    print(f"Wallet Address: {wallet_address}")
    print(f"Actual Balance: {Fore.GREEN}{actual_balance} SOL{Style.RESET_ALL}")
    
    # Update bot_control_real.json
    config_path = 'config/bot_control_real.json'
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Backup current config
        backup_path = f'config/bot_control_real_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"\n✅ Backed up config to: {backup_path}")
        
        # Update values
        old_balance = config.get('starting_balance', 2.0)
        config['starting_balance'] = actual_balance
        config['real_wallet_address'] = wallet_address
        
        # Also update position limits based on actual balance
        # With 1 SOL, we should be more conservative
        config['max_position_size_sol'] = 0.05  # Max 5% of 1 SOL = 0.05 SOL
        config['max_daily_loss_percentage'] = 0.05  # Still 5% but = 0.05 SOL
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\n✅ Updated {config_path}")
        print(f"   Starting balance: {old_balance} → {actual_balance} SOL")
        print(f"   Max position size: {config['max_position_size_sol']} SOL")
        
    except Exception as e:
        print(f"\n❌ Error updating config: {e}")
        return False
    
    # Update trading_params.json for percentage-based sizing
    params_path = 'config/trading_params.json'
    
    try:
        with open(params_path, 'r') as f:
            params = json.load(f)
        
        # With 1 SOL balance, adjust percentages to be more conservative
        params['default_position_size_pct'] = 3.0  # 3% of 1 SOL = 0.03 SOL
        params['min_position_size_pct'] = 2.0     # 2% of 1 SOL = 0.02 SOL
        params['max_position_size_pct'] = 5.0     # 5% of 1 SOL = 0.05 SOL
        params['absolute_min_sol'] = 0.02         # Minimum 0.02 SOL
        params['absolute_max_sol'] = 0.05         # Maximum 0.05 SOL
        
        # Save updated params
        with open(params_path, 'w') as f:
            json.dump(params, f, indent=4)
        
        print(f"\n✅ Updated {params_path}")
        print(f"   Position sizing: {params['min_position_size_pct']}-{params['default_position_size_pct']}-{params['max_position_size_pct']}%")
        
    except Exception as e:
        print(f"\n❌ Error updating params: {e}")
    
    # Show new position sizes
    print(f"\n{Fore.CYAN}📊 NEW POSITION SIZES WITH {actual_balance} SOL:{Style.RESET_ALL}")
    print(f"   Default position: {actual_balance * 0.03:.4f} SOL (3%)")
    print(f"   Min position: {actual_balance * 0.02:.4f} SOL (2%)")
    print(f"   Max position: {actual_balance * 0.05:.4f} SOL (5%)")
    print(f"   Daily loss limit: {actual_balance * 0.05:.4f} SOL (5%)")
    
    # Safety warnings
    print(f"\n{Fore.YELLOW}⚠️  IMPORTANT NOTES:{Style.RESET_ALL}")
    print(f"1. Position sizes are now smaller due to lower balance")
    print(f"2. Max loss per day: {actual_balance * 0.05:.4f} SOL")
    print(f"3. Consider adding more SOL for better position sizing")
    print(f"4. Bot will trade with 0.02-0.05 SOL positions")
    
    # Recommendations
    print(f"\n{Fore.CYAN}💡 RECOMMENDATIONS:{Style.RESET_ALL}")
    print(f"1. With 1 SOL, you'll have limited flexibility")
    print(f"2. Consider starting with 2-3 SOL for better results")
    print(f"3. Current settings are ultra-conservative for safety")
    print(f"4. Monitor closely as small positions = small profits")
    
    return True

def show_impact():
    """Show the impact of the balance on trading"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📈 TRADING IMPACT ANALYSIS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    balance = 1.0014
    
    # Example trade scenarios
    print("Example Trade Scenarios:")
    
    # Scenario 1: Small win
    position = 0.03  # 3% position
    profit_pct = 0.30  # 30% profit (take profit)
    profit_sol = position * profit_pct
    print(f"\n{Fore.GREEN}Winning Trade (30% gain):{Style.RESET_ALL}")
    print(f"  Position: {position} SOL")
    print(f"  Profit: {profit_sol:.4f} SOL")
    print(f"  New balance: {balance + profit_sol:.4f} SOL")
    
    # Scenario 2: Loss
    loss_pct = 0.05  # 5% loss (stop loss)
    loss_sol = position * loss_pct
    print(f"\n{Fore.RED}Losing Trade (5% loss):{Style.RESET_ALL}")
    print(f"  Position: {position} SOL")
    print(f"  Loss: {loss_sol:.4f} SOL")
    print(f"  New balance: {balance - loss_sol:.4f} SOL")
    
    # Daily scenarios
    print(f"\n{Fore.CYAN}Daily Performance Scenarios:{Style.RESET_ALL}")
    
    # Good day
    daily_trades = 10
    win_rate = 0.76  # Your historical win rate
    wins = int(daily_trades * win_rate)
    losses = daily_trades - wins
    
    daily_pnl = (wins * profit_sol) - (losses * loss_sol)
    print(f"\nTypical Day ({wins} wins, {losses} losses):")
    print(f"  Expected P&L: +{daily_pnl:.4f} SOL")
    print(f"  End balance: {balance + daily_pnl:.4f} SOL")
    
    # Growth projection
    print(f"\n{Fore.CYAN}Growth Projection (if maintaining 76% win rate):{Style.RESET_ALL}")
    print(f"  Week 1: {balance * 1.05:.4f} SOL (+5%)")
    print(f"  Week 2: {balance * 1.10:.4f} SOL (+10%)")
    print(f"  Month: {balance * 1.20:.4f} SOL (+20%)")
    
    print(f"\n{Fore.YELLOW}Note: With only 1 SOL, growth will be slow but steady.{Style.RESET_ALL}")
    print(f"Consider adding funds once you verify the bot works well.")

if __name__ == "__main__":
    if update_real_balance():
        show_impact()
        
        print(f"\n{Fore.GREEN}✅ Configuration updated for your actual balance!{Style.RESET_ALL}")
        print(f"\nThe monitor will now show:")
        print(f"  Starting balance: 1.0014 SOL")
        print(f"  Current balance: [Live from blockchain]")
        print(f"  P&L: [Current - 1.0014]")
