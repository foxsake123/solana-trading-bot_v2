# check_db_fix_monitor.py
import sqlite3
import json

def check_database():
    """Check actual database structure"""
    conn = sqlite3.connect('data/db/trading_bot.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📊 Database Tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Get columns for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns[:5]:  # Show first 5 columns
            print(f"    • {col[1]} ({col[2]})")
    
    # Check for trades
    if any('trades' in t[0] for t in tables):
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"\n💰 Total Trades: {count}")
    
    # Check tokens table
    if any('tokens' in t[0] for t in tables):
        cursor.execute("SELECT COUNT(*) FROM tokens")
        count = cursor.fetchone()[0]
        print(f"\n🪙 Total Tokens Seen: {count}")
        
        # Show recent tokens
        cursor.execute("""
            SELECT contract_address, symbol, name 
            FROM tokens 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        tokens = cursor.fetchall()
        print("\nRecent tokens:")
        for addr, symbol, name in tokens:
            print(f"  {symbol or 'N/A'}: {addr[:16]}...")
    
    conn.close()
    
    # Check config
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    print(f"\n⚙️ Config Status:")
    print(f"  Min score: {config.get('min_token_score', 'N/A')}")
    print(f"  Position size: {config.get('position_size_min', 0)*100:.0f}-{config.get('position_size_max', 0)*100:.0f}%")
    print(f"  Citadel: {'ON' if config.get('use_citadel_strategy') else 'OFF'}")
    
    # Check if bot is analyzing tokens
    if count == 0:
        print("\n❌ No tokens in database - bot not analyzing properly")
        print("   The analyze_and_trade_token method may not be called")
    else:
        print(f"\n✅ Bot has seen {count} tokens")
        print("   But no trades executed - scoring issue")

if __name__ == "__main__":
    check_database()