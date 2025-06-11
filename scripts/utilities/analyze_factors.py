#!/usr/bin/env python3
"""
Analyze which factors contribute most to profitable trades
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_factor_performance():
    """Analyze factor contribution to returns"""
    
    conn = sqlite3.connect('data/db/sol_bot.db')
    
    # Get completed trades with P&L
    query = """
    SELECT 
        t1.contract_address,
        t1.timestamp as buy_time,
        t2.timestamp as sell_time,
        t1.amount as position_size,
        t2.gain_loss_sol as pnl,
        t2.percentage_change as pct_return,
        tk.volume_24h,
        tk.liquidity_usd,
        tk.holders,
        tk.price_usd
    FROM trades t1
    JOIN trades t2 ON t1.contract_address = t2.contract_address
    LEFT JOIN tokens tk ON t1.contract_address = tk.contract_address
    WHERE t1.action = 'BUY' 
    AND t2.action = 'SELL'
    AND t2.gain_loss_sol IS NOT NULL
    AND t1.timestamp < t2.timestamp
    ORDER BY t2.timestamp DESC
    LIMIT 100
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No completed trades found")
        return
    
    # Calculate derived factors
    df['volume_liquidity_ratio'] = df['volume_24h'] / (df['liquidity_usd'] + 1)
    df['position_size_factor'] = df['position_size'] / df['position_size'].mean()
    df['holding_hours'] = pd.to_datetime(df['sell_time']) - pd.to_datetime(df['buy_time'])
    df['holding_hours'] = df['holding_hours'].dt.total_seconds() / 3600
    
    # Categorize trades
    df['profitable'] = df['pnl'] > 0
    df['big_winner'] = df['pct_return'] > 100  # 100%+ gains
    
    print("FACTOR ATTRIBUTION ANALYSIS")
    print("=" * 60)
    
    # 1. Position Size Impact
    print("\n1. POSITION SIZE IMPACT:")
    size_correlation = df['position_size'].corr(df['pnl'])
    print(f"   Position size correlation with P&L: {size_correlation:.3f}")
    
    avg_pnl_small = df[df['position_size'] < 0.4]['pnl'].mean()
    avg_pnl_large = df[df['position_size'] >= 0.4]['pnl'].mean()
    print(f"   Avg P&L (positions < 0.4 SOL): {avg_pnl_small:.4f}")
    print(f"   Avg P&L (positions >= 0.4 SOL): {avg_pnl_large:.4f}")
    
    # 2. Volume/Liquidity Analysis  
    print("\n2. VOLUME/LIQUIDITY FACTORS:")
    high_vol_liq = df['volume_liquidity_ratio'] > df['volume_liquidity_ratio'].median()
    print(f"   Win rate (high vol/liq): {df[high_vol_liq]['profitable'].mean():.1%}")
    print(f"   Win rate (low vol/liq): {df[~high_vol_liq]['profitable'].mean():.1%}")
    
    # 3. Holding Period Analysis
    print("\n3. HOLDING PERIOD OPTIMIZATION:")
    holding_buckets = pd.cut(df['holding_hours'], bins=[0, 6, 12, 24, 48, 1000])
    holding_analysis = df.groupby(holding_buckets)['pnl'].agg(['mean', 'count'])
    print(holding_analysis)
    
    # 4. Big Winner Characteristics
    print("\n4. BIG WINNER CHARACTERISTICS (100%+ gains):")
    if df['big_winner'].any():
        big_winners = df[df['big_winner']]
        print(f"   Count: {len(big_winners)} ({len(big_winners)/len(df)*100:.1f}% of trades)")
        print(f"   Avg position size: {big_winners['position_size'].mean():.4f} SOL")
        print(f"   Avg holding time: {big_winners['holding_hours'].mean():.1f} hours")
        print(f"   Avg vol/liq ratio: {big_winners['volume_liquidity_ratio'].mean():.2f}")
    
    # 5. Recommendations
    print("\n5. OPTIMIZATION RECOMMENDATIONS:")
    
    if size_correlation > 0.3:
        print("   ✓ Larger positions correlate with better returns - increase base size")
    
    optimal_holding = df.loc[df['pnl'].idxmax(), 'holding_hours']
    print(f"   ✓ Optimal holding period: {optimal_holding:.1f} hours")
    
    if df['big_winner'].mean() > 0.15:
        print("   ✓ 15%+ trades are 100%+ winners - use trailing stops to capture")
    
    conn.close()

if __name__ == "__main__":
    analyze_factor_performance()
