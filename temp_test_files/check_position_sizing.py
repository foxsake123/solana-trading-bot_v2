#!/usr/bin/env python3
"""
Diagnose and fix position sizing issues
"""

import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def check_position_sizing():
    """Check current position sizing configuration and recent trades"""
    
    print("="*60)
    print("POSITION SIZING DIAGNOSTIC")
    print("="*60)
    
    # 1. Check configuration
    print("\n1. CHECKING CONFIGURATION:")
    print("-"*40)
    
    try:
        with open('config/trading_params.json', 'r') as f:
            config = json.load(f)
        
        print("Position Size Settings:")
        print(f"  Min position %: {config.get('min_position_size_pct', 'NOT SET')}%")
        print(f"  Default position %: {config.get('default_position_size_pct', 'NOT SET')}%")
        print(f"  Max position %: {config.get('max_position_size_pct', 'NOT SET')}%")
        print(f"  Absolute min SOL: {config.get('absolute_min_sol', 'NOT SET')}")
        print(f"  Absolute max SOL: {config.get('absolute_max_sol', 'NOT SET')}")
        
        # Check if these are reasonable
        min_pct = config.get('min_position_size_pct', 0)
        abs_min = config.get('absolute_min_sol', 0)
        
        if min_pct < 3:
            print(f"\n⚠️  WARNING: min_position_size_pct is too low: {min_pct}%")
            print("   Recommended: 3-5%")
        
        if abs_min < 0.3:
            print(f"\n⚠️  WARNING: absolute_min_sol is too low: {abs_min} SOL")
            print("   Recommended: 0.3-0.5 SOL")
            
    except Exception as e:
        print(f"Error reading config: {e}")
    
    # 2. Check recent trades
    print("\n\n2. CHECKING RECENT TRADES:")
    print("-"*40)
    
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        
        # Get recent buy trades
        query = """
        SELECT 
            contract_address,
            action,
            amount,
            price,
            timestamp
        FROM trades
        WHERE action = 'BUY'
        ORDER BY timestamp DESC
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            print(f"Last 10 buy trades:")
            print(f"Average position size: {df['amount'].mean():.4f} SOL")
            print(f"Min position size: {df['amount'].min():.4f} SOL")
            print(f"Max position size: {df['amount'].max():.4f} SOL")
            
            # Show each trade
            print("\nRecent positions:")
            for _, row in df.iterrows():
                timestamp = row['timestamp'].split('T')[1].split('.')[0] if 'T' in row['timestamp'] else row['timestamp']
                print(f"  {timestamp}: {row['amount']:.4f} SOL")
            
            # Check if positions are too small
            if df['amount'].mean() < 0.1:
                print(f"\n❌ CRITICAL: Average position size is WAY TOO SMALL!")
                print(f"   Current: {df['amount'].mean():.4f} SOL")
                print(f"   Should be: 0.3-0.5 SOL minimum")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking trades: {e}")
    
    # 3. Calculate potential profits
    print("\n\n3. PROFIT POTENTIAL ANALYSIS:")
    print("-"*40)
    
    try:
        # Assuming 84% win rate and 362% average gain
        current_avg_position = 0.08  # Your current average
        recommended_position = 0.4   # Recommended size
        
        win_rate = 0.84
        avg_gain = 3.62  # 362%
        avg_loss = 0.05  # 5% loss
        
        # Expected value per trade
        current_ev = current_avg_position * (win_rate * (avg_gain - 1) - (1-win_rate) * avg_loss)
        recommended_ev = recommended_position * (win_rate * (avg_gain - 1) - (1-win_rate) * avg_loss)
        
        print(f"Expected Value per Trade:")
        print(f"  Current ({current_avg_position} SOL positions): {current_ev:.4f} SOL")
        print(f"  Recommended ({recommended_position} SOL positions): {recommended_ev:.4f} SOL")
        print(f"  Potential increase: {recommended_ev/current_ev:.1f}x")
        
        print(f"\nWith 50 trades per day:")
        print(f"  Current daily profit: {current_ev * 50:.2f} SOL")
        print(f"  Potential daily profit: {recommended_ev * 50:.2f} SOL")
        
    except Exception as e:
        print(f"Error calculating potential: {e}")
    
    # 4. Provide fix
    print("\n\n4. RECOMMENDED FIX:")
    print("-"*40)
    
    print("Add this to your enhanced_trading_bot.py in _execute_trade method:")
    print("")
    print("# FORCE MINIMUM POSITION SIZE")
    print("min_position_sol = 0.4  # Force 0.4 SOL minimum")
    print("amount_sol = max(amount_sol, min_position_sol)")
    print("")
    print("Or update config/trading_params.json:")
    print(json.dumps({
        "absolute_min_sol": 0.4,
        "min_position_size_pct": 4.0,
        "default_position_size_pct": 5.0,
        "max_position_size_pct": 6.0
    }, indent=2))

if __name__ == "__main__":
    check_position_sizing()