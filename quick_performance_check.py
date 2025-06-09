#!/usr/bin/env python3
"""
Quick performance check for Citadel-Barra strategy
"""

import sqlite3
import json
from datetime import datetime, timedelta
from colorama import init, Fore, Style

init()

def quick_performance_check():
    """Quick check of bot performance with Citadel strategy"""
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🏛️  CITADEL-BARRA PERFORMANCE CHECK{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # 1. Check if strategy is enabled
    try:
        with open('config/trading_params.json', 'r') as f:
            config = json.load(f)
        
        citadel_enabled = config.get('use_citadel_strategy', False)
        print(f"\n📊 Strategy Status: ", end="")
        if citadel_enabled:
            print(f"{Fore.GREEN}CITADEL-BARRA ACTIVE{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}STANDARD MODE (Citadel Disabled){Style.RESET_ALL}")
    except:
        print(f"{Fore.RED}Could not read config{Style.RESET_ALL}")
    
    # 2. Connect to database
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        
        # 3. Check recent trades
        print(f"\n📈 RECENT PERFORMANCE (Last 24h):")
        print("-" * 40)
        
        # Get trades from last 24 hours
        query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN action='BUY' THEN 1 ELSE 0 END) as buys,
            SUM(CASE WHEN action='SELL' THEN 1 ELSE 0 END) as sells,
            AVG(CASE WHEN action='BUY' THEN amount END) as avg_buy_size,
            MAX(CASE WHEN action='BUY' THEN amount END) as max_buy_size,
            MIN(CASE WHEN action='BUY' THEN amount END) as min_buy_size
        FROM trades
        WHERE timestamp > datetime('now', '-24 hours')
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            total, buys, sells, avg_size, max_size, min_size = row
            print(f"Total Trades: {total} ({buys} buys, {sells} sells)")
            
            if avg_size:
                print(f"Position Sizes:")
                print(f"  Average: {avg_size:.4f} SOL")
                print(f"  Range: {min_size:.4f} - {max_size:.4f} SOL")
                
                # Check if positions are proper size
                if avg_size >= 0.4:
                    print(f"  Status: {Fore.GREEN}✅ Proper sizing!{Style.RESET_ALL}")
                else:
                    print(f"  Status: {Fore.RED}❌ Too small!{Style.RESET_ALL}")
        
        # 4. Check P&L
        print(f"\n💰 PROFIT/LOSS ANALYSIS:")
        print("-" * 40)
        
        pnl_query = """
        SELECT 
            COUNT(*) as completed_trades,
            SUM(gain_loss_sol) as total_pnl,
            AVG(gain_loss_sol) as avg_pnl,
            MAX(gain_loss_sol) as best_trade,
            MIN(gain_loss_sol) as worst_trade,
            SUM(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
            AVG(percentage_change) as avg_pct_change
        FROM trades
        WHERE action='SELL' 
        AND gain_loss_sol IS NOT NULL
        AND timestamp > datetime('now', '-24 hours')
        """
        
        cursor.execute(pnl_query)
        pnl = cursor.fetchone()
        
        if pnl and pnl[0] > 0:  # If there are completed trades
            completed, total_pnl, avg_pnl, best, worst, wins, avg_pct = pnl
            win_rate = (wins / completed * 100) if completed > 0 else 0
            
            print(f"Completed Trades: {completed}")
            print(f"Win Rate: {Fore.GREEN if win_rate > 70 else Fore.YELLOW}{win_rate:.1f}%{Style.RESET_ALL}")
            print(f"Total P&L: {Fore.GREEN if total_pnl > 0 else Fore.RED}{total_pnl:.4f} SOL{Style.RESET_ALL}")
            print(f"Average P&L: {avg_pnl:.4f} SOL ({avg_pct:.1f}%)")
            print(f"Best Trade: {Fore.GREEN}+{best:.4f} SOL{Style.RESET_ALL}")
            print(f"Worst Trade: {Fore.RED}{worst:.4f} SOL{Style.RESET_ALL}")
        else:
            print("No completed trades in last 24h")
        
        # 5. Current Balance Estimate
        print(f"\n🏦 BALANCE ESTIMATE:")
        print("-" * 40)
        
        balance_query = """
        SELECT 
            10.0 - SUM(CASE WHEN action='BUY' THEN amount ELSE 0 END) 
            + SUM(CASE WHEN action='SELL' THEN amount ELSE 0 END) as estimated_balance
        FROM trades
        """
        
        cursor.execute(balance_query)
        balance = cursor.fetchone()[0] or 10.0
        
        print(f"Estimated Balance: {balance:.4f} SOL")
        print(f"Starting Balance: 10.0000 SOL")
        print(f"Net Change: {Fore.GREEN if balance > 10 else Fore.RED}{balance - 10:+.4f} SOL{Style.RESET_ALL}")
        
        # 6. Factor Analysis Preview
        print(f"\n🔬 FACTOR INSIGHTS:")
        print("-" * 40)
        
        # Check recent buy reasons (simplified)
        recent_buys_query = """
        SELECT contract_address, amount, timestamp
        FROM trades
        WHERE action='BUY'
        ORDER BY timestamp DESC
        LIMIT 5
        """
        
        cursor.execute(recent_buys_query)
        recent_buys = cursor.fetchall()
        
        if recent_buys:
            print("Recent Buy Decisions:")
            for address, amount, timestamp in recent_buys:
                time_str = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp
                print(f"  {time_str}: {amount:.4f} SOL - {address[:12]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"{Fore.RED}Database error: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 For detailed analysis, run:{Style.RESET_ALL}")
    print("  python citadel_monitor_simple.py")
    print("  python monitoring/enhanced_monitor.py")

if __name__ == "__main__":
    quick_performance_check()