#!/usr/bin/env python3
"""
Live monitoring for Citadel-Barra strategy performance
"""
import time
import os
import json
import sqlite3
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import asyncio

init()

class CitadelLiveMonitor:
    def __init__(self):
        self.db_path = 'data/db/sol_bot.db'
        self.last_trade_id = 0
        self.start_time = datetime.now()
        self.initial_balance = 10.0
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_latest_trades(self, limit=10):
        """Get most recent trades"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, action, amount, contract_address, 
                       gain_loss_sol, percentage_change
                FROM trades
                WHERE id > ?
                ORDER BY id DESC
                LIMIT ?
            """, (self.last_trade_id, limit))
            
            trades = cursor.fetchall()
            if trades:
                self.last_trade_id = max(t[0] for t in trades)
            
            conn.close()
            return trades
            
        except Exception as e:
            return []
    
    def calculate_metrics(self):
        """Calculate current performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session stats (since monitor started)
            session_start = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN action='BUY' THEN 1 ELSE 0 END) as buys,
                    SUM(CASE WHEN action='SELL' THEN 1 ELSE 0 END) as sells,
                    AVG(CASE WHEN action='BUY' THEN amount END) as avg_position,
                    MAX(CASE WHEN action='BUY' THEN amount END) as max_position,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as session_pnl
                FROM trades
                WHERE timestamp > ?
            """, (session_start,))
            
            session_stats = cursor.fetchone()
            
            # Get all-time stats
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN action='BUY' THEN -amount 
                             WHEN action='SELL' THEN amount 
                             ELSE 0 END) as net_flow,
                    COUNT(DISTINCT contract_address) as unique_tokens,
                    AVG(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN percentage_change END) as avg_win_pct,
                    MAX(CASE WHEN action='SELL' THEN percentage_change END) as best_trade_pct
                FROM trades
            """)
            
            all_time_stats = cursor.fetchone()
            
            conn.close()
            
            # Calculate current balance
            current_balance = self.initial_balance + (all_time_stats[0] or 0)
            
            return {
                'session': session_stats,
                'all_time': all_time_stats,
                'current_balance': current_balance
            }
            
        except Exception as e:
            return None
    
    def display_monitor(self):
        """Display live monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'CITADEL-BARRA LIVE MONITOR'.center(80)}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"Runtime: {str(datetime.now() - self.start_time).split('.')[0]}")
        print()
        
        # Get metrics
        metrics = self.calculate_metrics()
        
        if metrics:
            # Balance section
            balance = metrics['current_balance']
            pnl = balance - self.initial_balance
            pnl_pct = (pnl / self.initial_balance) * 100
            
            print(f"{Fore.CYAN}💰 BALANCE{Style.RESET_ALL}")
            balance_color = Fore.GREEN if pnl >= 0 else Fore.RED
            print(f"Current: {balance:.4f} SOL | "
                  f"P&L: {balance_color}{pnl:+.4f} SOL ({pnl_pct:+.1f}%){Style.RESET_ALL}")
            print()
            
            # Session stats
            session = metrics['session']
            if session[0] > 0:  # If there are session trades
                print(f"{Fore.CYAN}📊 SESSION STATS{Style.RESET_ALL}")
                print(f"Trades: {session[0]} ({session[1]} buys, {session[2]} sells)")
                
                if session[3]:  # avg_position
                    pos_color = Fore.GREEN if session[3] >= 0.4 else Fore.YELLOW
                    print(f"Avg Position: {pos_color}{session[3]:.4f} SOL{Style.RESET_ALL}")
                    print(f"Max Position: {session[4]:.4f} SOL")
                
                if session[5]:  # session_pnl
                    pnl_color = Fore.GREEN if session[5] > 0 else Fore.RED
                    print(f"Session P&L: {pnl_color}{session[5]:.4f} SOL{Style.RESET_ALL}")
                print()
            
            # Check Citadel strategy status
            try:
                with open('config/trading_params.json', 'r') as f:
                    config = json.load(f)
                
                if config.get('use_citadel_strategy'):
                    print(f"{Fore.GREEN}✅ Citadel-Barra Strategy ACTIVE{Style.RESET_ALL}")
                    print(f"   Alpha Decay: {config.get('alpha_decay_halflife_hours', 24)}h")
                    print(f"   Min Position: {config.get('absolute_min_sol', 0.1)} SOL")
                else:
                    print(f"{Fore.YELLOW}⚠️  Citadel-Barra Strategy DISABLED{Style.RESET_ALL}")
            except:
                pass
            
            print()
        
        # Recent trades
        recent_trades = self.get_latest_trades()
        if recent_trades:
            print(f"{Fore.CYAN}📈 RECENT TRADES{Style.RESET_ALL}")
            
            for trade in recent_trades[:5]:
                _, timestamp, action, amount, address, gain_loss, pct_change = trade
                
                time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp[-8:]
                action_color = Fore.GREEN if action == 'BUY' else Fore.MAGENTA
                
                print(f"{time_str} | {action_color}{action:4}{Style.RESET_ALL} | "
                      f"{amount:.4f} SOL | {address[:8]}...", end='')
                
                if action == 'SELL' and gain_loss is not None:
                    pnl_color = Fore.GREEN if gain_loss > 0 else Fore.RED
                    print(f" | {pnl_color}{gain_loss:+.4f} SOL ({pct_change:+.1f}%){Style.RESET_ALL}")
                else:
                    print()
        
        # Status line
        print(f"\n{Fore.YELLOW}Refreshing every 5 seconds... Press Ctrl+C to exit{Style.RESET_ALL}")
    
    def run(self):
        """Run the live monitor"""
        print("Starting Citadel-Barra Live Monitor...")
        time.sleep(2)
        
        while True:
            try:
                self.display_monitor()
                time.sleep(5)
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = CitadelLiveMonitor()
    monitor.run()