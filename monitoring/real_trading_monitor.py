#!/usr/bin/env python3
"""
Advanced Real Trading Monitor with ML Data Collection
Optimized for live trading with alerts and safety features
"""

import asyncio
import sqlite3
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from colorama import init, Fore, Style, Back
import logging
from typing import Dict, List, Tuple
import winsound  # For alerts on Windows

init()

class RealTradingMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = None
        self.daily_pnl_limit = -1.0  # Stop at 1 SOL loss
        self.alert_thresholds = {
            'large_loss': -0.5,
            'large_win': 2.0,
            'position_size': 0.5,
            'drawdown': -0.15  # 15% drawdown
        }
        self.performance_history = []
        self.ml_training_data = []
        self.start_time = datetime.now()
        
        # Setup logging for real trading
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring/real_trading.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RealTradingMonitor')
    
    def alert(self, message: str, level: str = 'info'):
        """Send alert with sound and logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if level == 'critical':
            print(f"{Back.RED}{Fore.WHITE}🚨 CRITICAL: {message}{Style.RESET_ALL}")
            self.logger.critical(message)
            # Sound alert (Windows)
            try:
                winsound.Beep(1000, 500)  # 1000Hz for 500ms
            except:
                pass
        elif level == 'warning':
            print(f"{Fore.YELLOW}⚠️  WARNING: {message}{Style.RESET_ALL}")
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    async def get_real_time_data(self) -> Dict:
        """Fetch real-time trading data"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Current positions
            positions_query = """
            SELECT 
                t1.contract_address,
                t1.amount as position_size,
                t1.price as entry_price,
                t1.timestamp as entry_time,
                t2.price_usd as current_price,
                t2.price_usd as current_price_usd,
            FROM trades t1
            LEFT JOIN tokens t2 ON t1.contract_address = t2.contract_address
            WHERE t1.action = 'BUY'
            AND NOT EXISTS (
                SELECT 1 FROM trades t3 
                WHERE t3.contract_address = t1.contract_address 
                AND t3.action = 'SELL' 
                AND t3.timestamp > t1.timestamp
            )
            """
            
            positions_df = pd.read_sql_query(positions_query, conn)
            
            # Recent trades (last hour)
            trades_query = """
            SELECT * FROM trades 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC
            """
            
            trades_df = pd.read_sql_query(trades_query, conn)
            
            # Performance metrics
            metrics_query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol < 0 THEN 1 ELSE 0 END) as losses,
                MAX(gain_loss_sol) as best_trade,
                MIN(gain_loss_sol) as worst_trade,
                AVG(amount) as avg_position_size
            FROM trades
            WHERE timestamp > datetime('now', '-24 hours')
            """
            
            cursor = conn.cursor()
            cursor.execute(metrics_query)
            metrics = cursor.fetchone()
            
            return {
                'positions': positions_df,
                'trades': trades_df,
                'metrics': metrics
            }
            
        finally:
            conn.close()
    
    def calculate_risk_metrics(self, data: Dict) -> Dict:
        """Calculate real-time risk metrics"""
        positions = data['positions']
        
        if positions.empty:
            return {
                'total_exposure': 0,
                'unrealized_pnl': 0,
                'position_count': 0,
                'largest_position': 0,
                'risk_score': 0
            }
        
        # Calculate unrealized P&L
        positions['unrealized_pnl'] = (
            (positions['current_price'] / positions['entry_price'] - 1) * 
            positions['position_size']
        )
        
        total_exposure = positions['position_size'].sum()
        unrealized_pnl = positions['unrealized_pnl'].sum()
        
        # Risk scoring
        risk_score = 0
        if total_exposure > 5.0:  # Over 5 SOL exposure
            risk_score += 30
        if positions['position_size'].max() > 1.0:  # Single position over 1 SOL
            risk_score += 20
        if unrealized_pnl < -0.5:  # Losing more than 0.5 SOL
            risk_score += 25
        if len(positions) > 10:  # Too many positions
            risk_score += 25
            
        return {
            'total_exposure': total_exposure,
            'unrealized_pnl': unrealized_pnl,
            'position_count': len(positions),
            'largest_position': positions['position_size'].max(),
            'risk_score': min(risk_score, 100),
            'positions_at_risk': len(positions[positions['unrealized_pnl'] < -0.1])
        }
    
    def collect_ml_training_data(self, data: Dict):
        """Collect data for ML model training"""
        trades = data['trades']
        
        if not trades.empty:
            # Extract features from recent trades
            for _, trade in trades.iterrows():
                if trade['action'] == 'SELL':
                    # Collect successful trade patterns
                    training_point = {
                        'timestamp': trade['timestamp'],
                        'contract_address': trade['contract_address'],
                        'gain_loss_sol': trade['gain_loss_sol'],
                        'percentage_change': trade['percentage_change'],
                        'hold_time': self.calculate_hold_time(trade),
                        'position_size': trade['amount'],
                        'hour_of_day': pd.to_datetime(trade['timestamp']).hour,
                        'day_of_week': pd.to_datetime(trade['timestamp']).dayofweek
                    }
                    
                    self.ml_training_data.append(training_point)
        
        # Save training data periodically
        if len(self.ml_training_data) >= 50:
            self.save_ml_training_data()
    
    def calculate_hold_time(self, sell_trade) -> float:
        """Calculate holding time for a trade"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Find corresponding buy
            query = """
            SELECT timestamp FROM trades 
            WHERE contract_address = ? 
            AND action = 'BUY' 
            AND timestamp < ?
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            cursor = conn.cursor()
            cursor.execute(query, (sell_trade['contract_address'], sell_trade['timestamp']))
            buy_time = cursor.fetchone()
            
            if buy_time:
                buy_dt = pd.to_datetime(buy_time[0])
                sell_dt = pd.to_datetime(sell_trade['timestamp'])
                return (sell_dt - buy_dt).total_seconds() / 3600  # Hours
            
            return 0
            
        finally:
            conn.close()
    
    def save_ml_training_data(self):
        """Save ML training data to file"""
        if self.ml_training_data:
            df = pd.DataFrame(self.ml_training_data)
            
            # Append to existing file
            file_path = 'data/ml_training_data.csv'
            if os.path.exists(file_path):
                existing_df = pd.read_csv(file_path)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(file_path, index=False)
            self.ml_training_data = []  # Clear buffer
            
            self.logger.info(f"Saved {len(df)} training samples")
    
    async def display_dashboard(self):
        """Display real-time trading dashboard"""
        while True:
            try:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Get real-time data
                data = await self.get_real_time_data()
                risk_metrics = self.calculate_risk_metrics(data)
                
                # Collect ML training data
                self.collect_ml_training_data(data)
                
                # Header
                print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
                print(f"{Back.BLUE}{Fore.WHITE}{'REAL TRADING MONITOR'.center(80)}{Style.RESET_ALL}")
                print(f"{Back.BLUE}{Fore.WHITE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(80)}{Style.RESET_ALL}")
                print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
                
                # Account Summary
                metrics = data['metrics']
                if metrics:
                    total_trades, total_pnl, wins, losses, best, worst, avg_size = metrics
                    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
                    
                    print(f"\n{Fore.CYAN}📊 24H PERFORMANCE{Style.RESET_ALL}")
                    print("─" * 40)
                    
                    pnl_color = Fore.GREEN if total_pnl > 0 else Fore.RED
                    print(f"P&L: {pnl_color}{total_pnl:.4f} SOL{Style.RESET_ALL}")
                    print(f"Win Rate: {win_rate:.1f}% ({wins}W/{losses}L)")
                    print(f"Avg Position: {avg_size:.4f} SOL")
                    
                    # Check for alerts
                    if total_pnl < self.daily_pnl_limit:
                        self.alert(f"Daily loss limit reached: {total_pnl:.4f} SOL", 'critical')
                    
                    if worst and worst < self.alert_thresholds['large_loss']:
                        self.alert(f"Large loss detected: {worst:.4f} SOL", 'warning')
                    
                    if best and best > self.alert_thresholds['large_win']:
                        self.alert(f"Large win: {best:.4f} SOL", 'info')
                
                # Risk Metrics
                print(f"\n{Fore.CYAN}⚡ RISK METRICS{Style.RESET_ALL}")
                print("─" * 40)
                
                risk_color = Fore.GREEN
                if risk_metrics['risk_score'] > 70:
                    risk_color = Fore.RED
                elif risk_metrics['risk_score'] > 40:
                    risk_color = Fore.YELLOW
                
                print(f"Risk Score: {risk_color}{risk_metrics['risk_score']}/100{Style.RESET_ALL}")
                print(f"Total Exposure: {risk_metrics['total_exposure']:.4f} SOL")
                print(f"Open Positions: {risk_metrics['position_count']}")
                print(f"Unrealized P&L: {Fore.GREEN if risk_metrics['unrealized_pnl'] > 0 else Fore.RED}"
                      f"{risk_metrics['unrealized_pnl']:.4f} SOL{Style.RESET_ALL}")
                
                if risk_metrics['positions_at_risk'] > 0:
                    print(f"{Fore.YELLOW}Positions at Risk: {risk_metrics['positions_at_risk']}{Style.RESET_ALL}")
                
                # Current Positions
                if not data['positions'].empty:
                    print(f"\n{Fore.CYAN}📈 OPEN POSITIONS{Style.RESET_ALL}")
                    print("─" * 80)
                    print(f"{'Token':<15} {'Size':<10} {'Entry':<12} {'Current':<12} {'P&L':<12} {'Time':<10}")
                    print("─" * 80)
                    
                    for _, pos in data['positions'].head(10).iterrows():
                        token = pos['contract_address'][:12] + "..."
                        size = f"{pos['position_size']:.4f}"
                        entry = f"${pos['entry_price']:.8f}"
                        current = f"${pos['current_price']:.8f}" if pos['current_price'] else "N/A"
                        
                        pnl = ((pos['current_price'] / pos['entry_price'] - 1) * 100) if pos['current_price'] else 0
                        pnl_color = Fore.GREEN if pnl > 0 else Fore.RED
                        pnl_str = f"{pnl_color}{pnl:+.1f}%{Style.RESET_ALL}"
                        
                        hold_time = (datetime.now() - pd.to_datetime(pos['entry_time'])).total_seconds() / 3600
                        time_str = f"{hold_time:.1f}h"
                        
                        print(f"{token:<15} {size:<10} {entry:<12} {current:<12} {pnl_str:<20} {time_str:<10}")
                
                # Recent Trades
                if not data['trades'].empty:
                    print(f"\n{Fore.CYAN}🔄 RECENT TRADES{Style.RESET_ALL}")
                    print("─" * 80)
                    
                    for _, trade in data['trades'].head(5).iterrows():
                        action_color = Fore.GREEN if trade['action'] == 'BUY' else Fore.RED
                        action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
                        
                        timestamp = pd.to_datetime(trade['timestamp']).strftime('%H:%M:%S')
                        token = trade['contract_address'][:12] + "..."
                        
                        print(f"{timestamp} {action_emoji} {action_color}{trade['action']:<4}{Style.RESET_ALL} "
                              f"{trade['amount']:.4f} SOL | {token}")
                        
                        if trade['action'] == 'SELL' and 'gain_loss_sol' in trade:
                            pnl_color = Fore.GREEN if trade['gain_loss_sol'] > 0 else Fore.RED
                            print(f"         P&L: {pnl_color}{trade['gain_loss_sol']:+.4f} SOL "
                                  f"({trade.get('percentage_change', 0):+.1f}%){Style.RESET_ALL}")
                
                # Status Bar
                uptime = (datetime.now() - self.start_time).total_seconds() / 3600
                print(f"\n{Back.BLACK}{Fore.WHITE}{'─'*80}{Style.RESET_ALL}")
                print(f"Uptime: {uptime:.1f}h | ML Samples: {len(self.ml_training_data)} | "
                      f"Press Ctrl+C to stop")
                
                # Sleep before refresh
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Stopping monitor...{Style.RESET_ALL}")
                self.save_ml_training_data()
                break
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run the real trading monitor"""
        self.logger.info("Starting Real Trading Monitor")
        
        # Check initial balance
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(CASE WHEN action='BUY' THEN -amount ELSE amount END) FROM trades")
        balance_change = cursor.fetchone()[0] or 0
        conn.close()
        
        print(f"{Fore.GREEN}Real Trading Monitor Started{Style.RESET_ALL}")
        print(f"Initial tracking from balance change: {balance_change:.4f} SOL")
        print(f"\n{Fore.YELLOW}Safety Features Active:{Style.RESET_ALL}")
        print(f"- Daily loss limit: {self.daily_pnl_limit} SOL")
        print(f"- Large loss alert: {self.alert_thresholds['large_loss']} SOL")
        print(f"- ML data collection: Enabled")
        print(f"\nStarting dashboard in 3 seconds...")
        
        await asyncio.sleep(3)
        await self.display_dashboard()

def main():
    monitor = RealTradingMonitor()
    asyncio.run(monitor.run())

if __name__ == "__main__":
    main()
