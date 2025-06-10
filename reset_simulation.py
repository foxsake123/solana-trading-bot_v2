#!/usr/bin/env python3
"""
Reset simulation database to start fresh
"""
import sqlite3
import os
import json

def reset_simulation():
    """Reset the simulation database"""
    
    print("Resetting simulation database...")
    
    # 1. Clear the database
    db_path = 'data/db/sol_bot.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Clear each table
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"  - Cleared table: {table_name}")
        
        conn.commit()
        conn.close()
    
    # 2. Reset wallet balance in solana_client.py
    solana_file = 'core/blockchain/solana_client.py'
    if os.path.exists(solana_file):
        with open(solana_file, 'r') as f:
            content = f.read()
        
        # Make sure _starting_balance is set properly
        if "self._starting_balance" not in content and "self.wallet_balance = config.get('starting_simulation_balance'" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "self.wallet_balance = config.get('starting_simulation_balance'" in line:
                    # Add _starting_balance initialization
                    indent = len(line) - len(line.lstrip())
                    new_line = ' ' * indent + "self._starting_balance = self.wallet_balance"
                    if i + 1 < len(lines) and new_line not in lines[i + 1]:
                        lines.insert(i + 1, new_line)
                        print("  - Fixed _starting_balance initialization")
                        break
            
            content = '\n'.join(lines)
            with open(solana_file, 'w') as f:
                f.write(content)
    
    # 3. Reset bot_control.json
    config_file = 'config/bot_control.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Reset balance
        config['starting_simulation_balance'] = 10.0
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"  - Reset starting balance to 10.0 SOL")
    
    print("\\nSimulation reset complete!")
    print("You can now start fresh with 10 SOL")

if __name__ == "__main__":
    reset_simulation()
