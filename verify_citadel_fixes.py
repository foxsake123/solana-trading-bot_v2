#!/usr/bin/env python3
"""
Verify Citadel-Barra strategy fixes and performance
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import numpy as np

init()

def verify_citadel_fixes():
    """Comprehensive verification of Citadel-Barra fixes"""
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🏛️  CITADEL-BARRA VERIFICATION REPORT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    # 1. Configuration Check
    print(f"\n📋 CONFIGURATION CHECK:")
    print("-" * 40)
    
    config_ok = True
    try:
        with open('config/trading_params.json', 'r') as f:
            config = json.load(f)
        
        # Check critical settings
        checks = {
            'use_citadel_strategy': (True, config.get('use_citadel_strategy')),
            'absolute_min_sol': (0.4, config.get('absolute_min_sol', 0)),
            'min_position_size_pct': (3.0, config.get('min_position_size_pct', 0)),
            'alpha_decay_halflife_hours': (24, config.get('alpha_decay_halflife_hours', 0))
        }
        
        for param, (expected, actual) in checks.items():
            if actual >= expected:
                print(f"✅ {param}: {actual} (expected >= {expected})")
            else:
                print(f"❌ {param}: {actual} (expected >= {expected})")
                config_ok = False
                
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        config_ok = False
    
    # 2. Recent Position Sizes
    print(f"\n📊 POSITION SIZE VERIFICATION:")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        
        # Get recent trades
        query = """
        SELECT 
            timestamp,
            action,
            amount,
            contract_address
        FROM trades
        WHERE action = 'BUY'
        AND timestamp > datetime('now', '-24 hours')
        ORDER BY timestamp DESC
        LIMIT 20
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            avg_position = df['amount'].mean()
            min_position = df['amount'].min()
            max_position = df['amount'].max()
            
            print(f"Recent Buy Positions (last 24h):")
            print(f"  Average: {avg_position:.4f} SOL")
            print(f"  Min: {min_position:.4f} SOL")
            print(f"  Max: {max_position:.4f} SOL")
            print(f"  Total trades: {len(df)}")
            
            # Check if positions are correct size
            if avg_position >= 0.35:
                print(f"\n✅ Position sizing FIXED! Average {avg_position:.4f} SOL")
            else:
                print(f"\n❌ Position sizing still too small! Average {avg_position:.4f} SOL")
                print("   Expected: 0.4+ SOL average")
            
            # Show last 5 trades
            print(f"\nLast 5 buy trades:")
            for idx, row in df.head(5).iterrows():
                time_str = row['timestamp'].split('T')[1][:8] if 'T' in row['timestamp'] else row['timestamp']
                status = "✅" if row['amount'] >= 0.4 else "❌"
                print(f"  {status} {time_str}: {row['amount']:.4f} SOL - {row['contract_address'][:12]}...")
        else:
            print("No recent trades to analyze")
        
        # 3. Performance Comparison
        print(f"\n💰 PERFORMANCE COMPARISON:")
        print("-" * 40)
        
        # Compare before/after position size fix
        before_query = """
        SELECT 
            AVG(amount) as avg_position,
            COUNT(*) as trade_count,
            SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl
        FROM trades
        WHERE timestamp < datetime('now', '-24 hours')
        AND timestamp > datetime('now', '-7 days')
        """
        
        after_query = """
        SELECT 
            AVG(amount) as avg_position,
            COUNT(*) as trade_count,
            SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl
        FROM trades
        WHERE timestamp > datetime('now', '-24 hours')
        """
        
        before = pd.read_sql_query(before_query, conn).iloc[0]
        after = pd.read_sql_query(after_query, conn).iloc[0]
        
        if before['trade_count'] > 0 and after['trade_count'] > 0:
            print(f"Before Fix (7d ago - 24h ago):")
            print(f"  Avg Position: {before['avg_position']:.4f} SOL")
            print(f"  Total P&L: {before['total_pnl']:.4f} SOL")
            print(f"  Trades: {before['trade_count']}")
            
            print(f"\nAfter Fix (last 24h):")
            print(f"  Avg Position: {after['avg_position']:.4f} SOL")
            print(f"  Total P&L: {after['total_pnl']:.4f} SOL")
            print(f"  Trades: {after['trade_count']}")
            
            if before['avg_position'] > 0:
                position_increase = after['avg_position'] / before['avg_position']
                print(f"\n📈 Position Size Increase: {position_increase:.1f}x")
                
                if after['total_pnl'] is not None and before['total_pnl'] is not None:
                    pnl_increase = after['total_pnl'] / max(before['total_pnl'], 0.0001)
                    print(f"📈 P&L Increase: {pnl_increase:.1f}x")
        
        # 4. Factor Analysis
        print(f"\n🔬 FACTOR ANALYSIS:")
        print("-" * 40)
        
        # Analyze holding periods for alpha decay optimization
        holding_query = """
        SELECT 
            contract_address,
            MIN(timestamp) as entry_time,
            MAX(timestamp) as exit_time,
            COUNT(*) as trade_count,
            SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as pnl
        FROM trades
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY contract_address
        HAVING trade_count > 1
        """
        
        holdings = pd.read_sql_query(holding_query, conn)
        
        if not holdings.empty:
            holdings['entry_time'] = pd.to_datetime(holdings['entry_time'])
            holdings['exit_time'] = pd.to_datetime(holdings['exit_time'])
            holdings['holding_hours'] = (holdings['exit_time'] - holdings['entry_time']).dt.total_seconds() / 3600
            
            avg_holding = holdings['holding_hours'].mean()
            median_holding = holdings['holding_hours'].median()
            
            print(f"Holding Period Analysis:")
            print(f"  Average: {avg_holding:.1f} hours")
            print(f"  Median: {median_holding:.1f} hours")
            
            # Recommend alpha decay adjustment
            if median_holding < 18:
                print(f"\n💡 Recommendation: Reduce alpha_decay_halflife_hours from 24 to {int(median_holding * 1.5)}")
                print("   Positions are exiting faster than alpha decay assumes")
            elif median_holding > 36:
                print(f"\n💡 Recommendation: Increase alpha_decay_halflife_hours from 24 to {int(median_holding * 0.75)}")
                print("   Positions are holding longer than alpha decay assumes")
                
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # 5. Balance Check
    print(f"\n💳 BALANCE VERIFICATION:")
    print("-" * 40)
    
    try:
        # Check if balance fix is needed
        with open('core/blockchain/solana_client.py', 'r') as f:
            content = f.read()
            
        if 'self.wallet_balance = 1.0' in content:
            print("❌ Balance hardcoded to 1.0 SOL - needs fix!")
            print("   Apply the balance tracking fix from artifacts")
        elif 'starting_simulation_balance' in content:
            print("✅ Balance tracking appears to be fixed")
        else:
            print("⚠️  Cannot determine balance tracking status")
            
    except Exception as e:
        print(f"Error checking balance code: {e}")
    
    # 6. Summary and Next Steps
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📋 SUMMARY & NEXT STEPS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    if config_ok and avg_position >= 0.35:
        print(f"\n{Fore.GREEN}✅ Citadel-Barra strategy appears to be working correctly!{Style.RESET_ALL}")
        print("\nNext optimizations to consider:")
        print("1. Monitor factor attribution after 50-100 trades")
        print("2. Adjust signal weights based on performance")
        print("3. Fine-tune alpha decay based on holding patterns")
        print("4. Consider partial exits at 2x, 5x, 10x levels")
    else:
        print(f"\n{Fore.RED}❌ Issues detected - please fix before continuing{Style.RESET_ALL}")
        print("\nRequired fixes:")
        if not config_ok:
            print("1. Update config/trading_params.json with correct values")
        if avg_position < 0.35:
            print("2. Ensure position sizing override is working")
        print("3. Apply balance tracking fix to solana_client.py")

if __name__ == "__main__":
    verify_citadel_fixes()