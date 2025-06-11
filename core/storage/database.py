# core/storage/database.py (Updated with new methods)

import aiosqlite
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class Database:
    """Handles all database operations for the trading bot."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        # The database setup is now called from main after object creation
        # using an explicit initialize method.

    async def initialize(self):
        """Initializes the database connection and creates tables if they don't exist."""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            # Use Row factory to get results as dictionaries
            self.conn.row_factory = aiosqlite.Row
            
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_address TEXT NOT NULL,
                    symbol TEXT,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    position_size_usd REAL,
                    status TEXT NOT NULL,
                    profit_loss_pct REAL,
                    open_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    close_timestamp DATETIME,
                    reason TEXT
                )
            ''')
            
            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_address TEXT UNIQUE NOT NULL,
                    symbol TEXT,
                    name TEXT,
                    initial_score REAL,
                    added_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await self.conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id INTEGER,
                    final_score REAL,
                    factors TEXT,
                    analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(token_id) REFERENCES tokens(id)
                )
            ''')

            await self.conn.commit()
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise

    async def add_token(self, **kwargs):
        """Adds a new token to the database."""
        # Basic implementation, can be expanded
        sql = 'INSERT OR IGNORE INTO tokens (contract_address, symbol, name, initial_score) VALUES (?, ?, ?, ?)'
        await self.conn.execute(sql, (kwargs['contract_address'], kwargs['symbol'], kwargs['name'], kwargs['initial_score']))
        await self.conn.commit()

    async def get_token(self, address: str) -> Optional[aiosqlite.Row]:
        """Retrieves a single token by its contract address."""
        cursor = await self.conn.execute("SELECT * FROM tokens WHERE contract_address = ?", (address,))
        return await cursor.fetchone()

    async def get_all_tokens(self) -> List[aiosqlite.Row]:
        """Retrieves all tokens from the database."""
        cursor = await self.conn.execute("SELECT * FROM tokens")
        return await cursor.fetchall()
    
    async def add_position(self, trade_details: Dict[str, Any]) -> int:
        """Adds a new open position to the database."""
        sql = '''INSERT INTO positions (contract_address, symbol, entry_price, position_size_usd, status, reason)
                 VALUES (?, ?, ?, ?, 'open', ?)'''
        cursor = await self.conn.execute(sql, (
            trade_details['contract_address'], trade_details['symbol'],
            trade_details['entry_price'], trade_details['position_size_usd'],
            trade_details['reason']
        ))
        await self.conn.commit()
        return cursor.lastrowid

    async def update_position(self, position_id: int, exit_price: float, pnl_pct: float):
        """Updates a position to closed status."""
        sql = "UPDATE positions SET status = 'closed', exit_price = ?, profit_loss_pct = ?, close_timestamp = CURRENT_TIMESTAMP WHERE id = ?"
        await self.conn.execute(sql, (exit_price, pnl_pct, position_id))
        await self.conn.commit()
        return True

    async def get_position(self, position_id: int) -> Optional[aiosqlite.Row]:
        """Retrieves a single position by its ID."""
        cursor = await self.conn.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
        return await cursor.fetchone()
    
    async def add_analysis_record(self, result: Dict[str, Any]):
        # Basic implementation
        pass

    # --- NEW METHODS TO FIX THE ERROR ---

    async def get_open_positions(self) -> List[aiosqlite.Row]:
        """Retrieves all positions with the status 'open'."""
        logger.debug("Fetching open positions from DB.")
        cursor = await self.conn.execute("SELECT * FROM positions WHERE status = 'open'")
        rows = await cursor.fetchall()
        return rows

    async def close(self):
        """Closes the database connection if it's open."""
        if self.conn:
            await self.conn.close() # Use await here
            logger.info("Database connection closed.")