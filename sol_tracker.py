#!/usr/bin/env python3
"""
SOL Balance Tracker - Finds where your SOL went
"""
import sqlite3
import json
from datetime import datetime
from colorama import init, Fore, Style

init()

def track_sol_balance():
    """Track SOL balance through trades"""
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💰 SOL BALANCE TRACKER{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Starting balance
    initial_balance = 1.0014
    current_balance = initial_balance
    
    print(f"Initial Balance: {Fore.GREEN}{initial_balance:.4f} SOL{Style.RESET_ALL}\n")
    
    # Check for real trades
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        cursor = conn.cursor()
        
        # Get all real trades
        cursor.execute("""
            SELECT 
                id, action, amount, contract_address, timestamp, 
                tx_hash, gain_loss_sol, percentage_change
            FROM trades
            WHERE tx_hash IS NOT NULL 
            AND tx_hash != 'simulated'
            ORDER BY timestamp
        """)
        
        trades = cursor.fetchall()
        
        if not trades:
            print(f"{Fore.YELLOW}No real trades found in database!{Style.RESET_ALL}")
            print("The bot may not have executed any real trades yet.")
        else:
            print(f"Found {len(trades)} real trades:\n")
            
            print(f"{'Time':<20} {'Action':<6} {'Amount':>10} {'Token':<15} {'Balance':>10}")
            print("-" * 75)
            
            tokens_bought = {}
            
            for trade in trades:
                _, action, amount, contract, timestamp, tx_hash, gain_loss, pct_change = trade
                
                # Update balance
                if action == 'BUY':
                    current_balance -= amount
                    tokens_bought[contract] = tokens_bought.get(contract, 0) + amount
                    action_color = Fore.RED
                elif action == 'SELL':
                    current_balance += amount
                    if contract in tokens_bought:
                        tokens_bought[contract] -= amount
                    action_color = Fore.GREEN
                
                # Format output
                time_str = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp
                token_short = contract[:10] + "..." if contract else "Unknown"
                
                print(f"{time_str:<20} {action_color}{action:<6}{Style.RESET_ALL} "
                      f"{amount:>10.4f} {token_short:<15} {current_balance:>10.4f}")
                
                if action == 'SELL' and gain_loss is not None:
                    pnl_color = Fore.GREEN if gain_loss > 0 else Fore.RED
                    print(f"{'':>20} P&L: {pnl_color}{gain_loss:+.4f} SOL ({pct_change:+.1f}%){Style.RESET_ALL}")
            
            print("-" * 75)
            
            # Summary
            sol_spent = initial_balance - current_balance
            
            print(f"\n{Fore.CYAN}SUMMARY:{Style.RESET_ALL}")
            print(f"Initial Balance:     {initial_balance:.4f} SOL")
            print(f"SOL Spent on Buys:   {sol_spent:.4f} SOL")
            print(f"Expected Balance:    {current_balance:.4f} SOL")
            print(f"Actual Balance:      0.0015 SOL")
            print(f"Difference:          {Fore.RED}{current_balance - 0.0015:.4f} SOL{Style.RESET_ALL}\n")
            
            # Tokens still held
            if tokens_bought:
                print(f"{Fore.CYAN}TOKENS YOU SHOULD HAVE:{Style.RESET_ALL}")
                for token, amount in tokens_bought.items():
                    if amount > 0.001:
                        print(f"  {token[:12]}...: {amount:.4f} SOL worth")
                print(f"\n{Fore.YELLOW}These tokens should appear in your wallet!{Style.RESET_ALL}")
                print(f"Check: https://solscan.io/account/16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf#tokens")
        
        conn.close()
        
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    
    # Check simulation vs real
    print(f"\n{Fore.CYAN}CHECKING FOR MIX-UP:{Style.RESET_ALL}")
    
    # Check if bot is actually in simulation mode
    try:
        with open('config/bot_control.json', 'r') as f:
            sim_config = json.load(f)
            if sim_config.get('simulation_mode', True):
                print(f"{Fore.GREEN}✓ Bot is in SIMULATION mode (config/bot_control.json){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Bot shows as REAL mode in config/bot_control.json{Style.RESET_ALL}")
    except:
        pass
    
    try:
        with open('config/bot_control_real.json', 'r') as f:
            real_config = json.load(f)
            print(f"{Fore.YELLOW}Real mode config exists with balance: {real_config.get('starting_balance')} SOL{Style.RESET_ALL}")
    except:
        print("No real mode config found")
    
    # Recommendations
    print(f"\n{Fore.CYAN}WHAT TO DO:{Style.RESET_ALL}")
    print("1. Check Solscan for your token holdings:")
    print("   https://solscan.io/account/16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf#tokens")
    print("\n2. Look at transaction history to see what happened:")
    print("   https://solscan.io/account/16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf#transactions")
    print("\n3. If tokens are there, your SOL is just converted to tokens")
    print("   - This is normal for a trading bot")
    print("   - The bot should sell them for profit")
    print("\n4. If no tokens found:")
    print("   - Check if this is the correct wallet")
    print("   - Review transaction history for unexpected transfers")
    print("   - Ensure bot didn't send to wrong address")

if __name__ == "__main__":
    track_sol_balance()
