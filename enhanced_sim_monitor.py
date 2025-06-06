#!/usr/bin/env python3
"""Enhanced simulation monitor with detailed statistics"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import statistics

init()

class EnhancedSimMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.initial_balance = 10.0  # Adjust if different
        
    def get_detailed_stats(self):
        """Get comprehensive simulation statistics"""
        conn = sqlite3.connect('data/db/sol_bot.db')
        cursor = conn.cursor()
        
        stats = {}
        
        # Get all trades
        cursor.execute("""
            SELECT action, amount, price, timestamp, contract_address, 
                   gain_loss_sol, percentage_change
            FROM trades
            ORDER BY timestamp DESC
        """)
        all_trades = cursor.fetchall()
        
        # Basic counts
        buys = [t for t in all_trades if t[0] == 'BUY']
        sells = [t for t in all_trades if t[0] == 'SELL']
        
        stats['total_buys'] = len(buys)
        stats['total_sells'] = len(sells)
        
        # Calculate current balance
        balance = self.initial_balance
        for trade in reversed(all_trades):  # Process in chronological order
            if trade[0] == 'BUY':
                balance -= trade[1]
            else:
                balance += trade[1]
        stats['current_balance'] = balance
        
        # Position analysis
        positions = {}
        for trade in all_trades:
            token = trade[4]
            if token not in positions:
                positions[token] = {'buys': 0, 'sells': 0, 'net': 0}
            
            if trade[0] == 'BUY':
                positions[token]['buys'] += trade[1]
                positions[token]['net'] += trade[1]
            else:
                positions[token]['sells'] += trade[1]
                positions[token]['net'] -= trade[1]
        
        stats['open_positions'] = sum(1 for p in positions.values() if p['net'] > 0.001)
        stats['unique_tokens'] = len(positions)
        
        # Completed trades analysis
        completed = [t for t in all_trades if t[0] == 'SELL' and t[5] is not None]
        stats['completed_trades'] = len(completed)
        
        if completed:
            # P&L analysis
            pnls = [t[5] for t in completed]
            pcts = [t[6] for t in completed if t[6] is not None]
            
            stats['total_pnl'] = sum(pnls)
            stats['avg_pnl'] = statistics.mean(pnls) if pnls else 0
            stats['best_trade'] = max(pnls) if pnls else 0
            stats['worst_trade'] = min(pnls) if pnls else 0
            stats['wins'] = sum(1 for p in pnls if p > 0)
            stats['losses'] = sum(1 for p in pnls if p < 0)
            stats['breakeven'] = sum(1 for p in pnls if p == 0)
            
            if pcts:
                stats['avg_pct_change'] = statistics.mean(pcts)
                stats['best_pct'] = max(pcts)
                stats['worst_pct'] = min(pcts)
        else:
            stats['total_pnl'] = 0
            stats['avg_pnl'] = 0
            stats['wins'] = 0
            stats['losses'] = 0
            stats['breakeven'] = 0
        
        # Trading frequency
        if all_trades:
            first_trade_time = datetime.fromisoformat(all_trades[-1][3].replace('+00:00', ''))
            last_trade_time = datetime.fromisoformat(all_trades[0][3].replace('+00:00', ''))
            time_span = (last_trade_time - first_trade_time).total_seconds() / 3600  # hours
            
            if time_span > 0:
                stats['trades_per_hour'] = len(all_trades) / time_span
            else:
                stats['trades_per_hour'] = 0
        
        # Position sizes
        if buys:
            buy_amounts = [t[1] for t in buys]
            stats['avg_position_size'] = statistics.mean(buy_amounts)
            stats['min_position_size'] = min(buy_amounts)
            stats['max_position_size'] = max(buy_amounts)
        
        conn.close()
        return stats
    
    def display_monitor(self):
        """Display enhanced monitoring information"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        stats = self.get_detailed_stats()
        
        # Header
        print(f"{Fore.CYAN}{Back.BLACK}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚀 ENHANCED SIMULATION MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{'='*80}{Style.RESET_ALL}\n")
        
        # Running time
        runtime = datetime.now() - self.start_time
        print(f"Running for: {str(runtime).split('.')[0]}\n")
        
        # Balance section
        balance_change = stats['current_balance'] - self.initial_balance
        balance_pct = (balance_change / self.initial_balance) * 100
        balance_color = Fore.GREEN if balance_change >= 0 else Fore.RED
        
        print(f"{Fore.WHITE}💰 BALANCE{Style.RESET_ALL}")
        print(f"Current:  {stats['current_balance']:.4f} SOL")
        print(f"Initial:  {self.initial_balance:.4f} SOL")
        print(f"Change:   {balance_color}{balance_change:+.4f} SOL ({balance_pct:+.1f}%){Style.RESET_ALL}\n")
        
        # Trading activity
        print(f"{Fore.WHITE}📊 TRADING ACTIVITY{Style.RESET_ALL}")
        print(f"Total Trades:     {stats['total_buys'] + stats['total_sells']}")
        print(f"Buys:            {stats['total_buys']}")
        print(f"Sells:           {stats['total_sells']}")
        print(f"Open Positions:   {stats['open_positions']}")
        print(f"Unique Tokens:    {stats['unique_tokens']}")
        print(f"Trades/Hour:      {stats.get('trades_per_hour', 0):.1f}\n")
        
        # Position sizing
        if 'avg_position_size' in stats:
            print(f"{Fore.WHITE}📏 POSITION SIZES{Style.RESET_ALL}")
            print(f"Average:  {stats['avg_position_size']:.4f} SOL")
            print(f"Min:      {stats['min_position_size']:.4f} SOL")
            print(f"Max:      {stats['max_position_size']:.4f} SOL\n")
        
        # Performance metrics
        print(f"{Fore.WHITE}📈 PERFORMANCE METRICS{Style.RESET_ALL}")
        print(f"Completed Trades: {stats['completed_trades']}")
        
        if stats['completed_trades'] > 0:
            total = stats['wins'] + stats['losses'] + stats['breakeven']
            if total > 0:
                win_rate = (stats['wins'] / total) * 100
            else:
                win_rate = 0
            
            win_color = Fore.GREEN if win_rate > 60 else Fore.YELLOW if win_rate > 50 else Fore.RED
            pnl_color = Fore.GREEN if stats['total_pnl'] > 0 else Fore.RED
            
            print(f"Win Rate:         {win_color}{win_rate:.1f}%{Style.RESET_ALL} ({stats['wins']}W / {stats['losses']}L / {stats['breakeven']}BE)")
            print(f"Total P&L:        {pnl_color}{stats['total_pnl']:.4f} SOL{Style.RESET_ALL}")
            print(f"Average P&L:      {stats['avg_pnl']:.4f} SOL")
            
            if 'avg_pct_change' in stats:
                print(f"Avg % Change:     {stats['avg_pct_change']:.1f}%")
            
            print(f"Best Trade:       {Fore.GREEN}+{stats['best_trade']:.4f} SOL{Style.RESET_ALL}")
            print(f"Worst Trade:      {Fore.RED}{stats['worst_trade']:.4f} SOL{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No completed trades yet...{Style.RESET_ALL}")
        
        # Issues detection
        print(f"\n{Fore.WHITE}🔍 DIAGNOSTICS{Style.RESET_ALL}")
        issues = []
        
        if stats['completed_trades'] > 0 and stats['total_pnl'] == 0:
            issues.append(f"{Fore.RED}⚠️  All trades showing 0 P&L - price tracking issue{Style.RESET_ALL}")
        
        if stats.get('avg_position_size', 0) < 0.1:
            issues.append(f"{Fore.YELLOW}⚠️  Position sizes very small (<0.1 SOL){Style.RESET_ALL}")
        
        if stats.get('trades_per_hour', 0) < 5:
            issues.append(f"{Fore.YELLOW}⚠️  Low trading frequency (<5 trades/hour){Style.RESET_ALL}")
        
        if stats['breakeven'] == stats['completed_trades'] and stats['completed_trades'] > 0:
            issues.append(f"{Fore.RED}⚠️  All trades breaking even - simulation issue{Style.RESET_ALL}")
        
        if issues:
            for issue in issues:
                print(issue)
        else:
            print(f"{Fore.GREEN}✅ No issues detected{Style.RESET_ALL}")
        
        # ML readiness
        print(f"\n{Fore.WHITE}🤖 ML TRAINING READINESS{Style.RESET_ALL}")
        target_trades = 50
        if stats['completed_trades'] < target_trades:
            print(f"{Fore.YELLOW}Need {target_trades - stats['completed_trades']} more completed trades{Style.RESET_ALL}")
            
            if stats.get('trades_per_hour', 0) > 0:
                eta_hours = (target_trades - stats['completed_trades']) / (stats.get('trades_per_hour', 1) / 2)  # Assuming 50% are sells
                print(f"ETA: ~{eta_hours:.1f} hours at current rate")
        else:
            print(f"{Fore.GREEN}✅ Ready for ML training!{Style.RESET_ALL}")
            print("Run: python simple_ml_training.py")
        
        # Recommendations
        print(f"\n{Fore.WHITE}💡 RECOMMENDATIONS{Style.RESET_ALL}")
        
        if stats['total_pnl'] == 0 and stats['completed_trades'] > 5:
            print("1. Restart simulation - price tracking seems broken")
            print("2. Check if bot is using real market data")
        elif stats.get('avg_position_size', 0) < 0.2:
            print("1. Increase position sizes in trading_params.json")
            print("2. Run: python fix_simulation_params.py")
        elif stats.get('trades_per_hour', 0) < 10:
            print("1. Lower ML confidence threshold for more trades")
            print("2. Check if bot is finding enough opportunities")
        
        print(f"\n{Fore.CYAN}Refreshing in 10 seconds... (Ctrl+C to stop){Style.RESET_ALL}")
    
    def run(self):
        """Run the monitor"""
        try:
            while True:
                self.display_monitor()
                time.sleep(10)
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Monitor stopped by user{Style.RESET_ALL}")
            
            # Show final summary
            stats = self.get_detailed_stats()
            print(f"\n{Fore.CYAN}FINAL SUMMARY{Style.RESET_ALL}")
            print(f"Total Runtime: {str(datetime.now() - self.start_time).split('.')[0]}")
            print(f"Total Trades: {stats['total_buys'] + stats['total_sells']}")
            print(f"Completed Trades: {stats['completed_trades']}")
            print(f"Final Balance: {stats['current_balance']:.4f} SOL")

if __name__ == "__main__":
    print(f"{Fore.CYAN}Starting Enhanced Simulation Monitor...{Style.RESET_ALL}\n")
    monitor = EnhancedSimMonitor()
    monitor.run()
