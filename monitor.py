#!/usr/bin/env python3
"""
Simple monitor for Solana Trading Bot v2
Displays trades, positions, and performance metrics
"""
import os
import time
import json
import sqlite3
from datetime import datetime, timedelta
from tabulate import tabulate
import colorama
from colorama import Fore, Back, Style

colorama.init()

class BotMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.config_path = 'config/bot_control.json'
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def get_current_positions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First, let's check what columns actually exist
        cursor.execute("PRAGMA table_info(positions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build query based on available columns
        if 'contract_address' in columns:
            address_col = 'contract_address'
        elif 'token_mint' in columns:
            address_col = 'token_mint'
        else:
            address_col = 'id'  # fallback
            
        query = f"""
        SELECT 
            {address_col},
            ticker,
            amount,
            entry_price,
            current_price,
            stop_loss,
            take_profit,
            CASE 
                WHEN current_price > 0 AND entry_price > 0 
                THEN ((current_price - entry_price) / entry_price * 100)
                ELSE 0
            END as pnl_percent,
            created_at
        FROM positions
        WHERE status = 'active'
        ORDER BY created_at DESC
        """
        
        try:
            cursor.execute(query)
            positions = cursor.fetchall()
        except:
            positions = []
            
        conn.close()
        return positions
        
    def get_recent_trades(self, hours=24):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check available columns
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build query based on available columns
        select_fields = []
        if 'ticker' in columns:
            select_fields.append('ticker')
        elif 'symbol' in columns:
            select_fields.append('symbol')
        else:
            select_fields.append("'Unknown' as ticker")
            
        query = f"""
        SELECT 
            {select_fields[0]},
            type as side,
            amount,
            price,
            total_cost as total,
            gain_loss_sol as profit_loss,
            percentage_change as profit_loss_pct,
            status,
            created_at
        FROM trades
        WHERE created_at > datetime('now', '-{hours} hours')
        ORDER BY created_at DESC
        LIMIT 20
        """
        
        try:
            cursor.execute(query)
            trades = cursor.fetchall()
        except Exception as e:
            print(f"Trade query error: {e}")
            trades = []
            
        conn.close()
        return trades
        
    def get_performance_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN gain_loss_sol < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(gain_loss_sol) as total_pnl,
                    AVG(percentage_change) as avg_pnl_pct
                FROM trades
                WHERE type = 'sell' AND status = 'completed'
            """)
            stats = cursor.fetchone()
        except:
            stats = None
            
        conn.close()
        return stats
        
    def display_monitor(self):
        while True:
            try:
                self.clear_screen()
                config = self.get_config()
                
                # Header
                print(Fore.CYAN + "="*80)
                print(" " * 20 + "SOLANA TRADING BOT MONITOR" + " " * 20)
                print("="*80 + Style.RESET_ALL)
                
                # Bot Status
                mode = "SIMULATION" if config.get('simulation_mode', True) else "REAL"
                running = "RUNNING" if config.get('running', False) else "STOPPED"
                
                status_color = Fore.GREEN if running == "RUNNING" else Fore.RED
                mode_color = Fore.YELLOW if mode == "SIMULATION" else Fore.RED
                
                print(f"\nBot Status: {status_color}{running}{Style.RESET_ALL} | Mode: {mode_color}{mode}{Style.RESET_ALL}")
                print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wallet Balance (from config)
                if mode == "SIMULATION":
                    balance = config.get('starting_simulation_balance', 10.0)
                    print(f"Balance: {balance:.4f} SOL (Simulation)")
                else:
                    real_balance = config.get('real_wallet_starting_balance', 0.0)
                    print(f"Starting Balance: {real_balance:.4f} SOL")
                
                # Current Positions
                print(f"\n{Fore.YELLOW}[CURRENT POSITIONS]{Style.RESET_ALL}")
                print("-" * 80)
                
                positions = self.get_current_positions()
                if positions:
                    headers = ["Symbol", "Amount", "Entry", "Current", "P&L %", "Stop Loss", "Take Profit", "Age"]
                    table_data = []
                    
                    for pos in positions:
                        symbol = pos[1][:8] if pos[1] else "Unknown"
                        amount = f"{pos[2]:.4f}" if pos[2] else "0"
                        entry = f"${pos[3]:.6f}" if pos[3] else "$0"
                        current = f"${pos[4]:.6f}" if pos[4] else "$0"
                        pnl = pos[7] if pos[7] else 0
                        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
                        pnl_str = f"{pnl_color}{pnl:+.2f}%{Style.RESET_ALL}"
                        sl = f"${pos[5]:.6f}" if pos[5] else "N/A"
                        tp = f"${pos[6]:.6f}" if pos[6] else "N/A"
                        
                        # Calculate age
                        try:
                            created = datetime.fromisoformat(pos[8])
                            age = datetime.now() - created
                            age_str = f"{int(age.total_seconds() / 60)}m"
                        except:
                            age_str = "N/A"
                        
                        table_data.append([symbol, amount, entry, current, pnl_str, sl, tp, age_str])
                    
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print("No open positions")
                
                # Recent Trades
                print(f"\n{Fore.YELLOW}[RECENT TRADES (Last 24h)]{Style.RESET_ALL}")
                print("-" * 80)
                
                trades = self.get_recent_trades()
                if trades:
                    headers = ["Time", "Symbol", "Side", "Amount", "Price", "Total", "P&L", "Status"]
                    table_data = []
                    
                    for trade in trades:
                        try:
                            time_str = datetime.fromisoformat(trade[8]).strftime("%H:%M:%S")
                        except:
                            time_str = "N/A"
                            
                        symbol = trade[0][:8] if trade[0] else "Unknown"
                        side_color = Fore.GREEN if trade[1] == "buy" else Fore.RED
                        side = f"{side_color}{trade[1].upper()}{Style.RESET_ALL}"
                        amount = f"{trade[2]:.4f}" if trade[2] else "0"
                        price = f"${trade[3]:.6f}" if trade[3] else "$0"
                        total = f"{trade[4]:.4f} SOL" if trade[4] else "0 SOL"
                        
                        if trade[5] and trade[1] == "sell":
                            pnl_color = Fore.GREEN if trade[5] > 0 else Fore.RED
                            pnl = f"{pnl_color}{trade[5]:+.4f} SOL{Style.RESET_ALL}"
                        else:
                            pnl = "-"
                            
                        status_color = Fore.GREEN if trade[7] == "completed" else Fore.YELLOW
                        status = f"{status_color}{trade[7]}{Style.RESET_ALL}"
                        
                        table_data.append([time_str, symbol, side, amount, price, total, pnl, status])
                    
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print("No recent trades")
                
                # Performance Stats
                print(f"\n{Fore.YELLOW}[PERFORMANCE STATISTICS]{Style.RESET_ALL}")
                print("-" * 80)
                
                stats = self.get_performance_stats()
                if stats and stats[0]:
                    total_trades = stats[0] or 0
                    winning = stats[1] or 0
                    losing = stats[2] or 0
                    total_pnl = stats[3] or 0
                    avg_pnl_pct = stats[4] or 0
                    
                    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
                    
                    pnl_color = Fore.GREEN if total_pnl > 0 else Fore.RED
                    
                    print(f"Total Trades: {total_trades} | Wins: {Fore.GREEN}{winning}{Style.RESET_ALL} | Losses: {Fore.RED}{losing}{Style.RESET_ALL}")
                    print(f"Win Rate: {win_rate:.1f}% | Avg P&L: {avg_pnl_pct:+.2f}%")
                    print(f"Total P&L: {pnl_color}{total_pnl:+.4f} SOL{Style.RESET_ALL}")
                else:
                    print("No completed trades yet")
                
                # Configuration Info
                print(f"\n{Fore.YELLOW}[CONFIGURATION]{Style.RESET_ALL}")
                print("-" * 80)
                print(f"Take Profit: {config.get('take_profit_target', 0)*100:.0f}% | Stop Loss: {config.get('stop_loss_percentage', 0)*100:.0f}%")
                print(f"Max Investment: {config.get('max_investment_per_token', 0)} SOL | Max Positions: {config.get('max_open_positions', 0)}")
                print(f"Slippage: {config.get('slippage_tolerance', 0)*100:.0f}% | Min Volume: ${config.get('MIN_VOLUME', 0):,.0f}")
                
                print(f"\n{Fore.CYAN}Press Ctrl+C to exit | Refreshing every 5 seconds...{Style.RESET_ALL}")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = BotMonitor()
    monitor.display_monitor()
