# real_trading_monitor.py

import asyncio
import sqlite3
import os
import json
from datetime import datetime
from colorama import init, Fore, Style
import pandas as pd

# Initialize colorama for colored output
init()

class RealTradingMonitor:
    """Monitor for real trading mode with safety checks and alerts"""
    
    def __init__(self, db_path='data/sol_bot.db', config_path='bot_control.json'):
        self.db_path = db_path
        self.config_path = config_path
        self.initial_balance = None
        self.alert_thresholds = {
            'max_loss_pct': 5.0,      # Alert if loss exceeds 5%
            'position_size_pct': 5.0,  # Alert if position > 5% of balance
            'min_balance_sol': 0.1,    # Alert if balance < 0.1 SOL
        }
        
    def get_config(self):
        """Get current bot configuration"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def check_trading_mode(self):
        """Verify if bot is in real trading mode"""
        config = self.get_config()
        return not config.get('simulation_mode', True)
    
    def get_wallet_info(self):
        """Get wallet balance and info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest wallet balance
        cursor.execute("""
            SELECT balance_sol, balance_usd, timestamp 
            FROM wallet_balance 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'balance_sol': result[0],
                'balance_usd': result[1],
                'last_update': result[2]
            }
        return None
    
    def get_positions(self):
        """Get current open positions"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                position_id,
                contract_address,
                symbol,
                entry_time,
                entry_price,
                entry_amount_sol,
                current_price,
                pnl_percent,
                pnl_sol,
                status
            FROM positions
            WHERE status = 'open'
            ORDER BY entry_time DESC
        """
        positions = pd.read_sql_query(query, conn)
        conn.close()
        return positions
    
    def get_recent_trades(self, limit=10):
        """Get recent trades"""
        conn = sqlite3.connect(self.db_path)
        query = f"""
            SELECT 
                timestamp,
                action,
                contract_address,
                amount,
                price,
                tx_hash
            FROM trades
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        trades = pd.read_sql_query(query, conn)
        conn.close()
        return trades
    
    def check_alerts(self, wallet_info, positions):
        """Check for alert conditions"""
        alerts = []
        
        # Check minimum balance
        if wallet_info['balance_sol'] < self.alert_thresholds['min_balance_sol']:
            alerts.append({
                'type': 'LOW_BALANCE',
                'message': f"Balance below minimum: {wallet_info['balance_sol']:.4f} SOL",
                'severity': 'HIGH'
            })
        
        # Check for large losses
        if self.initial_balance:
            loss_pct = ((self.initial_balance - wallet_info['balance_sol']) / 
                       self.initial_balance * 100)
            if loss_pct > self.alert_thresholds['max_loss_pct']:
                alerts.append({
                    'type': 'MAX_LOSS',
                    'message': f"Loss exceeds threshold: {loss_pct:.2f}%",
                    'severity': 'HIGH'
                })
        
        # Check position sizes
        if not positions.empty:
            for _, pos in positions.iterrows():
                pos_size_pct = (pos['entry_amount_sol'] / wallet_info['balance_sol'] * 100)
                if pos_size_pct > self.alert_thresholds['position_size_pct']:
                    alerts.append({
                        'type': 'LARGE_POSITION',
                        'message': f"Large position: {pos['symbol']} - {pos_size_pct:.1f}% of balance",
                        'severity': 'MEDIUM'
                    })
        
        return alerts
    
    def display_status(self):
        """Display current trading status"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}🤖 REAL TRADING MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        # Check if in real trading mode
        if not self.check_trading_mode():
            print(f"{Fore.RED}⚠️  WARNING: Bot is in SIMULATION mode!{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ REAL TRADING MODE ACTIVE{Style.RESET_ALL}\n")
        
        # Get wallet info
        wallet = self.get_wallet_info()
        if wallet:
            print(f"{Fore.WHITE}💰 Wallet Balance:")
            print(f"   SOL: {wallet['balance_sol']:.4f}")
            print(f"   USD: ${wallet['balance_usd']:.2f}")
            print(f"   Updated: {wallet['last_update']}{Style.RESET_ALL}\n")
            
            # Set initial balance if not set
            if self.initial_balance is None:
                self.initial_balance = wallet['balance_sol']
        
        # Get positions
        positions = self.get_positions()
        print(f"{Fore.WHITE}📊 Open Positions: {len(positions)}")
        
        if not positions.empty:
            for _, pos in positions.iterrows():
                color = Fore.GREEN if pos['pnl_percent'] > 0 else Fore.RED
                print(f"   {pos['symbol']}: {pos['entry_amount_sol']:.4f} SOL | "
                      f"PnL: {color}{pos['pnl_percent']:.2f}%{Style.RESET_ALL}")
        else:
            print("   No open positions")
        
        # Recent trades
        print(f"\n{Fore.WHITE}📈 Recent Trades:")
        trades = self.get_recent_trades(5)
        if not trades.empty:
            for _, trade in trades.iterrows():
                action_color = Fore.GREEN if trade['action'] == 'BUY' else Fore.RED
                print(f"   {action_color}{trade['action']}{Style.RESET_ALL}: "
                      f"{trade['amount']:.4f} SOL | "
                      f"{trade['timestamp']}")
        
        # Check alerts
        alerts = self.check_alerts(wallet, positions)
        if alerts:
            print(f"\n{Fore.RED}🚨 ALERTS:")
            for alert in alerts:
                severity_color = Fore.RED if alert['severity'] == 'HIGH' else Fore.YELLOW
                print(f"   {severity_color}{alert['type']}: {alert['message']}{Style.RESET_ALL}")
    
    async def run(self):
        """Run the monitor"""
        print(f"{Fore.CYAN}Starting Real Trading Monitor...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        while True:
            try:
                self.display_status()
                await asyncio.sleep(5)  # Update every 5 seconds
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Monitor stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                await asyncio.sleep(5)


# Safety check script before switching to real trading
def pre_flight_check():
    """Run safety checks before enabling real trading"""
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}PRE-FLIGHT CHECK FOR REAL TRADING")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    checks = []
    
    # Check 1: Config file exists
    if os.path.exists('bot_control.json'):
        checks.append(('Config file exists', True))
    else:
        checks.append(('Config file exists', False))
    
    # Check 2: Database exists
    if os.path.exists('data/sol_bot.db'):
        checks.append(('Database exists', True))
    else:
        checks.append(('Database exists', False))
    
    # Check 3: Wallet configuration
    with open('bot_control.json', 'r') as f:
        config = json.load(f)
    
    if config.get('real_wallet_address'):
        checks.append(('Wallet address configured', True))
    else:
        checks.append(('Wallet address configured', False))
    
    # Check 4: Risk parameters
    safe_params = (
        config.get('max_investment_per_token', 1.0) <= 0.1 and
        config.get('stop_loss_percentage', 0) >= 0.05 and
        config.get('max_open_positions', 10) <= 5
    )
    checks.append(('Risk parameters safe', safe_params))
    
    # Check 5: ML model exists
    ml_exists = os.path.exists('data/ml_model.pkl')
    checks.append(('ML model trained', ml_exists))
    
    # Display results
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print(f"{Fore.GREEN}✅ {check_name}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ {check_name}{Style.RESET_ALL}")
            all_passed = False
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    if all_passed:
        print(f"{Fore.GREEN}✅ All checks passed! Ready for real trading.{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}To enable real trading:")
        print(f"1. Set 'simulation_mode' to false in bot_control.json")
        print(f"2. Ensure your wallet has sufficient SOL")
        print(f"3. Start with small amounts to test")
        print(f"4. Monitor closely using: python real_trading_monitor.py{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Some checks failed. Fix issues before enabling real trading.{Style.RESET_ALL}")
    
    return all_passed


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Run pre-flight check
        pre_flight_check()
    else:
        # Run monitor
        monitor = RealTradingMonitor()
        asyncio.run(monitor.run())
