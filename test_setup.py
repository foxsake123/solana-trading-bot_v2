# test_setup.py - Test if everything is set up correctly
import os
import json

print("🔍 Checking Solana Trading Bot v2 Setup...")
print("=" * 50)

# Check directories
directories = ['config', 'core', 'ml', 'monitoring', 'data/db']
for dir in directories:
    exists = "✅" if os.path.exists(dir) else "❌"
    print(f"{exists} Directory: {dir}")

# Check essential files
files = [
    'main.py',
    'requirements.txt',
    '.env',
    'config/trading_params.json',
    'scripts/setup_database.py'
]
for file in files:
    exists = "✅" if os.path.exists(file) else "❌"
    print(f"{exists} File: {file}")

# Check database
db_exists = "✅" if os.path.exists('data/db/sol_bot.db') else "❌"
print(f"{db_exists} Database: data/db/sol_bot.db")

print("\n✅ Setup check complete!")
