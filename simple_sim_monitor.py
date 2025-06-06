#!/usr/bin/env python3
"""Simple simulation monitor without errors"""
import sqlite3
import time
import os
from datetime import datetime
from colorama import init, Fore, Style

init()

def monitor_simulation():
    """Monitor only simulation trades"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}SIMULATION MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        conn = sqlite3.connect('data/db/sol_bot.db')
        cursor = conn.cursor()
        
        # Get trade counts
        cursor.execute("SELECT COUNT(*) FROM trades WHERE action='BUY'")
        buys = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
        sells = cursor.fetchone()[0]
        
        # Get balance
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN action='BUY' THEN -amount ELSE amount END) as net_flow
            FROM trades
        """)
        net_flow = cursor.fetchone()[0] or 0
        current_balance = 9.05 + net_flow  # Starting balance + net flow
        
        # Get open positions
        cursor.execute("""
            SELECT COUNT(DISTINCT contract_address) 
            FROM (
                SELECT contract_address, 
                       SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net
                FROM trades
                GROUP BY contract_address
                HAVING net > 0.001
            )
        """)
        open_positions = cursor.fetchone()[0]
        
        # Get completed trades with P&L
        cursor.execute("""
            SELECT 
                COUNT(*) as completed,
                SUM(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                AVG(gain_loss_sol) as avg_pnl,
                SUM(gain_loss_sol) as total_pnl,
                MAX(gain_loss_sol) as best_trade,
                MIN(gain_loss_sol) as worst_trade
            FROM trades 
            WHERE action='SELL' 
            AND gain_loss_sol IS NOT NULL
        """)
        result = cursor.fetchone()
        completed = result[0] or 0
        wins = result[1] or 0
        avg_pnl = result[2] or 0
        total_pnl = result[3] or 0
        best_trade = result[4] or 0
        worst_trade = result[5] or 0
        
        # Display stats
        print(f"{Fore.WHITE}📊 TRADING ACTIVITY{Style.RESET_ALL}")
        print(f"Total Buys:       {Fore.GREEN}{buys}{Style.RESET_ALL}")
        print(f"Total Sells:      {Fore.RED}{sells}{Style.RESET_ALL}")
        print(f"Open Positions:   {Fore.YELLOW}{open_positions}{Style.RESET_ALL}")
        print(f"Current Balance:  {Fore.CYAN}{current_balance:.4f} SOL{Style.RESET_ALL}\n")
        
        print(f"{Fore.WHITE}📈 COMPLETED TRADES{Style.RESET_ALL}")
        print(f"Completed:        {completed}")
        
        if completed > 0:
            win_rate = (wins / completed) * 100
            losses = completed - wins
            
            win_color = Fore.GREEN if win_rate > 60 else Fore.YELLOW if win_rate > 50 else Fore.RED
            print(f"Win Rate:         {win_color}{win_rate:.1f}%{Style.RESET_ALL} ({wins}W / {losses}L)")
            print(f"Total P&L:        {Fore.GREEN if total_pnl > 0 else Fore.RED}{total_pnl:.4f} SOL{Style.RESET_ALL}")
            print(f"Average P&L:      {avg_pnl:.4f} SOL")
            print(f"Best Trade:       {Fore.GREEN}+{best_trade:.4f} SOL{Style.RESET_ALL}")
            print(f"Worst Trade:      {Fore.RED}{worst_trade:.4f} SOL{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No completed trades yet...{Style.RESET_ALL}")
            print(f"Waiting for buy positions to hit take profit or stop loss")
        
        # Recent activity
        cursor.execute("""
            SELECT action, amount, contract_address, timestamp
            FROM trades
            ORDER BY id DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        if recent:
            print(f"\n{Fore.WHITE}🕐 RECENT ACTIVITY{Style.RESET_ALL}")
            for action, amount, contract, timestamp in recent:
                time_str = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp
                action_color = Fore.GREEN if action == 'BUY' else Fore.RED
                print(f"{time_str} {action_color}{action}{Style.RESET_ALL} {amount:.4f} SOL - {contract[:8]}...")
        
        conn.close()
        
        # ML Training readiness
        print(f"\n{Fore.WHITE}🤖 ML TRAINING STATUS{Style.RESET_ALL}")
        if completed < 50:
            print(f"{Fore.YELLOW}Need {50 - completed} more completed trades for ML training{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Ready for ML training! Run: python simple_ml_training.py{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Refreshing in 5 seconds... (Ctrl+C to stop){Style.RESET_ALL}")
        time.sleep(5)

if __name__ == "__main__":
    try:
        print(f"{Fore.CYAN}Starting Simple Simulation Monitor...{Style.RESET_ALL}\n")
        monitor_simulation()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Monitor stopped by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
