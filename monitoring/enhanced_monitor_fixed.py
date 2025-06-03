#!/usr/bin/env python3
"""
Enhanced trading monitor with FIXED real-time balance calculation
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import pandas as pd

# Initialize colorama for Windows
init()

class EnhancedTradingMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = 10.0
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def check_database(self):
        """Check if database exists"""
        if not os.path.exists(self.db_path):
            print(f"{Fore.RED}❌ Database not found at {self.db_path}{Style.RESET_ALL}")
            return False
        return True
    
    def calculate_balance(self):
        """Calculate current balance including open positions"""
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
            
            return balance
            
        except Exception as e:
            print(f"{Fore.RED}Error calculating balance: {e}{Style.RESET_ALL}")
            return self.initial_balance
        finally:
            conn.close()
    
    def calculate_real_time_balance(self):
        """Calculate real-time balance (available + in positions)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get available balance (initial - buys + sells)
            available_balance = self.calculate_balance()
            
            # Get current open positions value
            cursor.execute("""
                SELECT 
                    contract_address,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net_amount
                FROM trades
                GROUP BY contract_address
                HAVING net_amount > 0.001
            """)
            
            open_positions = cursor.fetchall()
            position_value = sum(float(net_amount) for _, net_amount in open_positions)
            
            # Total balance = available + in positions
            total_balance = available_balance + position_value
            
            return {
                'total': total_balance,
                'available': available_balance,
                'in_positions': position_value,
                'open_positions_count': len(open_positions)
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error calculating real-time balance: {e}{Style.RESET_ALL}")
            return {
                'total': self.initial_balance,
                'available': self.initial_balance,
                'in_positions': 0,
                'open_positions_count': 0
            }
        finally:
            conn.close()
    
    def get_detailed_stats(self):
        """Get comprehensive trading statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Total trades
            cursor.execute("SELECT COUNT(*) FROM trades")
            stats['total_trades'] = cursor.fetchone()[0]
            
            # Buys and sells
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='BUY'")
            stats['total_buys'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trades WHERE action='SELL'")
            stats['total_sells'] = cursor.fetchone()[0]
            
            # Detailed P&L analysis
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
                    AVG(percentage_change) as avg_pct_change
                FROM trades 
                WHERE action='SELL' AND gain_loss_sol IS NOT NULL
            """)
            
            result = cursor.fetchone()
            stats.update({
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
                'avg_pct_change': result[11] or 0.0
            })
            
            # Win rate calculation
            total_completed = stats['wins'] + stats['losses']
            stats['win_rate'] = (stats['wins'] / total_completed * 100) if total_completed > 0 else 0
            
            # Risk/reward ratio
            if stats['avg_loss'] != 0:
                stats['risk_reward'] = abs(stats['avg_win'] / stats['avg_loss'])
            else:
                stats['risk_reward'] = 0
            
            # Position size analysis
            cursor.execute("""
                SELECT 
                    AVG(amount) as avg_position,
                    MIN(amount) as min_position,
                    MAX(amount) as max_position,
                    SUM(amount) as total_volume
                FROM trades
                WHERE action='BUY'
            """)
            
            pos_result = cursor.fetchone()
            stats.update({
                'avg_position': pos_result[0] or 0.0,
                'min_position': pos_result[1] or 0.0,
                'max_position': pos_result[2] or 0.0,
                'total_volume': pos_result[3] or 0.0
            })
            
            # Time analysis - last 24h
            cursor.execute("""
                SELECT COUNT(*) 
                FROM trades 
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            stats['trades_24h'] = cursor.fetchone()[0]
            
            # Token analysis
            cursor.execute("SELECT COUNT(DISTINCT contract_address) FROM trades")
            stats['unique_tokens'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            print(f"{Fore.RED}Error getting detailed stats: {e}{Style.RESET_ALL}")
            return {}
        finally:
            conn.close()
    
    def get_open_positions(self):
        """Get detailed open positions"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    contract_address,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net_amount,
                    COUNT(CASE WHEN action='BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN action='SELL' THEN 1 END) as sell_count,
                    AVG(CASE WHEN action='BUY' THEN price END) as avg_buy_price,
                    MAX(timestamp) as last_trade_time
                FROM trades
                GROUP BY contract_address
                HAVING net_amount > 0.001
                ORDER BY net_amount DESC
            """
            
            df = pd.read_sql_query(query, conn)
            return df
            
        except Exception as e:
            print(f"{Fore.RED}Error getting open positions: {e}{Style.RESET_ALL}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_token_performance(self):
        """Get performance by token"""
        conn = self.get_connection()
        
        try:
            query = """
                SELECT 
                    contract_address,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE 0 END) as total_bought,
                    SUM(CASE WHEN action='SELL' THEN amount ELSE 0 END) as total_sold,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl,
                    MAX(CASE WHEN action='SELL' THEN percentage_change ELSE 0 END) as best_gain
                FROM trades
                GROUP BY contract_address
                HAVING trade_count > 1
                ORDER BY total_pnl DESC
            """
            
            df = pd.read_sql_query(query, conn)
            return df
            
        except Exception as e:
            print(f"{Fore.RED}Error getting token performance: {e}{Style.RESET_ALL}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_recent_trades(self, limit=10):
        """Get recent trades with full details"""
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
                    percentage_change,
                    price_multiple
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
    
    def display_enhanced(self):
        """Display enhanced monitoring information"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get all data
        balance_info = self.calculate_real_time_balance()
        stats = self.get_detailed_stats()
        token_perf = self.get_token_performance()
        recent_trades = self.get_recent_trades(10)
        open_positions = self.get_open_positions()
        
        # Header
        print(f"{Fore.CYAN}{Back.BLACK}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🤖 ENHANCED SOLANA TRADING BOT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{'='*100}{Style.RESET_ALL}\n")
        
        # Balance Overview - FIXED VERSION
        total_balance = balance_info['total']
        available_balance = balance_info['available']
        in_positions = balance_info['in_positions']
        
        balance_color = Fore.GREEN if total_balance >= self.initial_balance else Fore.RED
        pnl = total_balance - self.initial_balance
        pnl_pct = (total_balance/self.initial_balance - 1)*100
        
        print(f"{Fore.CYAN}💰 BALANCE OVERVIEW:{Style.RESET_ALL}")
        print(f"   Total Balance: {balance_color}{total_balance:.4f} SOL{Style.RESET_ALL}")
        print(f"   ├─ Available: {Fore.WHITE}{available_balance:.4f} SOL{Style.RESET_ALL}")
        print(f"   └─ In Positions: {Fore.YELLOW}{in_positions:.4f} SOL{Style.RESET_ALL} ({balance_info['open_positions_count']} positions)")
        print(f"   Initial: {self.initial_balance:.4f} SOL")
        print(f"   Total P&L: {balance_color}{pnl:+.4f} SOL ({pnl_pct:+.1f}%){Style.RESET_ALL}")
        print(f"   Realized P&L: {balance_color}{stats.get('total_pnl', 0):.4f} SOL{Style.RESET_ALL}\n")
        
        # Open Positions (if any)
        if not open_positions.empty:
            print(f"{Fore.CYAN}📂 OPEN POSITIONS ({len(open_positions)}):{Style.RESET_ALL}")
            for idx, row in open_positions.head(5).iterrows():
                token = row['contract_address'][:8] + "..."
                amount = row['net_amount']
                print(f"   {Fore.YELLOW}{token}{Style.RESET_ALL}: {amount:.4f} SOL")
            if len(open_positions) > 5:
                print(f"   ... and {len(open_positions) - 5} more")
            print()
        
        # Performance Metrics
        print(f"{Fore.CYAN}📊 PERFORMANCE METRICS:{Style.RESET_ALL}")
        win_color = Fore.GREEN if stats.get('win_rate', 0) > 60 else Fore.YELLOW if stats.get('win_rate', 0) > 50 else Fore.RED
        print(f"   Win Rate: {win_color}{stats.get('win_rate', 0):.1f}%{Style.RESET_ALL} ({stats.get('wins', 0)}W / {stats.get('losses', 0)}L)")
        print(f"   Risk/Reward: {stats.get('risk_reward', 0):.2f}:1")
        print(f"   Avg Win: {Fore.GREEN}{stats.get('avg_win', 0):.4f} SOL{Style.RESET_ALL}")
        print(f"   Avg Loss: {Fore.RED}{stats.get('avg_loss', 0):.4f} SOL{Style.RESET_ALL}")
        print(f"   Best Trade: {Fore.GREEN}+{stats.get('best_trade', 0):.4f} SOL ({stats.get('best_pct', 0):.1f}%){Style.RESET_ALL}")
        print(f"   Worst Trade: {Fore.RED}{stats.get('worst_trade', 0):.4f} SOL ({stats.get('worst_pct', 0):.1f}%){Style.RESET_ALL}\n")
        
        # Position Size Analysis
        print(f"{Fore.CYAN}📏 POSITION SIZE ANALYSIS:{Style.RESET_ALL}")
        print(f"   Average: {stats.get('avg_position', 0):.4f} SOL")
        print(f"   Range: {stats.get('min_position', 0):.4f} - {stats.get('max_position', 0):.4f} SOL")
        print(f"   Total Volume: {stats.get('total_volume', 0):.2f} SOL")
        
        # Position size warning based on available balance
        if available_balance < 3.0 and stats.get('max_position', 0) >= 0.1:
            print(f"   {Fore.YELLOW}⚠️  Consider reducing position size for low balance!{Style.RESET_ALL}")
        elif stats.get('avg_position', 0) < 0.1:
            print(f"   {Fore.YELLOW}⚠️  Small positions limiting profits!{Style.RESET_ALL}")
        print()
        
        # Trading Activity
        print(f"{Fore.CYAN}📈 TRADING ACTIVITY:{Style.RESET_ALL}")
        print(f"   Total Trades: {stats.get('total_trades', 0)} ({stats.get('total_buys', 0)} buys, {stats.get('total_sells', 0)} sells)")
        print(f"   Last 24h: {stats.get('trades_24h', 0)} trades")
        print(f"   Unique Tokens: {stats.get('unique_tokens', 0)}\n")
        
        # Top Performing Tokens
        if not token_perf.empty:
            print(f"{Fore.CYAN}🏆 TOP PERFORMING TOKENS:{Style.RESET_ALL}")
            for idx, row in token_perf.head(5).iterrows():
                token = row['contract_address'][:8] + "..."
                pnl_color = Fore.GREEN if row['total_pnl'] > 0 else Fore.RED
                print(f"   {token}: {pnl_color}{row['total_pnl']:.4f} SOL{Style.RESET_ALL} | Best: {row['best_gain']:.1f}% | Trades: {row['trade_count']}")
            print()
        
        # Recent Trades
        print(f"{Fore.CYAN}📋 RECENT TRADES:{Style.RESET_ALL}")
        if recent_trades:
            for trade in recent_trades[:5]:
                trade_id, contract, action, amount, price, timestamp, gain_loss, pct_change, price_mult = trade
                
                action_color = Fore.GREEN if action == 'BUY' else Fore.RED
                action_emoji = "🟢" if action == 'BUY' else "🔴"
                token = contract[:8] + "..." if contract and len(contract) > 12 else contract
                time_str = timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp.split(' ')[1] if ' ' in timestamp else timestamp
                
                print(f"   {action_emoji} {action_color}{action}{Style.RESET_ALL} {amount:.4f} SOL | {token} | {time_str}")
                
                if action == 'SELL' and gain_loss is not None:
                    pnl_color = Fore.GREEN if gain_loss > 0 else Fore.RED
                    pct_color = Fore.GREEN if pct_change > 0 else Fore.RED
                    print(f"      P&L: {pnl_color}{gain_loss:+.4f} SOL{Style.RESET_ALL} ({pct_color}{pct_change:+.1f}%{Style.RESET_ALL})")
        print()
        
        # Insights and Recommendations
        print(f"{Fore.CYAN}💡 INSIGHTS & RECOMMENDATIONS:{Style.RESET_ALL}")
        
        # Balance-specific recommendations
        if available_balance < 1.0:
            print(f"   {Fore.RED}• Very low available balance ({available_balance:.4f} SOL) - reduce position size!{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}• Consider using 10% positions (~{available_balance * 0.1:.4f} SOL each){Style.RESET_ALL}")
        elif available_balance < 3.0:
            print(f"   {Fore.YELLOW}• Low available balance ({available_balance:.4f} SOL) - use percentage sizing{Style.RESET_ALL}")
        
        if stats.get('avg_position', 0) < 0.1 and available_balance > 3.0:
            print(f"   {Fore.YELLOW}• Position sizes too small ({stats.get('avg_position', 0):.4f} SOL) - increase to 0.3-0.5 SOL{Style.RESET_ALL}")
        
        if stats.get('best_pct', 0) > 1000:
            print(f"   {Fore.GREEN}• Found {stats.get('best_pct', 0):.0f}% gain! Bot can identify massive winners{Style.RESET_ALL}")
        
        if stats.get('win_rate', 0) > 70:
            print(f"   {Fore.GREEN}• Excellent {stats.get('win_rate', 0):.1f}% win rate - maintain strategy{Style.RESET_ALL}")
        
        if stats.get('risk_reward', 0) > 3:
            print(f"   {Fore.GREEN}• Strong {stats.get('risk_reward', 0):.1f}:1 risk/reward ratio{Style.RESET_ALL}")
        
        # Calculate potential with larger positions
        if stats.get('avg_position', 0) > 0 and stats.get('total_pnl', 0) != 0:
            scale_factor = 0.4 / stats.get('avg_position', 0)  # Scale to 0.4 SOL positions
            potential_pnl = stats.get('total_pnl', 0) * scale_factor
            print(f"   {Fore.MAGENTA}• With 0.4 SOL positions, realized P&L would be: {potential_pnl:.4f} SOL{Style.RESET_ALL}")
    
    def run(self):
        """Run the enhanced monitor"""
        print(f"{Fore.CYAN}Starting Enhanced Trading Monitor...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        if not self.check_database():
            return
        
        time.sleep(2)
        
        while True:
            try:
                self.display_enhanced()
                time.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = EnhancedTradingMonitor()
    monitor.run()
