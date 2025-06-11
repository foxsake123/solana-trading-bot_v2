#!/usr/bin/env python3
"""
Comprehensive performance monitor for Citadel-Barra strategy
"""
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import time
import os

init()

class CitadelPerformanceMonitor:
    def __init__(self):
        self.db_path = 'data/db/sol_bot.db'
        self.start_time = datetime.now()
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def get_performance_metrics(self):
        """Get comprehensive performance metrics"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get trades from the last 24 hours (or since bot restart)
            recent_trades_query = """
            SELECT 
                id, timestamp, action, amount, contract_address,
                gain_loss_sol, percentage_change, price_multiple
            FROM trades
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
            """
            
            recent_trades = pd.read_sql_query(recent_trades_query, conn)
            
            # Get all-time statistics
            all_time_query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN action='BUY' THEN 1 ELSE 0 END) as total_buys,
                SUM(CASE WHEN action='SELL' THEN 1 ELSE 0 END) as total_sells,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol < 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl,
                AVG(CASE WHEN action='BUY' THEN amount END) as avg_position_size,
                MAX(CASE WHEN action='BUY' THEN amount END) as max_position_size,
                AVG(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN percentage_change END) as avg_win_pct,
                MAX(CASE WHEN action='SELL' THEN percentage_change END) as best_trade_pct,
                COUNT(DISTINCT contract_address) as unique_tokens
            FROM trades
            """
            
            all_time_stats = pd.read_sql_query(all_time_query, conn).iloc[0]
            
            # Get position size trends (to verify Citadel fix)
            position_trend_query = """
            SELECT 
                DATE(timestamp) as date,
                AVG(amount) as avg_position,
                COUNT(*) as trade_count
            FROM trades
            WHERE action = 'BUY'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
            """
            
            position_trends = pd.read_sql_query(position_trend_query, conn)
            
            conn.close()
            
            return {
                'recent_trades': recent_trades,
                'all_time': all_time_stats,
                'position_trends': position_trends
            }
            
        except Exception as e:
            conn.close()
            return None
    
    def calculate_sharpe_ratio(self, trades_df):
        """Calculate Sharpe ratio from trades"""
        if trades_df.empty or 'gain_loss_sol' not in trades_df.columns:
            return 0
        
        # Get daily returns
        daily_returns = trades_df[trades_df['action'] == 'SELL'].groupby(
            pd.to_datetime(trades_df['timestamp']).dt.date
        )['gain_loss_sol'].sum()
        
        if len(daily_returns) < 2:
            return 0
        
        # Calculate Sharpe (annualized for crypto - 365 days)
        avg_return = daily_returns.mean()
        std_return = daily_returns.std()
        
        if std_return == 0:
            return 0
        
        return (avg_return / std_return) * np.sqrt(365)
    
    def display_dashboard(self):
        """Display comprehensive performance dashboard"""
        self.clear_screen()
        
        # Header
        print(f"{Back.BLUE}{Fore.WHITE}{'='*100}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'CITADEL-BARRA STRATEGY PERFORMANCE MONITOR'.center(100)}{Style.RESET_ALL}")
        print(f"{Back.BLUE}{Fore.WHITE}{'='*100}{Style.RESET_ALL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Runtime: {str(datetime.now() - self.start_time).split('.')[0]}")
        
        # Get metrics
        metrics = self.get_performance_metrics()
        
        if not metrics:
            print(f"\n{Fore.RED}No data available{Style.RESET_ALL}")
            return
        
        all_time = metrics['all_time']
        recent_trades = metrics['recent_trades']
        position_trends = metrics['position_trends']
        
        # Strategy Status
        print(f"\n{Fore.CYAN}📊 STRATEGY STATUS{Style.RESET_ALL}")
        try:
            with open('config/trading_params.json', 'r') as f:
                config = json.load(f)
            
            citadel_active = config.get('use_citadel_strategy', False)
            status_color = Fore.GREEN if citadel_active else Fore.RED
            print(f"Citadel-Barra: {status_color}{'ACTIVE' if citadel_active else 'INACTIVE'}{Style.RESET_ALL}")
            
            if citadel_active:
                print(f"Alpha Decay: {config.get('alpha_decay_halflife_hours', 24)}h | "
                      f"Kelly Factor: {config.get('kelly_safety_factor', 0.25):.0%} | "
                      f"Max Position: {config.get('max_position_size_pct', 5)}%")
        except:
            pass
        
        # Overall Performance
        print(f"\n{Fore.CYAN}💰 OVERALL PERFORMANCE{Style.RESET_ALL}")
        
        total_trades = all_time['total_trades'] or 0
        total_sells = all_time['total_sells'] or 0
        wins = all_time['wins'] or 0
        losses = all_time['losses'] or 0
        
        if total_sells > 0:
            win_rate = (wins / total_sells) * 100
            win_color = Fore.GREEN if win_rate > 70 else Fore.YELLOW if win_rate > 50 else Fore.RED
        else:
            win_rate = 0
            win_color = Fore.WHITE
        
        print(f"Total Trades: {total_trades} ({all_time['total_buys']} buys, {total_sells} sells)")
        print(f"Win Rate: {win_color}{win_rate:.1f}%{Style.RESET_ALL} ({wins}W / {losses}L)")
        
        total_pnl = all_time['total_pnl'] or 0
        pnl_color = Fore.GREEN if total_pnl > 0 else Fore.RED
        print(f"Total P&L: {pnl_color}{total_pnl:.4f} SOL{Style.RESET_ALL}")
        
        if all_time['avg_win_pct']:
            print(f"Avg Win: {all_time['avg_win_pct']:.1f}% | Best: {all_time['best_trade_pct']:.1f}%")
        
        # Position Sizing Analysis (Key for Citadel Success)
        print(f"\n{Fore.CYAN}📏 POSITION SIZING ANALYSIS{Style.RESET_ALL}")
        
        avg_position = all_time['avg_position_size'] or 0
        max_position = all_time['max_position_size'] or 0
        
        print(f"Average Position: {avg_position:.4f} SOL")
        print(f"Max Position: {max_position:.4f} SOL")
        
        # Check if Citadel fix is working
        if avg_position >= 0.4:
            print(f"{Fore.GREEN}✓ Citadel position sizing ACTIVE (0.4+ SOL){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Old position sizing detected (<0.4 SOL){Style.RESET_ALL}")
        
        # Position Size Trend
        if not position_trends.empty:
            print(f"\nPosition Size Trend (Daily Avg):")
            for _, row in position_trends.head(3).iterrows():
                date_str = row['date']
                avg_pos = row['avg_position']
                count = row['trade_count']
                trend_color = Fore.GREEN if avg_pos >= 0.4 else Fore.YELLOW
                print(f"  {date_str}: {trend_color}{avg_pos:.4f} SOL{Style.RESET_ALL} ({count} trades)")
        
        # Risk Metrics
        print(f"\n{Fore.CYAN}⚖️ RISK METRICS{Style.RESET_ALL}")
        
        if not recent_trades.empty:
            sharpe = self.calculate_sharpe_ratio(recent_trades)
            sharpe_color = Fore.GREEN if sharpe > 2 else Fore.YELLOW if sharpe > 1 else Fore.RED
            print(f"Sharpe Ratio: {sharpe_color}{sharpe:.2f}{Style.RESET_ALL}")
        
        # Calculate max drawdown
        if total_pnl != 0:
            # Simple drawdown calculation
            cumulative_pnl = recent_trades[recent_trades['action'] == 'SELL']['gain_loss_sol'].cumsum()
            if len(cumulative_pnl) > 0:
                running_max = cumulative_pnl.expanding().max()
                drawdown = (cumulative_pnl - running_max).min()
                print(f"Max Drawdown: {Fore.RED}{drawdown:.4f} SOL{Style.RESET_ALL}")
        
        # Recent Activity
        print(f"\n{Fore.CYAN}📈 RECENT ACTIVITY (24h){Style.RESET_ALL}")
        
        if not recent_trades.empty:
            recent_buys = len(recent_trades[recent_trades['action'] == 'BUY'])
            recent_sells = len(recent_trades[recent_trades['action'] == 'SELL'])
            recent_pnl = recent_trades[recent_trades['action'] == 'SELL']['gain_loss_sol'].sum()
            
            print(f"Trades: {len(recent_trades)} ({recent_buys} buys, {recent_sells} sells)")
            if recent_pnl != 0:
                pnl_color = Fore.GREEN if recent_pnl > 0 else Fore.RED
                print(f"24h P&L: {pnl_color}{recent_pnl:.4f} SOL{Style.RESET_ALL}")
            
            # Show last 5 trades
            print(f"\nLast 5 Trades:")
            for _, trade in recent_trades.head(5).iterrows():
                time_str = trade['timestamp'].split('T')[1][:8] if 'T' in trade['timestamp'] else trade['timestamp'][-8:]
                action = trade['action']
                amount = trade['amount']
                address = trade['contract_address'][:8] + "..."
                
                action_color = Fore.GREEN if action == 'BUY' else Fore.MAGENTA
                print(f"  {time_str} | {action_color}{action:4}{Style.RESET_ALL} | {amount:.4f} SOL | {address}", end='')
                
                if action == 'SELL' and trade['gain_loss_sol'] is not None:
                    pnl = trade['gain_loss_sol']
                    pct = trade['percentage_change']
                    pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
                    print(f" | {pnl_color}{pnl:+.4f} SOL ({pct:+.1f}%){Style.RESET_ALL}")
                else:
                    print()
        
        # Citadel-Specific Metrics
        print(f"\n{Fore.CYAN}🏛️ CITADEL STRATEGY METRICS{Style.RESET_ALL}")
        
        # Factor performance would go here once we have more data
        print("Factor Attribution: Coming soon with more trades...")
        print("Signal Performance: Momentum (40%) | Volume (25%) | Mean Rev (15%) | ML (20%)")
        
        # Footer
        print(f"\n{Fore.YELLOW}Refreshing every 10 seconds... Press Ctrl+C to exit{Style.RESET_ALL}")
    
    def run(self):
        """Run the monitor continuously"""
        print("Starting Citadel-Barra Performance Monitor...")
        time.sleep(2)
        
        while True:
            try:
                self.display_dashboard()
                time.sleep(10)  # Refresh every 10 seconds
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(10)

if __name__ == "__main__":
    monitor = CitadelPerformanceMonitor()
    monitor.run()