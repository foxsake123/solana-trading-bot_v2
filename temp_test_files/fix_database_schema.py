#!/usr/bin/env python3
"""
Fix database schema issues and trading parameter problems
"""
import sqlite3
import os

def check_and_fix_database():
    """Check and fix the database schema"""
    db_path = 'data/db/sol_bot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check trades table schema
        cursor.execute("PRAGMA table_info(trades)")
        columns = [info[1] for info in cursor.fetchall()]
        
        print("Current trades table columns:", columns)
        
        if 'amount' not in columns:
            print("⚠️  'amount' column missing from trades table!")
            
            # Check if there's any data we need to preserve
            cursor.execute("SELECT COUNT(*) FROM trades")
            trade_count = cursor.fetchone()[0]
            
            if trade_count > 0:
                print(f"Found {trade_count} existing trades. Creating backup...")
                # Create backup
                cursor.execute("ALTER TABLE trades RENAME TO trades_backup")
                conn.commit()
            
            # Create new trades table with correct schema
            print("Creating new trades table with correct schema...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT,
                action TEXT,
                amount REAL,
                price REAL,
                timestamp TEXT,
                tx_hash TEXT,
                gain_loss_sol REAL DEFAULT 0.0,
                percentage_change REAL DEFAULT 0.0,
                price_multiple REAL DEFAULT 1.0
            )
            ''')
            conn.commit()
            
            print("✅ Trades table recreated with correct schema")
            
            if trade_count > 0:
                print("Note: Old trades backed up to 'trades_backup' table")
        else:
            print("✅ Trades table has 'amount' column")
        
        # Verify all required columns exist
        required_columns = ['contract_address', 'action', 'amount', 'price', 'timestamp']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"⚠️  Missing columns: {missing}")
        else:
            print("✅ All required columns present")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False
    finally:
        conn.close()
    
    return True

def fix_simplified_solana_trader():
    """Fix the record_trade call in simplified_solana_trader.py"""
    trader_paths = [
        'core/solana/simplified_solana_trader.py',
        'simplified_solana_trader.py',
        'core/blockchain/simplified_solana_trader.py'
    ]
    
    found = False
    for path in trader_paths:
        if os.path.exists(path):
            found = True
            print(f"\nFixing {path}...")
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for the record_trade call with is_simulation parameter
            if 'is_simulation=True' in content or 'is_simulation=' in content:
                # Backup original
                if not os.path.exists(f'{path}.backup'):
                    os.rename(path, f'{path}.backup')
                
                # Remove is_simulation parameter from record_trade calls
                import re
                # This regex will match record_trade calls and remove is_simulation parameter
                content = re.sub(
                    r'(self\.db\.record_trade\([^)]+),\s*is_simulation=[^,\)]+',
                    r'\1',
                    content
                )
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Fixed record_trade calls in {path}")
                print(f"   Removed is_simulation parameter")
                print(f"   Original backed up as {path}.backup")
            else:
                print(f"✅ No is_simulation parameter found in {path}")
            break
    
    if not found:
        print("\n⚠️  Could not find simplified_solana_trader.py")
        print("You may need to manually remove 'is_simulation' parameter from record_trade() calls")

def create_simple_monitor():
    """Create a simple monitor that works with the current schema"""
    monitor_content = '''#!/usr/bin/env python3
"""
Simple trading monitor for the bot
"""
import sqlite3
import time
import os
from datetime import datetime

def get_balance_from_trades(conn):
    """Calculate balance from trades"""
    try:
        cursor = conn.cursor()
        
        # Get all trades
        cursor.execute("SELECT action, amount FROM trades")
        trades = cursor.fetchall()
        
        balance = 10.0  # Starting balance
        for action, amount in trades:
            if amount is None:
                continue
            if action == 'BUY':
                balance -= float(amount)
            elif action == 'SELL':
                balance += float(amount)
        
        return balance
    except Exception as e:
        print(f"Error calculating balance: {e}")
        return 10.0

def monitor():
    """Simple monitoring loop"""
    db_path = 'data/db/sol_bot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    print("\\n🤖 Simple Trading Bot Monitor")
    print("Press Ctrl+C to stop\\n")
    
    while True:
        try:
            conn = sqlite3.connect(db_path)
            
            # Get balance
            balance = get_balance_from_trades(conn)
            
            # Get recent trades
            cursor = conn.cursor()
            cursor.execute("""
                SELECT contract_address, action, amount, timestamp 
                FROM trades 
                ORDER BY id DESC 
                LIMIT 10
            """)
            recent_trades = cursor.fetchall()
            
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Display info
            print(f"\\n📊 Bot Status - {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Balance: {balance:.4f} SOL\\n")
            
            if recent_trades:
                print("📈 Recent Trades:")
                for address, action, amount, timestamp in recent_trades[:5]:
                    if amount is not None:
                        symbol = "🟢" if action == "BUY" else "🔴"
                        print(f"{symbol} {action}: {amount:.4f} SOL - {address[:12]}...")
            else:
                print("No trades yet...")
            
            conn.close()
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\\n\\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()
'''
    
    with open('simple_monitor.py', 'w', encoding='utf-8') as f:
        f.write(monitor_content)
    
    print("\n✅ Created simple_monitor.py")
    print("   This monitor will work with the current database schema")

def main():
    print("🔧 Fixing Database and Trading Issues")
    print("="*60)
    
    # Fix database schema
    print("\n1. Checking database schema...")
    if check_and_fix_database():
        print("✅ Database schema verified/fixed")
    
    # Fix simplified_solana_trader
    print("\n2. Fixing simplified_solana_trader...")
    fix_simplified_solana_trader()
    
    # Create simple monitor
    print("\n3. Creating simple monitor...")
    create_simple_monitor()
    
    print("\n" + "="*60)
    print("✅ Fixes complete!")
    print("\nYou can now:")
    print("1. Run the bot: python start_bot.py simulation")
    print("2. Monitor with: python simple_monitor.py")
    print("\nThe original monitor should also work now if the schema is fixed.")

if __name__ == "__main__":
    main()
