#!/usr/bin/env python3
"""
Clear fake trades from database
"""
import sqlite3
from datetime import datetime

def clear_fake_trades():
    """Remove all fake trades with simulated transaction IDs"""
    
    print("🧹 Clearing fake trades from database...")
    
    conn = sqlite3.connect('data/db/sol_bot.db')
    cursor = conn.cursor()
    
    # First, let's see what we're about to delete
    cursor.execute("""
        SELECT COUNT(*) 
        FROM trades 
        WHERE tx_hash LIKE 'SIM_%' 
        OR tx_hash LIKE 'REAL_%'
        OR tx_hash = 'simulated'
    """)
    
    fake_count = cursor.fetchone()[0]
    
    if fake_count == 0:
        print("✅ No fake trades found in database!")
        conn.close()
        return
    
    print(f"Found {fake_count} fake trades to remove")
    
    # Show a sample of what we're deleting
    cursor.execute("""
        SELECT action, amount, contract_address, timestamp, tx_hash
        FROM trades 
        WHERE tx_hash LIKE 'SIM_%' 
        OR tx_hash LIKE 'REAL_%'
        OR tx_hash = 'simulated'
        LIMIT 5
    """)
    
    print("\nSample of trades to be deleted:")
    for trade in cursor.fetchall():
        print(f"  {trade[0]} {trade[1]:.4f} SOL - {trade[4]}")
    
    # Ask for confirmation
    response = input(f"\nDelete all {fake_count} fake trades? (y/n): ")
    
    if response.lower() == 'y':
        # Delete the fake trades
        cursor.execute("""
            DELETE FROM trades 
            WHERE tx_hash LIKE 'SIM_%' 
            OR tx_hash LIKE 'REAL_%'
            OR tx_hash = 'simulated'
        """)
        
        conn.commit()
        print(f"✅ Successfully deleted {cursor.rowcount} fake trades")
        
        # Show remaining trade count
        cursor.execute("SELECT COUNT(*) FROM trades")
        remaining = cursor.fetchone()[0]
        print(f"📊 Remaining trades in database: {remaining}")
        
    else:
        print("❌ Deletion cancelled")
    
    conn.close()
    
    print("\n✅ Database cleaned!")
    print("\nNext steps:")
    print("1. Add at least 0.5 SOL to your wallet")
    print("2. Verify bot configuration is correct")
    print("3. Start with real-time monitoring")

if __name__ == "__main__":
    clear_fake_trades()
