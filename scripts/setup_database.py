# scripts/setup_database.py - Database setup and migration script

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_tables(conn):
    """Create all necessary tables"""
    cursor = conn.cursor()
    
    # Tokens table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tokens (
        contract_address TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        name TEXT,
        decimals INTEGER DEFAULT 9,
        price_usd REAL,
        volume_24h REAL,
        liquidity_usd REAL,
        market_cap REAL,
        holders INTEGER,
        price_change_1h REAL,
        price_change_6h REAL,
        price_change_24h REAL,
        safety_score REAL,
        last_updated TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Positions table with proper tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        position_id TEXT PRIMARY KEY,
        contract_address TEXT NOT NULL,
        symbol TEXT NOT NULL,
        entry_time TIMESTAMP NOT NULL,
        entry_price REAL NOT NULL,
        entry_amount_sol REAL NOT NULL,
        entry_amount_tokens REAL NOT NULL,
        current_price REAL,
        current_value_sol REAL,
        stop_loss REAL,
        take_profit REAL,
        trailing_stop_active BOOLEAN DEFAULT 0,
        highest_price REAL,
        pnl_sol REAL DEFAULT 0,
        pnl_percent REAL DEFAULT 0,
        status TEXT DEFAULT 'open',
        exit_time TIMESTAMP,
        exit_price REAL,
        exit_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_address) REFERENCES tokens(contract_address)
    )
    ''')
    
    # Trades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id TEXT,
        contract_address TEXT NOT NULL,
        action TEXT NOT NULL,
        amount_sol REAL NOT NULL,
        amount_tokens REAL NOT NULL,
        price REAL NOT NULL,
        tx_hash TEXT,
        fee_sol REAL DEFAULT 0,
        slippage REAL DEFAULT 0,
        status TEXT DEFAULT 'completed',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (position_id) REFERENCES positions(position_id),
        FOREIGN KEY (contract_address) REFERENCES tokens(contract_address)
    )
    ''')
    
    # Wallet balance tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wallet_balance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        balance_sol REAL NOT NULL,
        balance_usd REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Performance metrics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_date DATE NOT NULL,
        total_trades INTEGER DEFAULT 0,
        winning_trades INTEGER DEFAULT 0,
        losing_trades INTEGER DEFAULT 0,
        total_pnl_sol REAL DEFAULT 0,
        total_pnl_usd REAL DEFAULT 0,
        win_rate REAL DEFAULT 0,
        avg_win_pct REAL DEFAULT 0,
        avg_loss_pct REAL DEFAULT 0,
        sharpe_ratio REAL DEFAULT 0,
        max_drawdown_pct REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ML predictions tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ml_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_address TEXT NOT NULL,
        prediction_type TEXT NOT NULL,
        prediction_value REAL NOT NULL,
        confidence REAL NOT NULL,
        features TEXT,
        actual_outcome REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contract_address) REFERENCES tokens(contract_address)
    )
    ''')
    
    # Alerts and notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        details TEXT,
        acknowledged BOOLEAN DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens_last_updated ON tokens(last_updated)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)')
    
    conn.commit()
    print("✅ Tables created successfully")

def migrate_from_v1(old_db_path, new_db_path):
    """Migrate data from v1 database"""
    if not os.path.exists(old_db_path):
        print("⚠️  No v1 database found to migrate")
        return
    
    print("🔄 Migrating data from v1...")
    
    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect(new_db_path)
    
    try:
        # Migrate tokens
        old_cursor = old_conn.cursor()
        old_cursor.execute("SELECT * FROM tokens")
        tokens = old_cursor.fetchall()
        
        if tokens:
            # Get column names
            columns = [description[0] for description in old_cursor.description]
            
            # Insert into new database
            for token in tokens:
                token_dict = dict(zip(columns, token))
                
                # Map old columns to new structure
                new_conn.execute('''
                    INSERT OR REPLACE INTO tokens 
                    (contract_address, symbol, name, price_usd, volume_24h, 
                     liquidity_usd, market_cap, holders, safety_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    token_dict.get('contract_address'),
                    token_dict.get('ticker', token_dict.get('symbol', 'UNKNOWN')),
                    token_dict.get('name', ''),
                    token_dict.get('price_usd', 0),
                    token_dict.get('volume_24h', 0),
                    token_dict.get('liquidity_usd', 0),
                    token_dict.get('mcap', token_dict.get('market_cap', 0)),
                    token_dict.get('holders', 0),
                    token_dict.get('safety_score', 0),
                    token_dict.get('last_updated', datetime.now().isoformat())
                ))
            
            print(f"✅ Migrated {len(tokens)} tokens")
        
        # Migrate trades
        old_cursor.execute("SELECT * FROM trades")
        trades = old_cursor.fetchall()
        
        if trades:
            columns = [description[0] for description in old_cursor.description]
            
            for trade in trades:
                trade_dict = dict(zip(columns, trade))
                
                new_conn.execute('''
                    INSERT INTO trades 
                    (contract_address, action, amount_sol, amount_tokens, 
                     price, tx_hash, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_dict.get('contract_address'),
                    trade_dict.get('action'),
                    trade_dict.get('amount', 0),
                    0,  # amount_tokens not in v1
                    trade_dict.get('price', 0),
                    trade_dict.get('tx_hash', ''),
                    trade_dict.get('timestamp')
                ))
            
            print(f"✅ Migrated {len(trades)} trades")
        
        new_conn.commit()
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
    finally:
        old_conn.close()
        new_conn.close()

def main():
    """Main setup function"""
    print("🚀 Setting up Solana Trading Bot v2 Database")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    os.makedirs('data/db', exist_ok=True)
    
    # Database path
    db_path = 'data/db/sol_bot.db'
    
    # Check if database already exists
    if os.path.exists(db_path):
        response = input("⚠️  Database already exists. Recreate? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing database.")
            
            # Check for migration
            old_db_path = '../solana-trading-bot/data/sol_bot.db'
            if os.path.exists(old_db_path):
                response = input("Found v1 database. Migrate data? (y/N): ")
                if response.lower() == 'y':
                    migrate_from_v1(old_db_path, db_path)
            return
        else:
            os.remove(db_path)
            print("Removed old database.")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    
    # Create tables
    create_tables(conn)
    
    # Check for v1 database to migrate
    old_db_path = '../solana-trading-bot/data/sol_bot.db'
    if os.path.exists(old_db_path):
        response = input("Found v1 database. Migrate data? (y/N): ")
        if response.lower() == 'y':
            conn.close()
            migrate_from_v1(old_db_path, db_path)
            conn = sqlite3.connect(db_path)
    
    # Insert initial data
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO performance_metrics 
        (metric_date, total_trades, winning_trades, losing_trades)
        VALUES (DATE('now'), 0, 0, 0)
    ''')
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database setup complete!")
    print(f"📁 Database location: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    main()
