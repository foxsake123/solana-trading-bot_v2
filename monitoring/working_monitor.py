#!/usr/bin/env python3
"""
Simple working monitor for the current database schema
"""
import sqlite3
import time
import os
from datetime import datetime
from colorama import init, Fore, Style, Back

# Initialize colorama for Windows
init()

class TradingMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = 10.0
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def check_database(self):
        """Check if database exists and show schema"""
        if not os.path.exists(self.db_path):
            print(f"{Fore.RED}❌ Database not found at {self.db_path}{Style.RESET_ALL}")
            return False
        
        # Check schema
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get trades table schema
        cursor.execute("PRAGMA table_info(trades)")
        columns = cursor.fetchall()
        
        print(f"{Fore.CYAN}Database Schema:{Style.RESET_ALL}")
        print("Trades table columns:", [col[1] for col in columns])
        print()
        
        conn.close()
        return True
    
    def calculate_balance(self):
        """Calculate current balance from trades"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start with initial balance
            balance = self.initial_balance
            
            # Get all trades
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
            
            return balance
            
        except Exception as e:
            print(f"{Fore.RED}Error calculating balance: {e}{Style.RESET_ALL}")
            return self.initial_balance
        finally:
            conn.close()
    
    def get_recent_trades(self, limit=10):
        """Get recent trades"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    id,
                    contract_address,
                    action,
                    amount,
                    price,
                    timestamp,
                    gain_loss_sol,
                    percentage_change
                FROM trades 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"{Fore.RED}Error getting trades: {e}{Style.RESET_ALL}")
            return []
        finally:
            conn.close()
    
    def get_positions(self):
        """Get current positions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    contract_address,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net_amount,
                    COUNT(CASE WHEN action='BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN action='SELL' THEN 1 END) as sell_count,
                    AVG(CASE WHEN action='BUY' THEN price END) as avg_buy_price
                FROM trades
                GROUP BY contract_address
                HAVING net_amount > 0.001
            """)
            
            return cursor.fetchall()
            
        except Exception as e:
            print(f"{Fore.RED}Error getting positions: {e}{Style.RESET_ALL}")
            return []
        finally:
            conn.close()
    
    def get_performance_stats(self):
        """Calculate performance statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Total trades
            cursor.execute("SELECT COUNT(*) FROM trades")
            total_trades = cursor.fetchone()[0]
            
            # Buys and sells
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='BUY'")
            total_buys = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
            total_sells = cursor.fetchone()[0]
            
            # Profit/Loss from sells
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN gain_loss_sol > 0 THEN 1 END) as wins,
                    COUNT(CASE WHEN gain_loss_sol < 0 THEN 1 END) as losses,
                    SUM(gain_loss_sol) as total_pnl
                FROM trades 
                WHERE action='SELL' AND gain_loss_sol IS NOT NULL
            """)
            
            result = cursor.fetchone()
            wins = result[0] or 0
            losses = result[1] or 0
            total_pnl = result[2] or 0.0
            
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            
            return {
                'total_trades': total_trades,
                'total_buys': total_buys,
                'total_sells': total_sells,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_pnl': total_pnl
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error getting performance stats: {e}{Style.RESET_ALL}")
            return None
        finally:
            conn.close()
    
    def display(self):
        """Display monitoring information"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Header
        print(f"{Fore.CYAN}{Back.BLACK}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🤖 SOLANA TRADING BOT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{'='*80}{Style.RESET_ALL}\n")
        
        # Balance
        balance = self.calculate_balance()
        balance_color = Fore.GREEN if balance >= self.initial_balance else Fore.RED
        print(f"{Fore.WHITE}💰 Current Balance: {balance_color}{balance:.4f} SOL{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   Initial Balance: {self.initial_balance:.4f} SOL")
        print(f"{Fore.WHITE}   P&L: {balance_color}{balance - self.initial_balance:+.4f} SOL ({(balance/self.initial_balance - 1)*100:+.1f}%){Style.RESET_ALL}\n")
        
        # Performance Stats
        stats = self.get_performance_stats()
        if stats:
            print(f"{Fore.CYAN}📊 PERFORMANCE STATISTICS:{Style.RESET_ALL}")
            print(f"   Total Trades: {stats['total_trades']} (Buy: {stats['total_buys']}, Sell: {stats['total_sells']})")
            if stats['total_sells'] > 0:
                win_color = Fore.GREEN if stats['win_rate'] > 50 else Fore.RED
                print(f"   Win Rate: {win_color}{stats['win_rate']:.1f}%{Style.RESET_ALL} ({stats['wins']} wins, {stats['losses']} losses)")
                pnl_color = Fore.GREEN if stats['total_pnl'] > 0 else Fore.RED
                print(f"   Total P&L from closed trades: {pnl_color}{stats['total_pnl']:.4f} SOL{Style.RESET_ALL}")
            print()
        
        # Active Positions
        positions = self.get_positions()
        print(f"{Fore.CYAN}💼 ACTIVE POSITIONS ({len(positions)}):{Style.RESET_ALL}")
        if positions:
            for contract, net_amount, buys, sells, avg_price in positions[:5]:
                token = contract[:8] + "..." if len(contract) > 12 else contract
                print(f"   {Fore.YELLOW}{token}{Style.RESET_ALL}: {net_amount:.4f} SOL (Buys: {buys}, Sells: {sells})")
        else:
            print("   No active positions")
        print()
        
        # Recent Trades
        trades = self.get_recent_trades(5)
        print(f"{Fore.CYAN}📈 RECENT TRADES:{Style.RESET_ALL}")
        if trades:
            for trade in trades:
                trade_id, contract, action, amount, price, timestamp, gain_loss, pct_change = trade
                
                # Format display
                action_color = Fore.GREEN if action == 'BUY' else Fore.RED
                action_emoji = "🟢" if action == 'BUY' else "🔴"
                token = contract[:8] + "..." if contract and len(contract) > 12 else contract
                time_str = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp
                
                print(f"   {action_emoji} {action_color}{action}{Style.RESET_ALL} {amount:.4f} SOL | {token} | {time_str}")
                
                # Show P&L for sells
                if action == 'SELL' and gain_loss is not None:
                    pnl_color = Fore.GREEN if gain_loss > 0 else Fore.RED
                    pct_color = Fore.GREEN if pct_change > 0 else Fore.RED
                    print(f"      P&L: {pnl_color}{gain_loss:+.4f} SOL{Style.RESET_ALL} ({pct_color}{pct_change:+.1f}%{Style.RESET_ALL})")
        else:
            print("   No trades yet")
    
    def run(self):
        """Run the monitor"""
        print(f"{Fore.CYAN}Starting Trading Monitor...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        # Check database first
        if not self.check_database():
            return
        
        time.sleep(2)
        
        while True:
            try:
                self.display()
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = TradingMonitor()
    monitor.run()
