#!/usr/bin/env python3
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
    
    print("\n🤖 Simple Trading Bot Monitor")
    print("Press Ctrl+C to stop\n")
    
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
            print(f"\n📊 Bot Status - {datetime.now().strftime('%H:%M:%S')}")
            print(f"💰 Balance: {balance:.4f} SOL\n")
            
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
            print("\n\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()
