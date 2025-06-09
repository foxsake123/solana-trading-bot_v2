#!/usr/bin/env python3
"""
Monitor current open positions
"""

import sqlite3
import pandas as pd
from datetime import datetime
from colorama import init, Fore, Style

init()

def monitor_positions():
    """Show current open positions"""
    
    print(f"{Fore.CYAN}CURRENT OPEN POSITIONS{Style.RESET_ALL}")
    print("="*80)
    
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        
        # Get all trades
        query = """
        SELECT 
            contract_address,
            action,
            amount,
            price,
            timestamp
        FROM trades
        ORDER BY contract_address, timestamp
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No trades found")
            return
        
        # Calculate open positions
        positions = {}
        
        for address, group in df.groupby('contract_address'):
            buys = group[group['action'] == 'BUY']['amount'].sum()
            sells = group[group['action'] == 'SELL']['amount'].sum()
            
            if buys > sells:  # Open position
                remaining = buys - sells
                avg_buy_price = (group[group['action'] == 'BUY']['amount'] * 
                                group[group['action'] == 'BUY']['price']).sum() / buys
                
                first_buy = group[group['action'] == 'BUY'].iloc[0]
                entry_time = datetime.fromisoformat(first_buy['timestamp'].replace('T', ' ').split('.')[0])
                hours_held = (datetime.now() - entry_time).total_seconds() / 3600
                
                positions[address] = {
                    'amount': remaining,
                    'avg_price': avg_buy_price,
                    'entry_time': entry_time,
                    'hours_held': hours_held
                }
        
        if positions:
            print(f"Found {len(positions)} open positions:\n")
            
            for i, (address, pos) in enumerate(positions.items(), 1):
                print(f"{i}. Token: {address[:12]}...")
                print(f"   Amount: {pos['amount']:.4f} SOL")
                print(f"   Entry Price: ${pos['avg_price']:.8f}")
                print(f"   Time Held: {pos['hours_held']:.1f} hours")
                print(f"   Entry: {pos['entry_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        else:
            print("No open positions")
        
        conn.close()
        
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    monitor_positions()