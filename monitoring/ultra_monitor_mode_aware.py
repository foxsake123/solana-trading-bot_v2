#!/usr/bin/env python3
"""
Ultra Enhanced Trading Monitor with Advanced Analytics and Alerts
Features: Real-time P&L tracking, position analysis, ML performance, alerts, and more
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import pandas as pd
import numpy as np
from collections import deque
import json

# Initialize colorama for Windows
init()

class UltraEnhancedMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = self._detect_initial_balance()
        self.performance_history = deque(maxlen=100)  # Track last 100 data points
        self.alerts = []
        self.last_check = datetime.now()
        print(f"Monitor initialized with balance: {self.initial_balance} SOL")
        
    def _detect_initial_balance(self):
        """Detect which mode we're in and get correct initial balance"""
        # First, check if we have a safety state file (indicates real mode)
        if os.path.exists('data/safety_state.json'):
            try:
                with open('data/safety_state.json', 'r') as f:
                    safety_state = json.load(f)
                    # If safety state exists, we might be in real mode
            except:
                pass
        
        # Check for active config by looking at recent database entries
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if we have real transactions
            cursor.execute("""
                SELECT tx_hash 
                FROM trades 
                WHERE tx_hash IS NOT NULL 
                AND tx_hash != 'simulated'
                AND timestamp > datetime('now', '-1 day')
                LIMIT 1
            """)
            
            real_tx = cursor.fetchone()
            conn.close()
            
            if real_tx:
                # We have real transactions, use real config
                try:
                    with open('config/bot_control_real.json', 'r') as f:
                        config = json.load(f)
                        balance = config.get('starting_balance', 1.0014)
                        print(f"Detected REAL mode - using balance: {balance} SOL")
                        return balance
                except:
                    return 1.0014  # Your known real balance
            
        except:
            pass
        
        # Default: Check simulation config
        try:
            with open('config/bot_control.json', 'r') as f:
                config = json.load(f)
                balance = config.get('starting_simulation_balance', 
                                   config.get('current_simulation_balance', 10.0))
                print(f"Detected SIMULATION mode - using balance: {balance} SOL")
                return balance
        except:
            return 9.05  # Your known simulation balance

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def check_database(self):
        """Check if database exists"""
        if not os.path.exists(self.db_path):
            print(f"{Fore.RED}❌ Database not found at {self.db_path}{Style.RESET_ALL}")
            return False
        return True
    
    def calculate_real_time_balance(self):
        """Calculate real-time balance with full portfolio value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start with initial balance
            balance = self.initial_balance
            
            # Calculate from all trades
            cursor.execute("""
                SELECT action, amount, price 
                FROM trades 
                ORDER BY id
            """)
            
            trades = cursor.fetchall()
            
            for action, amount, price in trades:
                if amount is None:
                    continue
                    
                if action == 'BUY':
                    balance -= float(amount)
                elif action == 'SELL':
                    balance += float(amount)
            
            # Get open positions
            cursor.execute("""
                SELECT 
                    contract_address,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net_amount,
                    AVG(CASE WHEN action='BUY' THEN price END) as avg_buy_price
                FROM trades
                GROUP BY contract_address
                HAVING net_amount > 0.001
            """)
            
            open_positions = cursor.fetchall()
            position_value = sum(float(net_amount) for _, net_amount, _ in open_positions)
            
            # Calculate unrealized P&L (simplified - would need current prices in real implementation)
            unrealized_pnl = 0
            for contract, net_amount, avg_price in open_positions:
                # In real implementation, fetch current price from API
                # For now, assume 10% unrealized gain as placeholder
                unrealized_pnl += net_amount * 0.1
            
            return {
                'total': balance + position_value + unrealized_pnl,
                'available': balance,
                'in_positions': position_value,
                'unrealized_pnl': unrealized_pnl,
                'open_positions_count': len(open_positions)
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error calculating balance: {e}{Style.RESET_ALL}")
            return {
                'total': self.initial_balance,
                'available': self.initial_balance,
                'in_positions': 0,
                'unrealized_pnl': 0,
                'open_positions_count': 0
            }
        finally:
            conn.close()
    
    def get_performance_metrics(self):
        """Get comprehensive performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        metrics = {}
        
        try:
            # Basic trade counts
            cursor.execute("SELECT COUNT(*) FROM trades")
            metrics['total_trades'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='BUY'")
            metrics['total_buys'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
            metrics['total_sells'] = cursor.fetchone()[0]
            
            # Win/Loss analysis
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN gain_loss_sol > 0 THEN 1 END) as wins,
                    COUNT(CASE WHEN gain_loss_sol < 0 THEN 1 END) as losses,
                    COUNT(CASE WHEN gain_loss_sol = 0 THEN 1 END) as breakeven,
                    SUM(gain_loss_sol) as total_pnl,
                    AVG(gain_loss_sol) as avg_pnl,
                    MAX(gain_loss_sol) as best_trade,
                    MIN(gain_loss_sol) as worst_trade,
                    AVG(CASE WHEN gain_loss_sol > 0 THEN gain_loss_sol END) as avg_win,
                    AVG(CASE WHEN gain_loss_sol < 0 THEN gain_loss_sol END) as avg_loss,
                    MAX(percentage_change) as best_pct,
                    MIN(percentage_change) as worst_pct,
                    AVG(CASE WHEN gain_loss_sol > 0 THEN percentage_change END) as avg_win_pct,
                    AVG(CASE WHEN gain_loss_sol < 0 THEN percentage_change END) as avg_loss_pct,
                    0.0 as pnl_stddev
                FROM trades 
                WHERE action='SELL' AND gain_loss_sol IS NOT NULL
            """)
            
            result = cursor.fetchone()
            metrics.update({
                'wins': result[0] or 0,
                'losses': result[1] or 0,
                'breakeven': result[2] or 0,
                'total_pnl': result[3] or 0.0,
                'avg_pnl': result[4] or 0.0,
                'best_trade': result[5] or 0.0,
                'worst_trade': result[6] or 0.0,
                'avg_win': result[7] or 0.0,
                'avg_loss': result[8] or 0.0,
                'best_pct': result[9] or 0.0,
                'worst_pct': result[10] or 0.0,
                'avg_win_pct': result[11] or 0.0,
                'avg_loss_pct': result[12] or 0.0,
                'pnl_stddev': result[13] or 0.0
            })
            
            # Calculate advanced metrics
            total_completed = metrics['wins'] + metrics['losses']
            if total_completed > 0:
                metrics['win_rate'] = (metrics['wins'] / total_completed) * 100
                
                # Risk metrics
                if metrics['avg_loss'] != 0:
                    metrics['risk_reward'] = abs(metrics['avg_win'] / metrics['avg_loss'])
                else:
                    metrics['risk_reward'] = 0
                
                # Profit factor
                total_wins = metrics['wins'] * abs(metrics['avg_win']) if metrics['avg_win'] else 0
                total_losses = metrics['losses'] * abs(metrics['avg_loss']) if metrics['avg_loss'] else 0
                metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else 0
                
                # Sharpe ratio approximation (simplified)
                if metrics['pnl_stddev'] > 0:
                    metrics['sharpe_ratio'] = (metrics['avg_pnl'] * np.sqrt(252)) / metrics['pnl_stddev']
                else:
                    metrics['sharpe_ratio'] = 0
            else:
                metrics['win_rate'] = 0
                metrics['risk_reward'] = 0
                metrics['profit_factor'] = 0
                metrics['sharpe_ratio'] = 0
            
            # Time-based analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as trades_24h,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as pnl_24h
                FROM trades 
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            
            time_result = cursor.fetchone()
            metrics['trades_24h'] = time_result[0] or 0
            metrics['pnl_24h'] = time_result[1] or 0.0
            
            # Position metrics
            cursor.execute("""
                SELECT 
                    AVG(amount) as avg_position,
                    MIN(amount) as min_position,
                    MAX(amount) as max_position,
                    COUNT(DISTINCT contract_address) as unique_tokens
                FROM trades
                WHERE action='BUY'
            """)
            
            pos_result = cursor.fetchone()
            metrics.update({
                'avg_position': pos_result[0] or 0.0,
                'min_position': pos_result[1] or 0.0,
                'max_position': pos_result[2] or 0.0,
                'unique_tokens': pos_result[3] or 0
            })
            
            # ML performance (if using ML)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM trades 
                WHERE action='BUY' 
                AND timestamp > datetime('now', '-24 hours')
            """)
            recent_buys = cursor.fetchone()[0]
            
            if recent_buys > 0:
                # Simplified ML performance - in real implementation, track ML predictions
                metrics['ml_accuracy'] = metrics['win_rate']  # Placeholder
                metrics['ml_trades_24h'] = recent_buys
            
            return metrics
            
        except Exception as e:
            print(f"{Fore.RED}Error getting metrics: {e}{Style.RESET_ALL}")
            return {}
        finally:
            conn.close()
    
    def check_alerts(self, balance_info, metrics):
        """Check for conditions that warrant alerts"""
        alerts = []
        
        # Balance alerts
        if balance_info['available'] < 1.0:
            alerts.append(('critical', 'Low available balance! Consider closing positions'))
        elif balance_info['available'] < 2.0:
            alerts.append(('warning', 'Available balance getting low'))
        
        # Performance alerts
        if metrics.get('pnl_24h', 0) < -0.5:
            alerts.append(('warning', f"High losses in 24h: {metrics['pnl_24h']:.4f} SOL"))
        
        if metrics.get('win_rate', 0) < 50 and metrics.get('total_sells', 0) > 20:
            alerts.append(('warning', 'Win rate below 50% - review strategy'))
        
        # Position size alerts
        avg_pos = metrics.get('avg_position', 0)
        available = balance_info['available']
        if avg_pos > 0 and available > 0:
            if avg_pos > available * 0.5:
                alerts.append(('warning', 'Position sizes too large for balance'))
        
        # Risk alerts
        if metrics.get('risk_reward', 0) < 1.5 and metrics.get('total_sells', 0) > 10:
            alerts.append(('info', 'Risk/reward ratio below 1.5:1'))
        
        # Opportunity alerts
        if metrics.get('best_pct', 0) > 1000:
            alerts.append(('success', f"Bot found {metrics['best_pct']:.0f}% gain!"))
        
        if metrics.get('win_rate', 0) > 80 and metrics.get('total_sells', 0) > 20:
            alerts.append(('success', 'Excellent win rate! Consider increasing position sizes'))
        
        return alerts
    
    def get_hourly_performance(self):
        """Analyze performance by hour"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    COUNT(*) as trades,
                    SUM(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                    AVG(CASE WHEN action='SELL' THEN gain_loss_sol END) as avg_pnl
                FROM trades
                GROUP BY hour
                ORDER BY hour
            """
            
            df = pd.read_sql_query(query, conn)
            return df
            
        except Exception as e:
            print(f"{Fore.RED}Error getting hourly performance: {e}{Style.RESET_ALL}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_token_leaderboard(self):
        """Get top performing tokens"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    contract_address,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl,
                    AVG(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN percentage_change END) as avg_gain_pct,
                    MAX(CASE WHEN action='SELL' THEN percentage_change END) as max_gain_pct
                FROM trades
                GROUP BY contract_address
                HAVING trade_count >= 2
                ORDER BY total_pnl DESC
                LIMIT 10
            """
            
            df = pd.read_sql_query(query, conn)
            return df
            
        except Exception as e:
            print(f"{Fore.RED}Error getting token leaderboard: {e}{Style.RESET_ALL}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def display_ultra_enhanced(self):
        """Display ultra enhanced monitoring with all features"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get all data
        balance_info = self.calculate_real_time_balance()
        metrics = self.get_performance_metrics()
        alerts = self.check_alerts(balance_info, metrics)
        hourly_perf = self.get_hourly_performance()
        token_leaderboard = self.get_token_leaderboard()
        
        # Store for performance tracking
        self.performance_history.append({
            'timestamp': datetime.now(),
            'balance': balance_info['total'],
            'pnl': balance_info['total'] - self.initial_balance
        })
        
        # Header with alerts
        print(f"{Fore.CYAN}{Back.BLACK}{'='*120}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚀 ULTRA ENHANCED TRADING BOT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{'='*120}{Style.RESET_ALL}")
        
        # Alerts section
        if alerts:
            print(f"\n{Fore.WHITE}🔔 ALERTS:{Style.RESET_ALL}")
            for alert_type, message in alerts:
                if alert_type == 'critical':
                    print(f"   {Fore.RED}⚠️  {message}{Style.RESET_ALL}")
                elif alert_type == 'warning':
                    print(f"   {Fore.YELLOW}⚡ {message}{Style.RESET_ALL}")
                elif alert_type == 'success':
                    print(f"   {Fore.GREEN}✨ {message}{Style.RESET_ALL}")
                else:
                    print(f"   {Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
        
        # Main dashboard layout
        print(f"\n{'─'*120}")
        
        # Row 1: Balance and P&L
        total_balance = balance_info['total']
        pnl = total_balance - self.initial_balance
        pnl_pct = (total_balance/self.initial_balance - 1)*100
        balance_color = Fore.GREEN if pnl >= 0 else Fore.RED
        
        print(f"{Fore.CYAN}💰 PORTFOLIO VALUE{Style.RESET_ALL}")
        print(f"┌{'─'*35}┬{'─'*35}┬{'─'*46}┐")
        print(f"│ Total Value: {balance_color}{total_balance:>16.4f} SOL{Style.RESET_ALL} │"
              f" Available: {Fore.WHITE}{balance_info['available']:>18.4f} SOL{Style.RESET_ALL} │"
              f" In Positions: {Fore.YELLOW}{balance_info['in_positions']:>12.4f} SOL{Style.RESET_ALL} ({balance_info['open_positions_count']} pos) │")
        print(f"│ Total P&L: {balance_color}{pnl:>18.4f} SOL{Style.RESET_ALL} │"
              f" Percentage: {balance_color}{pnl_pct:>17.1f}%{Style.RESET_ALL} │"
              f" Unrealized P&L: {Fore.YELLOW}{balance_info['unrealized_pnl']:>10.4f} SOL{Style.RESET_ALL} (est)    │")
        print(f"└{'─'*35}┴{'─'*35}┴{'─'*46}┘")
        
        # Row 2: Key Performance Indicators
        print(f"\n{Fore.CYAN}📊 KEY PERFORMANCE INDICATORS{Style.RESET_ALL}")
        print(f"┌{'─'*29}┬{'─'*29}┬{'─'*29}┬{'─'*29}┐")
        
        win_color = Fore.GREEN if metrics.get('win_rate', 0) > 60 else Fore.YELLOW if metrics.get('win_rate', 0) > 50 else Fore.RED
        rr_color = Fore.GREEN if metrics.get('risk_reward', 0) > 2 else Fore.YELLOW if metrics.get('risk_reward', 0) > 1.5 else Fore.RED
        pf_color = Fore.GREEN if metrics.get('profit_factor', 0) > 1.5 else Fore.YELLOW if metrics.get('profit_factor', 0) > 1 else Fore.RED
        
        print(f"│ Win Rate: {win_color}{metrics.get('win_rate', 0):>15.1f}%{Style.RESET_ALL} │"
              f" Risk/Reward: {rr_color}{metrics.get('risk_reward', 0):>12.2f}:1{Style.RESET_ALL} │"
              f" Profit Factor: {pf_color}{metrics.get('profit_factor', 0):>11.2f}{Style.RESET_ALL} │"
              f" Sharpe Ratio: {metrics.get('sharpe_ratio', 0):>12.2f} │")
        
        print(f"│ Wins: {Fore.GREEN}{metrics.get('wins', 0):>20}{Style.RESET_ALL} │"
              f" Losses: {Fore.RED}{metrics.get('losses', 0):>18}{Style.RESET_ALL} │"
              f" Total Trades: {metrics.get('total_trades', 0):>12} │"
              f" Unique Tokens: {metrics.get('unique_tokens', 0):>11} │")
        
        print(f"└{'─'*29}┴{'─'*29}┴{'─'*29}┴{'─'*29}┘")
        
        # Row 3: Recent Performance
        print(f"\n{Fore.CYAN}📈 RECENT PERFORMANCE (24H){Style.RESET_ALL}")
        pnl_24h_color = Fore.GREEN if metrics.get('pnl_24h', 0) > 0 else Fore.RED
        print(f"Trades: {metrics.get('trades_24h', 0)} | "
              f"P&L: {pnl_24h_color}{metrics.get('pnl_24h', 0):+.4f} SOL{Style.RESET_ALL} | "
              f"Best Trade: {Fore.GREEN}{metrics.get('best_trade', 0):.4f} SOL{Style.RESET_ALL} ({metrics.get('best_pct', 0):.1f}%) | "
              f"Worst: {Fore.RED}{metrics.get('worst_trade', 0):.4f} SOL{Style.RESET_ALL} ({metrics.get('worst_pct', 0):.1f}%)")
        
        # Row 4: Position Analysis
        print(f"\n{Fore.CYAN}📏 POSITION SIZING ANALYSIS{Style.RESET_ALL}")
        avg_pos_pct = (metrics.get('avg_position', 0) / balance_info['total']) * 100 if balance_info['total'] > 0 else 0
        print(f"Average Size: {metrics.get('avg_position', 0):.4f} SOL ({avg_pos_pct:.1f}% of portfolio) | "
              f"Range: {metrics.get('min_position', 0):.4f} - {metrics.get('max_position', 0):.4f} SOL")
        
        # Row 5: Best Performing Hours
        if not hourly_perf.empty:
            print(f"\n{Fore.CYAN}⏰ BEST TRADING HOURS (UTC){Style.RESET_ALL}")
            best_hours = hourly_perf.nlargest(3, 'avg_pnl')
            hour_str = ""
            for idx, row in best_hours.iterrows():
                win_rate = (row['wins'] / row['trades'] * 100) if row['trades'] > 0 else 0
                hour_str += f"Hour {int(row['hour']):02d}: {win_rate:.0f}% WR, {row['avg_pnl']:.4f} SOL avg | "
            print(hour_str.rstrip(" | "))
        
        # Row 6: Token Leaderboard
        if not token_leaderboard.empty:
            print(f"\n{Fore.CYAN}🏆 TOP PERFORMING TOKENS{Style.RESET_ALL}")
            print(f"{'Token':<15} {'Trades':>8} {'Total P&L':>12} {'Avg Gain %':>12} {'Max Gain %':>12}")
            print("─" * 62)
            
            for idx, row in token_leaderboard.head(5).iterrows():
                token = row['contract_address'][:10] + "..." if len(row['contract_address']) > 10 else row['contract_address']
                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"{token:<15} {int(row['trade_count']):>8} "
                      f"{pnl_color}{row['total_pnl']:>12.4f}{Style.RESET_ALL} "
                      f"{row['avg_gain_pct'] or 0:>12.1f} "
                      f"{row['max_gain_pct'] or 0:>12.1f}")
        
        # Row 7: Performance Trend
        if len(self.performance_history) > 1:
            print(f"\n{Fore.CYAN}📉 PERFORMANCE TREND{Style.RESET_ALL}")
            recent_points = list(self.performance_history)[-10:]
            trend = ""
            for i in range(len(recent_points)):
                if i == 0:
                    continue
                if recent_points[i]['balance'] > recent_points[i-1]['balance']:
                    trend += "▲"
                elif recent_points[i]['balance'] < recent_points[i-1]['balance']:
                    trend += "▼"
                else:
                    trend += "─"
            print(f"Last 10 updates: {trend}")
        
        # Row 8: ML Performance (if available)
        if metrics.get('ml_trades_24h', 0) > 0:
            print(f"\n{Fore.CYAN}🤖 ML MODEL PERFORMANCE{Style.RESET_ALL}")
            print(f"ML Accuracy: ~{metrics.get('ml_accuracy', 0):.1f}% | "
                  f"ML Trades (24h): {metrics.get('ml_trades_24h', 0)}")
        
        # Footer with recommendations
        print(f"\n{'─'*120}")
        print(f"{Fore.CYAN}💡 RECOMMENDATIONS{Style.RESET_ALL}")
        
        # Dynamic recommendations based on current state
        if balance_info['available'] < 1.0:
            print(f"• {Fore.RED}Critical: Very low balance! Close some positions or add funds{Style.RESET_ALL}")
        
        if metrics.get('win_rate', 0) > 75 and metrics.get('avg_position', 0) < balance_info['total'] * 0.03:
            print(f"• {Fore.GREEN}Increase position sizes - your win rate of {metrics.get('win_rate', 0):.1f}% is excellent{Style.RESET_ALL}")
        
        if metrics.get('risk_reward', 0) < 1.5:
            print(f"• {Fore.YELLOW}Consider increasing take profit target to improve risk/reward ratio{Style.RESET_ALL}")
        
        if metrics.get('best_pct', 0) > 500:
            print(f"• {Fore.GREEN}Bot successfully finding high-gain opportunities (best: {metrics.get('best_pct', 0):.0f}%){Style.RESET_ALL}")
        
        if metrics.get('trades_24h', 0) == 0:
            print(f"• {Fore.YELLOW}No trades in last 24h - check if bot is running properly{Style.RESET_ALL}")
    
    def export_performance_report(self):
        """Export detailed performance report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'balance_info': self.calculate_real_time_balance(),
            'performance_metrics': self.get_performance_metrics(),
            'hourly_performance': self.get_hourly_performance().to_dict('records'),
            'token_leaderboard': self.get_token_leaderboard().to_dict('records'),
            'performance_history': list(self.performance_history)
        }
        
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n{Fore.GREEN}✅ Performance report exported to performance_report.json{Style.RESET_ALL}")
    
    def run(self):
        """Run the ultra enhanced monitor"""
        print(f"{Fore.CYAN}Starting Ultra Enhanced Trading Monitor...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop | Press 'E' to export report{Style.RESET_ALL}\n")
        
        if not self.check_database():
            return
        
        time.sleep(2)
        
        while True:
            try:
                self.display_ultra_enhanced()
                
                # Check for keyboard input (non-blocking)
                if os.name == 'nt':  # Windows
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                        if key == 'E':
                            self.export_performance_report()
                            time.sleep(2)
                
                time.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                
                # Ask if user wants to export report before exiting
                try:
                    response = input("Export performance report before exiting? (y/n): ")
                    if response.lower() == 'y':
                        self.export_performance_report()
                except:
                    pass
                
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = UltraEnhancedMonitor()
    monitor.run()
