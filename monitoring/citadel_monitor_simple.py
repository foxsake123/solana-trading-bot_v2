#!/usr/bin/env python3
"""
Monitor for Citadel-Barra strategy performance (No matplotlib required)
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from colorama import init, Fore, Style

init()

class CitadelStrategyMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
    
    def analyze_factor_performance(self):
        """Analyze performance attribution by factors"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # First, let's check what columns exist in the trades table
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\n{Fore.CYAN}FACTOR PERFORMANCE ANALYSIS{Style.RESET_ALL}")
            print("="*50)
            
            # For now, analyze based on available data
            # Check if we have gain_loss_sol column
            if 'gain_loss_sol' in columns:
                # Get trade performance data
                query = """
                SELECT 
                    contract_address,
                    action,
                    amount,
                    price,
                    timestamp,
                    gain_loss_sol,
                    percentage_change
                FROM trades 
                WHERE action = 'SELL' AND gain_loss_sol IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 50
                """
                
                df = pd.read_sql_query(query, conn)
                
                if not df.empty:
                    print(f"\nRecent Sell Performance:")
                    print(f"Total trades analyzed: {len(df)}")
                    print(f"Average P&L: {df['gain_loss_sol'].mean():.4f} SOL")
                    print(f"Win rate: {(df['gain_loss_sol'] > 0).sum() / len(df) * 100:.1f}%")
                    
                    # Group by time of day
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['hour'] = df['timestamp'].dt.hour
                    
                    hourly_perf = df.groupby('hour')['gain_loss_sol'].agg(['mean', 'count'])
                    
                    print(f"\nPerformance by Hour (UTC):")
                    for hour, row in hourly_perf.iterrows():
                        if row['count'] > 0:
                            color = Fore.GREEN if row['mean'] > 0 else Fore.RED
                            print(f"  Hour {hour:02d}: {color}{row['mean']:.4f} SOL{Style.RESET_ALL} (n={row['count']})")
                else:
                    print("No completed trades with P&L data found yet")
            else:
                print("Trades table doesn't have factor data yet (this is normal for new setups)")
                print("Factor analysis will be available after running with Citadel strategy")
                
        except Exception as e:
            print(f"{Fore.YELLOW}Note: {e}{Style.RESET_ALL}")
        finally:
            conn.close()
    
    def calculate_sharpe_ratio(self):
        """Calculate Sharpe ratio and other risk metrics"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get daily returns
            query = """
            SELECT 
                DATE(timestamp) as date,
                SUM(gain_loss_sol) as daily_pnl
            FROM trades
            WHERE action = 'SELL' AND gain_loss_sol IS NOT NULL
            GROUP BY DATE(timestamp)
            ORDER BY date
            """
            
            df = pd.read_sql_query(query, conn)
            
            print(f"\n{Fore.CYAN}RISK-ADJUSTED PERFORMANCE{Style.RESET_ALL}")
            print("="*50)
            
            if len(df) < 2:
                print(f"{Fore.YELLOW}Insufficient data for Sharpe ratio calculation{Style.RESET_ALL}")
                print("Need at least 2 days of trading data")
                return
            
            # Calculate metrics
            daily_returns = df['daily_pnl'].values
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            
            # Annualized Sharpe (crypto trades 24/7)
            sharpe = (avg_return / std_return) * np.sqrt(365) if std_return > 0 else 0
            
            # Max drawdown
            cumulative = np.cumsum(daily_returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / (running_max + 0.0001)  # Avoid division by zero
            max_drawdown = np.min(drawdown)
            
            print(f"Sharpe Ratio: {Fore.GREEN if sharpe > 1 else Fore.YELLOW}{sharpe:.2f}{Style.RESET_ALL}")
            print(f"Max Drawdown: {Fore.RED}{max_drawdown:.1%}{Style.RESET_ALL}")
            print(f"Daily Avg Return: {avg_return:.4f} SOL")
            print(f"Daily Volatility: {std_return:.4f} SOL")
            print(f"Trading Days: {len(df)}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}Note: {e}{Style.RESET_ALL}")
        finally:
            conn.close()
    
    def show_alpha_decay(self):
        """Visualize alpha decay over time"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get positions with holding time
            query = """
            SELECT 
                contract_address,
                MIN(timestamp) as entry_time,
                MAX(timestamp) as exit_time,
                COUNT(*) as trade_count,
                SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl
            FROM trades
            GROUP BY contract_address
            HAVING trade_count > 1
            """
            
            df = pd.read_sql_query(query, conn)
            
            print(f"\n{Fore.CYAN}ALPHA DECAY ANALYSIS{Style.RESET_ALL}")
            print("="*50)
            
            if df.empty:
                print("No completed round-trip trades yet")
                return
            
            # Calculate holding periods
            df['entry_time'] = pd.to_datetime(df['entry_time'])
            df['exit_time'] = pd.to_datetime(df['exit_time'])
            df['holding_hours'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
            
            # Group by holding period buckets
            buckets = [0, 6, 12, 24, 48, 168]  # hours
            labels = ['0-6h', '6-12h', '12-24h', '24-48h', '48h+']
            
            df['holding_bucket'] = pd.cut(df['holding_hours'], bins=buckets, labels=labels)
            
            perf_by_holding = df.groupby('holding_bucket')['total_pnl'].agg(['mean', 'count'])
            
            print("\nP&L by Holding Period:")
            for bucket, row in perf_by_holding.iterrows():
                if row['count'] > 0:
                    color = Fore.GREEN if row['mean'] > 0 else Fore.RED
                    print(f"{bucket}: {color}{row['mean']:.4f} SOL{Style.RESET_ALL} (n={row['count']})")
            
            # Show average holding time
            avg_holding = df['holding_hours'].mean()
            print(f"\nAverage Holding Time: {avg_holding:.1f} hours")
            
            # Show best and worst holding periods
            if len(df) > 0:
                best_trade = df.loc[df['total_pnl'].idxmax()]
                worst_trade = df.loc[df['total_pnl'].idxmin()]
                
                print(f"\nBest Trade:")
                print(f"  Token: {best_trade['contract_address'][:12]}...")
                print(f"  P&L: {Fore.GREEN}{best_trade['total_pnl']:.4f} SOL{Style.RESET_ALL}")
                print(f"  Holding: {best_trade['holding_hours']:.1f} hours")
                
                print(f"\nWorst Trade:")
                print(f"  Token: {worst_trade['contract_address'][:12]}...")
                print(f"  P&L: {Fore.RED}{worst_trade['total_pnl']:.4f} SOL{Style.RESET_ALL}")
                print(f"  Holding: {worst_trade['holding_hours']:.1f} hours")
                
        except Exception as e:
            print(f"{Fore.YELLOW}Note: {e}{Style.RESET_ALL}")
        finally:
            conn.close()
    
    def show_current_status(self):
        """Show current bot status and configuration"""
        print(f"\n{Fore.CYAN}CURRENT BOT STATUS{Style.RESET_ALL}")
        print("="*50)
        
        # Check if Citadel strategy is enabled
        try:
            import json
            with open('config/trading_params.json', 'r') as f:
                config = json.load(f)
            
            citadel_enabled = config.get('use_citadel_strategy', False)
            
            if citadel_enabled:
                print(f"Strategy: {Fore.GREEN}Citadel-Barra ENABLED{Style.RESET_ALL}")
                print(f"\nSignal Weights:")
                weights = config.get('signal_weights', {})
                for signal, weight in weights.items():
                    print(f"  {signal}: {weight:.1%}")
                
                print(f"\nRisk Parameters:")
                print(f"  Max Factor Exposure: {config.get('max_factor_exposure', 2.0)}")
                print(f"  Target Idiosyncratic Ratio: {config.get('target_idiosyncratic_ratio', 0.6):.0%}")
                print(f"  Alpha Decay Half-life: {config.get('alpha_decay_halflife_hours', 24)} hours")
            else:
                print(f"Strategy: {Fore.YELLOW}Standard Mode (Citadel-Barra DISABLED){Style.RESET_ALL}")
                print("\nTo enable Citadel strategy, set 'use_citadel_strategy': true in config/trading_params.json")
                
        except Exception as e:
            print(f"Could not read configuration: {e}")
    
    def run(self):
        """Run all analyses"""
        print(f"{Fore.CYAN}CITADEL-BARRA STRATEGY MONITOR{Style.RESET_ALL}")
        print("="*60)
        
        self.show_current_status()
        self.analyze_factor_performance()
        self.calculate_sharpe_ratio()
        self.show_alpha_decay()
        
        print(f"\n{Fore.YELLOW}Note: Full factor analysis will be available after trades are executed with Citadel strategy enabled{Style.RESET_ALL}")

if __name__ == "__main__":
    monitor = CitadelStrategyMonitor()
    monitor.run()