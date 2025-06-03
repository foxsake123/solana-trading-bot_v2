#!/usr/bin/env python3
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
    
    print("\n🤖 Solana Trading Bot Live Monitor")
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
            print(f"\n🤖 Bot Live Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"💰 Balance: {balance:.4f} SOL (${balance * sol_price:.2f})")
            print(f"📈 SOL Price: ${sol_price:.2f}")
            print("=" * 80)
            
            # Active positions
            print(f"\n💼 Active Positions ({len(positions)}):")
            if not positions.empty:
                for _, pos in positions.iterrows():
                    print(f"💎 {pos['ticker']}: {pos['holding']:.4f} SOL")
            else:
                print("No active positions")
            
            # Recent trades
            print(f"\n📊 Recent Trades:")
            if not recent_trades.empty:
                for _, trade in recent_trades.head(5).iterrows():
                    action_emoji = "🟢" if trade['action'] == "BUY" else "🔴"
                    token = trade['contract_address'][:12] + "..."
                    
                    print(f"{action_emoji} {trade['action']}: {trade['amount_sol']:.4f} SOL - {token}")
            
            conn.close()
            
            # Update every 5 seconds
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n⛔ Monitoring stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_bot()
