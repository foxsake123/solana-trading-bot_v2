#!/usr/bin/env python3
"""
Real Trading Setup and Pre-flight Checklist
Run this before switching to real trading
"""

import json
import os
import sys
from datetime import datetime
from colorama import init, Fore, Style
import sqlite3

init()

class RealTradingSetup:
    def __init__(self):
        self.checklist_passed = True
        self.warnings = []
        self.errors = []
        
    def check_wallet_setup(self):
        """Check wallet configuration"""
        print(f"\n{Fore.CYAN}1. WALLET CONFIGURATION CHECK{Style.RESET_ALL}")
        print("-" * 50)
        
        # Check for private key in .env
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.read()
                
            if 'WALLET_PRIVATE_KEY' in env_content and 'your_private_key_here' not in env_content:
                print(f"{Fore.GREEN}✓ Private key configured{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Private key not configured{Style.RESET_ALL}")
                self.errors.append("Set WALLET_PRIVATE_KEY in .env file")
                self.checklist_passed = False
                
            if 'SOLANA_RPC_ENDPOINT' in env_content:
                print(f"{Fore.GREEN}✓ RPC endpoint configured{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠ Using default RPC endpoint{Style.RESET_ALL}")
                self.warnings.append("Consider using a premium RPC endpoint for better performance")
        else:
            print(f"{Fore.RED}✗ .env file not found{Style.RESET_ALL}")
            self.errors.append("Create .env file with wallet configuration")
            self.checklist_passed = False
    
    def check_risk_parameters(self):
        """Verify risk parameters are appropriate for real trading"""
        print(f"\n{Fore.CYAN}2. RISK PARAMETERS CHECK{Style.RESET_ALL}")
        print("-" * 50)
        
        try:
            with open('config/MASTER_CONFIG.json', 'r') as f:
                config = json.load(f)
            
            # Check critical risk parameters
            checks = {
                'stop_loss_percentage': (0.03, 0.10, config['profit_management']['stop_loss_percentage']),
                'max_open_positions': (5, 15, config['position_sizing']['max_open_positions']),
                'slippage_tolerance': (0.05, 0.20, config['execution']['slippage_tolerance']),
            }
            
            for param, (min_val, max_val, current) in checks.items():
                if min_val <= current <= max_val:
                    print(f"{Fore.GREEN}✓ {param}: {current} (OK){Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠ {param}: {current} (outside recommended range {min_val}-{max_val}){Style.RESET_ALL}")
                    self.warnings.append(f"Review {param} setting")
            
            # Position sizing check
            max_pos = config['position_sizing']['max_position_size_sol']
            if max_pos > 1.0:
                print(f"{Fore.YELLOW}⚠ Max position size: {max_pos} SOL (consider starting smaller){Style.RESET_ALL}")
                self.warnings.append("Consider reducing position sizes for initial real trading")
            else:
                print(f"{Fore.GREEN}✓ Max position size: {max_pos} SOL{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}✗ Error reading config: {e}{Style.RESET_ALL}")
            self.errors.append("Fix configuration file")
            self.checklist_passed = False
    
    def check_recent_performance(self):
        """Analyze recent simulation performance"""
        print(f"\n{Fore.CYAN}3. RECENT PERFORMANCE CHECK{Style.RESET_ALL}")
        print("-" * 50)
        
        try:
            conn = sqlite3.connect('data/db/sol_bot.db')
            
            # Check last 7 days performance
            query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                SUM(gain_loss_sol) as total_pnl,
                AVG(gain_loss_sol) as avg_pnl,
                MAX(gain_loss_sol) as best_trade,
                MIN(gain_loss_sol) as worst_trade
            FROM trades
            WHERE action = 'SELL' 
            AND timestamp > datetime('now', '-7 days')
            """
            
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                total, wins, pnl, avg_pnl, best, worst = row
                win_rate = (wins / total) * 100 if total > 0 else 0
                
                print(f"Last 7 days:")
                print(f"  Trades: {total}")
                print(f"  Win Rate: {win_rate:.1f}%")
                print(f"  Total P&L: {pnl:.4f} SOL")
                print(f"  Avg P&L: {avg_pnl:.4f} SOL")
                
                if win_rate < 50:
                    self.warnings.append("Win rate below 50% - review strategy")
                if pnl < 0:
                    self.warnings.append("Negative P&L in last 7 days")
                    
            conn.close()
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Could not analyze performance: {e}{Style.RESET_ALL}")
    
    def create_real_config(self):
        """Create optimized configuration for real trading"""
        print(f"\n{Fore.CYAN}4. CREATING REAL TRADING CONFIG{Style.RESET_ALL}")
        print("-" * 50)
        
        real_config = {
            "mode": "REAL_TRADING",
            "created": datetime.now().isoformat(),
            "position_sizing": {
                "min_position_size_sol": 0.1,  # Start smaller in real trading
                "max_position_size_sol": 0.3,  # Conservative max
                "default_position_size_sol": 0.2,
                "max_open_positions": 10,
                "risk_per_trade_pct": 2.0  # 2% risk per trade
            },
            "risk_management": {
                "daily_loss_limit_sol": 1.0,  # Stop trading after 1 SOL loss
                "max_drawdown_pct": 20.0,     # Circuit breaker at 20% drawdown
                "require_confirmation": True,   # Confirm trades over 0.5 SOL
            },
            "execution": {
                "use_limit_orders": True,      # Use limit orders for better fills
                "max_retry_attempts": 2,        # Fewer retries in real trading
                "priority_fee_lamports": 5000,  # Priority fee for faster execution
            },
            "monitoring": {
                "alert_on_large_loss": True,
                "alert_threshold_sol": 0.5,
                "log_all_trades": True,
                "backup_interval_minutes": 60
            }
        }
        
        # Save real trading config
        with open('config/real_trading_config.json', 'w') as f:
            json.dump(real_config, f, indent=4)
        
        print(f"{Fore.GREEN}✓ Created config/real_trading_config.json{Style.RESET_ALL}")
        
        return real_config
    
    def safety_recommendations(self):
        """Provide safety recommendations"""
        print(f"\n{Fore.CYAN}5. SAFETY RECOMMENDATIONS{Style.RESET_ALL}")
        print("-" * 50)
        
        recommendations = [
            "Start with small position sizes (0.1-0.2 SOL)",
            "Set daily loss limit (e.g., 1 SOL)",
            "Monitor closely for first 24-48 hours",
            "Have emergency stop script ready",
            "Keep 50% of funds in cold wallet",
            "Use a dedicated trading wallet",
            "Enable 2FA on all exchange accounts",
            "Test stop loss execution in real environment",
            "Document your risk management plan"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    def run_checklist(self):
        """Run complete pre-flight checklist"""
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}REAL TRADING PRE-FLIGHT CHECKLIST{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
        
        self.check_wallet_setup()
        self.check_risk_parameters()
        self.check_recent_performance()
        real_config = self.create_real_config()
        self.safety_recommendations()
        
        # Summary
        print(f"\n{Fore.CYAN}SUMMARY{Style.RESET_ALL}")
        print("="*60)
        
        if self.errors:
            print(f"{Fore.RED}ERRORS (Must Fix):{Style.RESET_ALL}")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        if self.warnings:
            print(f"{Fore.YELLOW}WARNINGS (Should Review):{Style.RESET_ALL}")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        if self.checklist_passed and not self.errors:
            print(f"\n{Fore.GREEN}✅ READY FOR REAL TRADING{Style.RESET_ALL}")
            print("\nTo start real trading:")
            print("1. Review and adjust config/real_trading_config.json")
            print("2. Ensure wallet has funds")
            print("3. Run: python start_bot.py real")
            print("4. Monitor closely with: python monitoring/real_trading_monitor.py")
        else:
            print(f"\n{Fore.RED}❌ NOT READY - Fix errors first{Style.RESET_ALL}")
        
        # Create emergency stop script
        self.create_emergency_stop()
    
    def create_emergency_stop(self):
        """Create emergency stop script"""
        emergency_script = '''#!/usr/bin/env python3
"""EMERGENCY STOP - Immediately halt all trading"""
import json
import os
import sys

print("🚨 EMERGENCY STOP ACTIVATED 🚨")

# Stop bot
with open('config/bot_control.json', 'r') as f:
    config = json.load(f)

config['running'] = False
config['emergency_stop'] = True

with open('config/bot_control.json', 'w') as f:
    json.dump(config, f, indent=4)

print("✓ Bot stopped")
print("✓ Review positions manually")
print("✓ Check monitoring/emergency_log.txt")
'''
        
        with open('EMERGENCY_STOP.py', 'w') as f:
            f.write(emergency_script)
        
        print(f"\n{Fore.RED}Created EMERGENCY_STOP.py - Use in case of issues{Style.RESET_ALL}")

if __name__ == "__main__":
    setup = RealTradingSetup()
    setup.run_checklist()
