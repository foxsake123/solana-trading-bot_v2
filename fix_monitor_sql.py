# fix_monitor_sql.py
import sqlite3

# Check actual column names
conn = sqlite3.connect('data/db/sol_bot.db')
cursor = conn.cursor()

# Check tokens table structure
cursor.execute("PRAGMA table_info(tokens)")
columns = cursor.fetchall()
print("Tokens table columns:")
for col in columns:
    print(f"  {col[1]}")

conn.close()