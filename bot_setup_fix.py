#!/usr/bin/env python3
"""
Fixed Bot Setup Script - No Unicode/Emoji Issues
"""
import os
import json
import sys
from datetime import datetime

def create_directories():
    """Create all necessary directories"""
    directories = [
        'core/safety',
        'core/alerts', 
        'data',
        'data/db',
        'logs',
        'models'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Created directory: {directory}")

def fix_safety_state():
    """Create initial safety_state.json file"""
    safety_state = {
        'is_paused': False,
        'pause_reason': '',
        'daily_loss': 0.0,
        'daily_trades': 0,
        'last_reset': datetime.now().date().isoformat()
    }
    
    with open('data/safety_state.json', 'w') as f:
        json.dump(safety_state, f, indent=2)
    
    print("[OK] Created data/safety_state.json")

def create_startup_script():
    """Create an enhanced startup script"""
    
    startup_code = '''#!/usr/bin/env python3
"""
Enhanced Bot Startup Script
Includes all necessary fixes and safety checks
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot components
from config.bot_config import BotConfiguration
from core.trading.trading_bot import TradingBot
from core.data.token_scanner import TokenScanner
from core.analysis.token_analyzer import TokenAnalyzer
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info("="*60)
    logger.info(f"Starting Solana Trading Bot - {mode.upper()} MODE")
    logger.info("="*60)
    
    try:
        # Load configuration
        config = BotConfiguration.load_config(mode)
        
        # Initialize database
        db = Database('data/db/sol_bot.db')
        
        # Initialize components
        token_analyzer = TokenAnalyzer(config, db, BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY'))
        solana_trader = SolanaTrader(
            rpc_url=BotConfiguration.RPC_URL,
            private_key=BotConfiguration.PRIVATE_KEY if mode == 'real' else None,
            simulation_mode=(mode != 'real')
        )
        
        # Initialize token scanner
        token_scanner = TokenScanner(db, solana_trader, token_analyzer)
        
        # Initialize trading bot
        trading_bot = TradingBot(config, db, token_scanner, solana_trader)
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(start_monitoring())
        
        # Start the bot
        logger.info("[LAUNCH] Starting trading bot...")
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("\\nShutdown requested...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if 'trading_bot' in locals():
            trading_bot.running = False
        logger.info("Bot stopped")

async def start_monitoring():
    """Start performance monitoring in background"""
    await asyncio.sleep(60)  # Wait 1 minute before starting monitor
    try:
        from monitoring.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        await monitor.start()
    except Exception as e:
        logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open('start_enhanced_bot.py', 'w', encoding='utf-8') as f:
        f.write(startup_code)
    
    # Make it executable
    os.chmod('start_enhanced_bot.py', 0o755)
    
    print("[OK] Created start_enhanced_bot.py")

def create_monitoring_script():
    """Create a simple monitoring script"""
    
    monitor_code = '''#!/usr/bin/env python3
"""
Simple Trading Performance Monitor
Shows real-time trading statistics
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Initialize colorama
init()

class SimpleMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = 10.0  # SOL
        
    def get_stats(self):
        """Get current trading statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent trades
            cursor.execute("""
                SELECT COUNT(*), SUM(profit_sol), AVG(profit_percentage)
                FROM trades
                WHERE timestamp > datetime('now', '-24 hours')
                AND status = 'closed'
            """)
            trades_24h, profit_24h, avg_profit = cursor.fetchone()
            
            # Get all-time stats
            cursor.execute("""
                SELECT COUNT(*), SUM(profit_sol), 
                       SUM(CASE WHEN profit_sol > 0 THEN 1 ELSE 0 END)
                FROM trades
                WHERE status = 'closed'
            """)
            total_trades, total_profit, winning_trades = cursor.fetchone()
            
            # Get open positions
            cursor.execute("""
                SELECT COUNT(*), SUM(amount_sol)
                FROM trades
                WHERE status = 'open'
            """)
            open_positions, sol_in_positions = cursor.fetchone()
            
            conn.close()
            
            return {
                'trades_24h': trades_24h or 0,
                'profit_24h': profit_24h or 0,
                'avg_profit': avg_profit or 0,
                'total_trades': total_trades or 0,
                'total_profit': total_profit or 0,
                'winning_trades': winning_trades or 0,
                'open_positions': open_positions or 0,
                'sol_in_positions': sol_in_positions or 0
            }
        except Exception as e:
            return None
    
    def display(self):
        """Display monitoring information"""
        os.system('clear' if os.name != 'nt' else 'cls')
        
        stats = self.get_stats()
        if not stats:
            print(f"{Fore.RED}Unable to connect to database{Style.RESET_ALL}")
            return
        
        current_balance = self.initial_balance + stats['total_profit']
        win_rate = (stats['winning_trades'] / max(stats['total_trades'], 1)) * 100
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[BOT] SOLANA TRADING BOT MONITOR{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\\n")
        
        # Account Summary
        print(f"{Fore.GREEN}[ACCOUNT] SUMMARY{Style.RESET_ALL}")
        print(f"Initial Balance: {self.initial_balance:.4f} SOL")
        print(f"Current Balance: {Fore.GREEN if current_balance > self.initial_balance else Fore.RED}{current_balance:.4f} SOL{Style.RESET_ALL}")
        print(f"Total Profit: {Fore.GREEN if stats['total_profit'] > 0 else Fore.RED}{stats['total_profit']:.4f} SOL{Style.RESET_ALL}")
        print(f"ROI: {Fore.GREEN if stats['total_profit'] > 0 else Fore.RED}{(stats['total_profit']/self.initial_balance)*100:.1f}%{Style.RESET_ALL}\\n")
        
        # Trading Stats
        print(f"{Fore.GREEN}[STATS] TRADING STATISTICS{Style.RESET_ALL}")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Win Rate: {Fore.GREEN if win_rate > 50 else Fore.RED}{win_rate:.1f}%{Style.RESET_ALL}")
        print(f"Open Positions: {stats['open_positions']} ({stats['sol_in_positions']:.4f} SOL)\\n")
        
        # 24h Performance
        print(f"{Fore.GREEN}[24H] PERFORMANCE{Style.RESET_ALL}")
        print(f"Trades: {stats['trades_24h']}")
        print(f"Profit: {Fore.GREEN if stats['profit_24h'] > 0 else Fore.RED}{stats['profit_24h']:.4f} SOL{Style.RESET_ALL}")
        print(f"Avg Profit/Trade: {stats['avg_profit']:.1f}%\\n")
        
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run(self):
        """Run the monitor"""
        print("Starting monitor... Press Ctrl+C to exit")
        try:
            while True:
                self.display()
                time.sleep(5)  # Update every 5 seconds
        except KeyboardInterrupt:
            print("\\nMonitor stopped")

if __name__ == "__main__":
    monitor = SimpleMonitor()
    monitor.run()
'''
    
    with open('simple_monitor.py', 'w', encoding='utf-8') as f:
        f.write(monitor_code)
    
    os.chmod('simple_monitor.py', 0o755)
    print("[OK] Created simple_monitor.py")

def create_test_script():
    """Create a test script to verify everything works"""
    
    test_code = '''#!/usr/bin/env python3
"""
Test Script - Verify all components are working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Solana Trading Bot Components...")
print("="*50)

# Test imports
try:
    from config.bot_config import BotConfiguration
    print("[OK] Configuration module loaded")
except Exception as e:
    print(f"[ERROR] Configuration error: {e}")

try:
    from core.data.market_data import BirdeyeAPI
    print("[OK] BirdeyeAPI module loaded")
except Exception as e:
    print(f"[ERROR] Market data error: {e}")

try:
    from core.analysis.token_analyzer import TokenAnalyzer
    analyzer = TokenAnalyzer()
    if hasattr(analyzer, 'analyze'):
        print("[OK] TokenAnalyzer has analyze() method")
    else:
        print("[ERROR] TokenAnalyzer missing analyze() method")
except Exception as e:
    print(f"[ERROR] TokenAnalyzer error: {e}")

try:
    from core.trading.trading_bot import TradingBot
    print("[OK] TradingBot module loaded")
except Exception as e:
    print(f"[ERROR] TradingBot error: {e}")

# Test file structure
required_files = [
    'data/safety_state.json',
    'config/bot_control.json',
    'config/trading_params.json'
]

print("\\nChecking required files:")
for file in required_files:
    if os.path.exists(file):
        print(f"[OK] {file}")
    else:
        print(f"[ERROR] {file} missing")

print("\\n" + "="*50)
print("Test complete!")
'''
    
    with open('test_bot_setup.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    os.chmod('test_bot_setup.py', 0o755)
    print("[OK] Created test_bot_setup.py")

def create_quick_start_script():
    """Create a quick start script"""
    
    quick_start = '''#!/usr/bin/env python3
"""
Quick Start Script for Solana Trading Bot
"""
import subprocess
import sys
import os

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    print("="*60)
    print(f"STARTING SOLANA TRADING BOT - {mode.upper()} MODE")
    print("="*60)
    
    # Check for required files
    if not os.path.exists('data/safety_state.json'):
        print("[!] Running setup first...")
        subprocess.run([sys.executable, 'bot_setup_fix.py'])
    
    # Start the bot
    print("\\n[LAUNCH] Starting bot...")
    subprocess.run([sys.executable, 'start_enhanced_bot.py', mode])

if __name__ == "__main__":
    main()
'''
    
    with open('quick_start.py', 'w', encoding='utf-8') as f:
        f.write(quick_start)
    
    os.chmod('quick_start.py', 0o755)
    print("[OK] Created quick_start.py")

def main():
    """Run all setup and fix operations"""
    print("Solana Trading Bot Setup & Fix Script")
    print("="*50)
    
    # Create directories
    print("\\n1. Creating directories...")
    create_directories()
    
    # Fix safety state
    print("\\n2. Creating safety_state.json...")
    fix_safety_state()
    
    # Create scripts
    print("\\n3. Creating helper scripts...")
    create_startup_script()
    create_monitoring_script()
    create_test_script()
    create_quick_start_script()
    
    print("\\n" + "="*50)
    print("[OK] Setup complete!")
    print("\\nNext steps:")
    print("1. Run: python test_bot_setup.py")
    print("2. Start bot: python quick_start.py simulation")
    print("3. Monitor: python simple_monitor.py")
    print("\\nFor real trading:")
    print("- python quick_start.py real")

if __name__ == "__main__":
    main()
