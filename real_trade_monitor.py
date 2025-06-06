#!/usr/bin/env python3
"""
Real-Time Trade Monitor for First Real Trading
Provides detailed monitoring and alerts for initial real trades
"""
import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import asyncio
import aiohttp
from typing import Dict, List, Optional

# Initialize colorama
init()

class RealTimeTradeMonitor:
    def __init__(self, db_path='data/db/sol_bot_real.db', wallet_address='16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf'):
        self.db_path = db_path if os.path.exists(db_path) else 'data/db/sol_bot.db'
        self.wallet_address = wallet_address
        self.initial_balance = 1.0014
        self.last_trade_id = 0
        self.trade_history = []
        self.alerts = []
        self.first_trade_time = None
        self.monitoring_start = datetime.now()
        
        # Load trading parameters
        self.trading_params = self._load_trading_params()
        
        # Performance tracking
        self.session_metrics = {
            'trades_executed': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_volume': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'current_positions': {}
        }
        
    def _load_trading_params(self) -> Dict:
        """Load trading parameters"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def check_new_trades(self) -> List[Dict]:
        """Check for new trades since last check"""
        conn = self.get_connection()
        cursor = conn.cursor()
        new_trades = []
        
        try:
            cursor.execute("""
                SELECT 
                    id, contract_address, action, amount, price, 
                    timestamp, tx_hash, gain_loss_sol, percentage_change
                FROM trades
                WHERE id > ?
                ORDER BY id
            """, (self.last_trade_id,))
            
            trades = cursor.fetchall()
            
            for trade in trades:
                trade_dict = {
                    'id': trade[0],
                    'contract_address': trade[1],
                    'action': trade[2],
                    'amount': trade[3],
                    'price': trade[4],
                    'timestamp': trade[5],
                    'tx_hash': trade[6],
                    'gain_loss_sol': trade[7],
                    'percentage_change': trade[8]
                }
                
                new_trades.append(trade_dict)
                self.last_trade_id = trade[0]
                
                # Track first trade
                if self.first_trade_time is None:
                    self.first_trade_time = datetime.now()
                
                # Update session metrics
                self._update_session_metrics(trade_dict)
            
        except Exception as e:
            print(f"{Fore.RED}Error checking trades: {e}{Style.RESET_ALL}")
        finally:
            conn.close()
        
        return new_trades
    
    def _update_session_metrics(self, trade: Dict):
        """Update session performance metrics"""
        self.session_metrics['trades_executed'] += 1
        self.session_metrics['total_volume'] += trade['amount']
        
        if trade['action'] == 'BUY':
            # Track open position
            self.session_metrics['current_positions'][trade['contract_address']] = {
                'amount': trade['amount'],
                'entry_price': trade['price'],
                'entry_time': trade['timestamp']
            }
        
        elif trade['action'] == 'SELL':
            # Update P&L metrics
            if trade['gain_loss_sol'] is not None:
                self.session_metrics['total_pnl'] += trade['gain_loss_sol']
                
                if trade['gain_loss_sol'] > 0:
                    self.session_metrics['winning_trades'] += 1
                    if trade['gain_loss_sol'] > self.session_metrics['best_trade']:
                        self.session_metrics['best_trade'] = trade['gain_loss_sol']
                else:
                    self.session_metrics['losing_trades'] += 1
                    if trade['gain_loss_sol'] < self.session_metrics['worst_trade']:
                        self.session_metrics['worst_trade'] = trade['gain_loss_sol']
            
            # Remove from open positions
            if trade['contract_address'] in self.session_metrics['current_positions']:
                del self.session_metrics['current_positions'][trade['contract_address']]
    
    def calculate_current_balance(self) -> float:
        """Calculate current balance"""
        return self.initial_balance + self.session_metrics['total_pnl']
    
    def check_safety_state(self) -> Dict:
        """Check current safety state"""
        try:
            with open('data/safety_state.json', 'r') as f:
                return json.load(f)
        except:
            return {'is_paused': False, 'daily_loss': 0, 'daily_trades': 0}
    
    def generate_alerts(self, new_trades: List[Dict]) -> List[str]:
        """Generate alerts for new trades"""
        alerts = []
        
        for trade in new_trades:
            # Trade execution alert
            if trade['action'] == 'BUY':
                alerts.append(f"🟢 BUY: {trade['amount']:.4f} SOL of {trade['contract_address'][:8]}...")
            
            elif trade['action'] == 'SELL':
                if trade['gain_loss_sol'] is not None:
                    if trade['gain_loss_sol'] > 0:
                        alerts.append(f"💰 PROFIT: +{trade['gain_loss_sol']:.4f} SOL ({trade['percentage_change']:+.1f}%)")
                    else:
                        alerts.append(f"📉 LOSS: {trade['gain_loss_sol']:.4f} SOL ({trade['percentage_change']:.1f}%)")
        
        # Performance alerts
        current_balance = self.calculate_current_balance()
        
        if current_balance < self.initial_balance * 0.95:
            alerts.append(f"⚠️  Balance below 95% of initial: {current_balance:.4f} SOL")
        
        if self.session_metrics['total_pnl'] > 0.05:
            alerts.append(f"🎉 Session profit exceeds 0.05 SOL!")
        
        if self.session_metrics['losing_trades'] >= 3 and self.session_metrics['winning_trades'] == 0:
            alerts.append(f"⚠️  3 losses without wins - review strategy")
        
        return alerts
    
    def display_real_time_monitor(self):
        """Display real-time monitoring interface"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Check for new trades
        new_trades = self.check_new_trades()
        
        # Generate alerts
        if new_trades:
            self.alerts = self.generate_alerts(new_trades)
        
        # Get current data
        current_balance = self.calculate_current_balance()
        safety_state = self.check_safety_state()
        
        # Header
        print(f"{Fore.MAGENTA}{Back.BLACK}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💎 REAL TRADING MONITOR - LIVE MODE - {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{Back.BLACK}{'='*100}{Style.RESET_ALL}\n")
        
        # Wallet info
        print(f"{Fore.WHITE}Wallet: {self.wallet_address}{Style.RESET_ALL}")
        print(f"Monitoring Duration: {str(datetime.now() - self.monitoring_start).split('.')[0]}")
        
        if self.first_trade_time:
            print(f"First Trade: {(datetime.now() - self.first_trade_time).seconds // 60} minutes ago")
        else:
            print(f"{Fore.YELLOW}Waiting for first trade...{Style.RESET_ALL}")
        
        print(f"\n{'─'*100}\n")
        
        # Balance section
        pnl = current_balance - self.initial_balance
        pnl_pct = (pnl / self.initial_balance) * 100
        balance_color = Fore.GREEN if pnl >= 0 else Fore.RED
        
        print(f"{Fore.CYAN}💰 BALANCE STATUS{Style.RESET_ALL}")
        print(f"┌{'─'*30}┬{'─'*30}┬{'─'*36}┐")
        print(f"│ Current: {balance_color}{current_balance:>15.4f} SOL{Style.RESET_ALL} │"
              f" Initial: {self.initial_balance:>15.4f} SOL │"
              f" P&L: {balance_color}{pnl:>15.4f} SOL ({pnl_pct:+.1f}%){Style.RESET_ALL} │")
        print(f"└{'─'*30}┴{'─'*30}┴{'─'*36}┘\n")
        
        # Safety state
        safety_color = Fore.GREEN if not safety_state['is_paused'] else Fore.RED
        print(f"{Fore.CYAN}🛡️  SAFETY STATUS{Style.RESET_ALL}")
        print(f"Status: {safety_color}{'PAUSED' if safety_state['is_paused'] else 'ACTIVE'}{Style.RESET_ALL} | "
              f"Daily Loss: {safety_state.get('daily_loss', 0):.4f} SOL | "
              f"Daily Trades: {safety_state.get('daily_trades', 0)}")
        
        if safety_state.get('is_paused'):
            print(f"{Fore.RED}Pause Reason: {safety_state.get('pause_reason', 'Unknown')}{Style.RESET_ALL}")
        
        print(f"\n{'─'*100}\n")
        
        # Session metrics
        print(f"{Fore.CYAN}📊 SESSION PERFORMANCE{Style.RESET_ALL}")
        
        win_rate = 0
        if self.session_metrics['winning_trades'] + self.session_metrics['losing_trades'] > 0:
            win_rate = (self.session_metrics['winning_trades'] / 
                       (self.session_metrics['winning_trades'] + self.session_metrics['losing_trades'])) * 100
        
        print(f"Trades: {self.session_metrics['trades_executed']} | "
              f"Wins: {Fore.GREEN}{self.session_metrics['winning_trades']}{Style.RESET_ALL} | "
              f"Losses: {Fore.RED}{self.session_metrics['losing_trades']}{Style.RESET_ALL} | "
              f"Win Rate: {win_rate:.1f}%")
        
        print(f"Volume: {self.session_metrics['total_volume']:.4f} SOL | "
              f"Best: {Fore.GREEN}+{self.session_metrics['best_trade']:.4f} SOL{Style.RESET_ALL} | "
              f"Worst: {Fore.RED}{self.session_metrics['worst_trade']:.4f} SOL{Style.RESET_ALL}")
        
        print(f"\n{'─'*100}\n")
        
        # Open positions
        print(f"{Fore.CYAN}📂 OPEN POSITIONS ({len(self.session_metrics['current_positions'])}){Style.RESET_ALL}")
        
        if self.session_metrics['current_positions']:
            print(f"{'Token':<15} {'Amount':>12} {'Entry Price':>15} {'Time Held':<15}")
            print("─" * 60)
            
            for token, pos in self.session_metrics['current_positions'].items():
                token_short = token[:10] + "..." if len(token) > 10 else token
                try:
                    entry_time = datetime.fromisoformat(pos['entry_time'].replace('T', ' ').split('.')[0])
                    time_held = str(datetime.now() - entry_time).split('.')[0]
                except:
                    time_held = "Unknown"
                
                print(f"{token_short:<15} {pos['amount']:>12.4f} ${pos['entry_price']:>14.6f} {time_held:<15}")
        else:
            print("No open positions")
        
        print(f"\n{'─'*100}\n")
        
        # Recent trades
        print(f"{Fore.CYAN}📜 RECENT TRADES (Last 5){Style.RESET_ALL}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT contract_address, action, amount, price, timestamp, gain_loss_sol, percentage_change
            FROM trades
            ORDER BY id DESC
            LIMIT 5
        """)
        
        recent = cursor.fetchall()
        conn.close()
        
        if recent:
            for trade in recent:
                token = trade[0][:8] + "..."
                action = trade[1]
                amount = trade[2]
                timestamp = trade[4].split('T')[1].split('.')[0] if 'T' in trade[4] else trade[4]
                
                action_color = Fore.GREEN if action == 'BUY' else Fore.RED
                print(f"{timestamp} | {action_color}{action:<4}{Style.RESET_ALL} | {amount:.4f} SOL | {token}")
                
                if action == 'SELL' and trade[5] is not None:
                    pnl_color = Fore.GREEN if trade[5] > 0 else Fore.RED
                    print(f"         └─ P&L: {pnl_color}{trade[5]:+.4f} SOL ({trade[6]:+.1f}%){Style.RESET_ALL}")
        else:
            print("No trades yet")
        
        # Alerts section
        if self.alerts:
            print(f"\n{'─'*100}\n")
            print(f"{Fore.YELLOW}🔔 ALERTS{Style.RESET_ALL}")
            for alert in self.alerts[-5:]:  # Show last 5 alerts
                print(f"  {alert}")
        
        # Trading parameters
        print(f"\n{'─'*100}\n")
        print(f"{Fore.CYAN}⚙️  ACTIVE PARAMETERS{Style.RESET_ALL}")
        print(f"Position Size: {self.trading_params.get('min_position_size_pct', 2)}-"
              f"{self.trading_params.get('default_position_size_pct', 3)}-"
              f"{self.trading_params.get('max_position_size_pct', 5)}% | "
              f"Take Profit: {self.trading_params.get('take_profit_pct', 0.5)*100:.0f}% | "
              f"Stop Loss: {self.trading_params.get('stop_loss_pct', 0.05)*100:.0f}%")
        
        print(f"ML Threshold: {self.trading_params.get('ml_confidence_threshold', 0.65)} | "
              f"Min Volume: ${self.trading_params.get('min_volume_24h', 30000):,.0f} | "
              f"Min Liquidity: ${self.trading_params.get('min_liquidity', 20000):,.0f}")
        
        # Recommendations
        print(f"\n{'─'*100}\n")
        print(f"{Fore.YELLOW}💡 LIVE RECOMMENDATIONS{Style.RESET_ALL}")
        
        # Dynamic recommendations based on current state
        if self.session_metrics['trades_executed'] == 0:
            print("• Waiting for first trade - ensure bot is running and finding opportunities")
        elif self.session_metrics['trades_executed'] < 5:
            print("• Collecting initial data - monitor closely for first 5-10 trades")
        elif win_rate < 50 and self.session_metrics['trades_executed'] > 5:
            print("• Win rate below 50% - consider increasing ML confidence threshold")
        elif win_rate > 80 and self.session_metrics['trades_executed'] > 10:
            print("• Excellent win rate! Consider slightly increasing position sizes")
        
        if current_balance < self.initial_balance * 0.95:
            print("• Balance down 5% - review recent losing trades for patterns")
        
        if len(self.session_metrics['current_positions']) > 3:
            print("• Multiple open positions - monitor closely for exit signals")
        
        # Footer
        print(f"\n{Fore.CYAN}{'─'*100}{Style.RESET_ALL}")
        print(f"Press Ctrl+C to stop monitoring | Updates every 3 seconds")
    
    def run(self):
        """Run the real-time monitor"""
        print(f"{Fore.MAGENTA}Starting Real-Time Trade Monitor...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Monitoring wallet: {self.wallet_address}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Initial balance: {self.initial_balance} SOL{Style.RESET_ALL}\n")
        
        time.sleep(2)
        
        while True:
            try:
                self.display_real_time_monitor()
                time.sleep(3)  # Update every 3 seconds for real-time monitoring
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitoring stopped.{Style.RESET_ALL}")
                
                # Show final summary
                print(f"\n{Fore.CYAN}SESSION SUMMARY{Style.RESET_ALL}")
                print(f"Duration: {str(datetime.now() - self.monitoring_start).split('.')[0]}")
                print(f"Total Trades: {self.session_metrics['trades_executed']}")
                print(f"Final P&L: {self.session_metrics['total_pnl']:+.4f} SOL")
                print(f"Final Balance: {self.calculate_current_balance():.4f} SOL")
                
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = RealTimeTradeMonitor()
    monitor.run()
