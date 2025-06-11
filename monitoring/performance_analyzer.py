import sqlite3
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'databases', 'trading_bot.db')

def initialize_db(conn):
    """Creates tables if they don't exist."""
    conn.execute('''
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
    conn.commit()
    logging.info("Database schema verified by analyzer.")

def calculate_performance_metrics():
    """
    Connects to the database, loads trade data, calculates performance metrics,
    and prints a summary report.
    """
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    try:
        conn = sqlite3.connect(DB_PATH)
        initialize_db(conn) # Ensure tables exist before querying

        query = "SELECT * FROM positions WHERE status = 'closed'"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            logging.info("No closed positions found to analyze.")
            return

        logging.info(f"Analyzing {len(df)} closed trades...")

        # --- Calculation logic (remains the same) ---
        total_trades = len(df)
        wins = df[df['profit_loss_pct'] > 0]
        losses = df[df['profit_loss_pct'] <= 0]
        
        num_wins = len(wins)
        num_losses = len(losses)
        win_rate = (num_wins / total_trades) * 100 if total_trades > 0 else 0

        df['profit_loss_pct'] = df['profit_loss_pct'].astype(float)
        
        gross_profit = wins['profit_loss_pct'].sum()
        gross_loss = abs(losses['profit_loss_pct'].sum())
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_win_pct = wins['profit_loss_pct'].mean() * 100 if num_wins > 0 else 0
        avg_loss_pct = abs(losses['profit_loss_pct'].mean() * 100) if num_losses > 0 else 0
        
        avg_risk_reward_ratio = avg_win_pct / avg_loss_pct if avg_loss_pct > 0 else float('inf')

        # --- Print Report (remains the same) ---
        print("\n--- Trading Performance Report ---")
        print("="*34)
        print(f"Total Trades:         {total_trades}")
        print(f"Winning Trades:       {num_wins}")
        print(f"Losing Trades:        {num_losses}")
        print(f"Win Rate:             {win_rate:.2f}%")
        print("-" * 34)
        print("Profitability:")
        print(f"Profit Factor:        {profit_factor:.2f}")
        print(f"Average Win:          {avg_win_pct:.2f}%")
        print(f"Average Loss:         {avg_loss_pct:.2f}%")
        print(f"Avg. Risk/Reward:     {avg_risk_reward_ratio:.2f} : 1")
        print("="*34)

    except Exception as e:
        logging.error(f"An error occurred during performance analysis: {e}", exc_info=True)

if __name__ == "__main__":
    calculate_performance_metrics()