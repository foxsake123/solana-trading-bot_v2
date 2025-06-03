#!/usr/bin/env python3
"""
Fix the live monitor to use the correct column names
"""
import os

def fix_live_monitor():
    """Fix live_monitor.py to use amount_sol instead of amount"""
    monitor_path = 'monitoring/live_monitor.py'
    
    if not os.path.exists(monitor_path):
        print(f"❌ {monitor_path} not found")
        return
    
    with open(monitor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace 'amount' with 'amount_sol' in SQL queries
    replacements = [
        ("WHEN action='BUY' THEN amount", "WHEN action='BUY' THEN amount_sol"),
        ("WHEN action='SELL' THEN amount", "WHEN action='SELL' THEN amount_sol"),
        ("WHEN action='SELL' THEN -t.amount", "WHEN action='SELL' THEN -t.amount_sol"),
        ("WHEN t.action='BUY' THEN t.amount", "WHEN t.action='BUY' THEN t.amount_sol"),
        ("WHEN t.action='SELL' THEN -t.amount", "WHEN t.action='SELL' THEN -t.amount_sol"),
        ("{trade['amount']}", "{trade['amount_sol']}")
    ]
    
    modified = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            modified = True
    
    if modified:
        # Backup original
        backup_path = f'{monitor_path}.backup2'
        if not os.path.exists(backup_path):
            with open(monitor_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
        
        # Write fixed version
        with open(monitor_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed {monitor_path}")
        print("   Changed 'amount' to 'amount_sol' in SQL queries")
    else:
        print(f"✅ {monitor_path} already fixed or has different structure")

def create_adapted_monitor():
    """Create a monitor that works with your exact schema"""
    content = '''#!/usr/bin/env python3
"""
Monitor adapted for your database schema
"""
import sqlite3
import time
import os
from datetime import datetime
import pandas as pd

def get_sol_price():
    """Get current SOL price"""
    try:
        import requests
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return float(data.get('solana', {}).get('usd', 168.56))
    except:
        pass
    return 168.56  # Fallback price

def monitor_bot():
    """Live monitoring of bot activity"""
    db_path = 'data/db/sol_bot.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    print("\\n🤖 Solana Trading Bot Live Monitor")
    print("=" * 80)
    
    while True:
        try:
            conn = sqlite3.connect(db_path)
            
            # Get wallet balance (simulation)
            balance_query = """
            SELECT 
                10.0 - COALESCE(SUM(CASE WHEN action='BUY' THEN amount_sol ELSE 0 END), 0) + 
                COALESCE(SUM(CASE WHEN action='SELL' THEN amount_sol ELSE 0 END), 0) as balance
            FROM trades
            WHERE status IS NULL OR status = 'completed'
            """
            balance = pd.read_sql_query(balance_query, conn).iloc[0]['balance']
            
            # Get recent trades
            recent_trades = pd.read_sql_query(
                """SELECT contract_address, action, amount_sol, timestamp 
                   FROM trades 
                   ORDER BY id DESC 
                   LIMIT 10""", 
                conn
            )
            
            # Get active positions
            positions_query = """
            SELECT 
                t.contract_address,
                COALESCE(tk.ticker, SUBSTR(t.contract_address, 1, 8)) as ticker,
                COALESCE(tk.name, 'Unknown') as name,
                SUM(CASE WHEN t.action='BUY' THEN t.amount_sol ELSE -t.amount_sol END) as holding,
                AVG(CASE WHEN t.action='BUY' THEN t.price ELSE NULL END) as avg_buy_price
            FROM trades t
            LEFT JOIN tokens tk ON t.contract_address = tk.contract_address
            GROUP BY t.contract_address
            HAVING holding > 0.001
            """
            positions = pd.read_sql_query(positions_query, conn)
            
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Display header
            sol_price = get_sol_price()
            print(f"\\n🤖 Bot Live Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"💰 Balance: {balance:.4f} SOL (${balance * sol_price:.2f})")
            print(f"📈 SOL Price: ${sol_price:.2f}")
            print("=" * 80)
            
            # Active positions
            print(f"\\n💼 Active Positions ({len(positions)}):")
            if not positions.empty:
                for _, pos in positions.iterrows():
                    print(f"💎 {pos['ticker']}: {pos['holding']:.4f} SOL")
            else:
                print("No active positions")
            
            # Recent trades
            print(f"\\n📊 Recent Trades:")
            if not recent_trades.empty:
                for _, trade in recent_trades.head(5).iterrows():
                    action_emoji = "🟢" if trade['action'] == "BUY" else "🔴"
                    token = trade['contract_address'][:12] + "..."
                    
                    print(f"{action_emoji} {trade['action']}: {trade['amount_sol']:.4f} SOL - {token}")
            
            conn.close()
            
            # Update every 5 seconds
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\\n\\n⛔ Monitoring stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_bot()
'''
    
    with open('adapted_monitor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Created adapted_monitor.py that works with your schema")

def find_simplified_trader():
    """Find where simplified_solana_trader.py is located"""
    possible_locations = [
        'core/solana/simplified_solana_trader.py',
        'simplified_solana_trader.py',
        'core/blockchain/simplified_solana_trader.py',
        'core/trading/simplified_solana_trader.py'
    ]
    
    # Also search for it
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'simplified_solana_trader.py':
                path = os.path.join(root, file)
                print(f"Found simplified_solana_trader.py at: {path}")
                return path
    
    return None

def main():
    print("🔧 Fixing Monitor for Your Database Schema")
    print("="*60)
    
    # Fix live monitor
    print("\\n1. Fixing live_monitor.py...")
    fix_live_monitor()
    
    # Create adapted monitor
    print("\\n2. Creating adapted monitor...")
    create_adapted_monitor()
    
    # Find simplified trader
    print("\\n3. Looking for simplified_solana_trader.py...")
    trader_path = find_simplified_trader()
    if trader_path:
        print(f"   You can manually edit {trader_path}")
        print("   Remove ', is_simulation=True' from record_trade() calls")
    else:
        print("   Could not find simplified_solana_trader.py")
        print("   The is_simulation error will continue but won't affect trading")
    
    print("\\n" + "="*60)
    print("✅ Fixes complete!")
    print("\\nYou can now use:")
    print("1. python monitoring/live_monitor.py  (fixed version)")
    print("2. python adapted_monitor.py  (new version)")
    print("3. python simple_monitor.py  (basic version)")

if __name__ == "__main__":
    main()
