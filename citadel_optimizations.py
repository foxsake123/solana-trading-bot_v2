#!/usr/bin/env python3
"""
Optimizations for Citadel-Barra strategy based on performance data
"""

import json

def optimize_citadel_parameters():
    """Apply optimizations based on 84% win rate and holding patterns"""
    
    # Load current config
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    # 1. Optimize Alpha Decay based on your holding patterns
    # Your average winning trade holds for ~12-18 hours
    config['alpha_decay_halflife_hours'] = 16  # Reduced from 24
    
    # 2. Adjust Signal Weights based on win rate
    # With 84% win rate, momentum signals are clearly working
    config['signal_weights'] = {
        'momentum': 0.4,        # Increased from 0.3
        'mean_reversion': 0.15, # Reduced from 0.2
        'volume_breakout': 0.25, # Increased from 0.2
        'ml_prediction': 0.2     # Reduced from 0.3 (since other signals are so strong)
    }
    
    # 3. Optimize Risk Parameters for your high win rate
    config['kelly_safety_factor'] = 0.35  # Increased from 0.25 (you can be more aggressive)
    config['max_position_size_pct'] = 8.0  # Increased from 5.0
    config['absolute_max_sol'] = 0.8  # Increased from 0.5
    
    # 4. Tighten Exit Conditions
    # With 362% average gains, we can take profits earlier and compound faster
    config['take_profit_pct'] = 0.3  # 30% take profit (reduced from 50%)
    config['partial_exit_levels'] = [0.3, 1.0, 3.0]  # Take partial profits at 30%, 100%, 300%
    config['partial_exit_percents'] = [0.3, 0.4, 0.3]  # Exit 30%, 40%, keep 30% moonbag
    
    # 5. Add Solana-Specific Factors
    config['solana_factors'] = {
        'network_congestion_weight': -0.1,  # Reduce position during congestion
        'validator_performance_weight': 0.05,
        'sol_dominance_weight': 0.1  # Increase when SOL is strong vs BTC
    }
    
    # 6. Optimize Factor Limits based on your market
    config['factor_limits'] = {
        'market_beta': [-1.0, 3.0],    # Allow higher beta for bull runs
        'volatility': [0, 4.0],        # Solana tokens are volatile
        'momentum': [-1.0, 5.0],       # Strong momentum works in crypto
        'liquidity': [0.3, 10.0]       # Wider range for various tokens
    }
    
    # 7. Dynamic Position Sizing Enhancement
    config['position_size_rules'] = {
        'base_size_pct': 5.0,
        'ml_confidence_multiplier': {
            'high': 1.5,    # >80% confidence
            'medium': 1.0,  # 60-80% confidence  
            'low': 0.7      # <60% confidence
        },
        'momentum_multiplier': {
            'strong': 1.3,  # >50% in 24h
            'medium': 1.0,  # 20-50% in 24h
            'weak': 0.8     # <20% in 24h
        },
        'win_streak_bonus': 0.1  # Add 10% size per consecutive win (max 50%)
    }
    
    # Save updated config
    with open('config/trading_params_optimized.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("✅ Created optimized configuration: config/trading_params_optimized.json")
    print("\nKey optimizations:")
    print("- Alpha decay: 24h → 16h (matches your holding patterns)")
    print("- Momentum weight: 30% → 40% (your strength)")
    print("- Kelly factor: 25% → 35% (leverage your 84% win rate)")
    print("- Added partial exits at 30%, 100%, 300%")
    print("- Position sizes: 5-8% with dynamic adjustments")
    
    return config

def create_factor_analyzer():
    """Create a factor attribution analyzer"""
    
    analyzer_code = '''#!/usr/bin/env python3
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
    print("\\n1. POSITION SIZE IMPACT:")
    size_correlation = df['position_size'].corr(df['pnl'])
    print(f"   Position size correlation with P&L: {size_correlation:.3f}")
    
    avg_pnl_small = df[df['position_size'] < 0.4]['pnl'].mean()
    avg_pnl_large = df[df['position_size'] >= 0.4]['pnl'].mean()
    print(f"   Avg P&L (positions < 0.4 SOL): {avg_pnl_small:.4f}")
    print(f"   Avg P&L (positions >= 0.4 SOL): {avg_pnl_large:.4f}")
    
    # 2. Volume/Liquidity Analysis  
    print("\\n2. VOLUME/LIQUIDITY FACTORS:")
    high_vol_liq = df['volume_liquidity_ratio'] > df['volume_liquidity_ratio'].median()
    print(f"   Win rate (high vol/liq): {df[high_vol_liq]['profitable'].mean():.1%}")
    print(f"   Win rate (low vol/liq): {df[~high_vol_liq]['profitable'].mean():.1%}")
    
    # 3. Holding Period Analysis
    print("\\n3. HOLDING PERIOD OPTIMIZATION:")
    holding_buckets = pd.cut(df['holding_hours'], bins=[0, 6, 12, 24, 48, 1000])
    holding_analysis = df.groupby(holding_buckets)['pnl'].agg(['mean', 'count'])
    print(holding_analysis)
    
    # 4. Big Winner Characteristics
    print("\\n4. BIG WINNER CHARACTERISTICS (100%+ gains):")
    if df['big_winner'].any():
        big_winners = df[df['big_winner']]
        print(f"   Count: {len(big_winners)} ({len(big_winners)/len(df)*100:.1f}% of trades)")
        print(f"   Avg position size: {big_winners['position_size'].mean():.4f} SOL")
        print(f"   Avg holding time: {big_winners['holding_hours'].mean():.1f} hours")
        print(f"   Avg vol/liq ratio: {big_winners['volume_liquidity_ratio'].mean():.2f}")
    
    # 5. Recommendations
    print("\\n5. OPTIMIZATION RECOMMENDATIONS:")
    
    if size_correlation > 0.3:
        print("   ✓ Larger positions correlate with better returns - increase base size")
    
    optimal_holding = df.loc[df['pnl'].idxmax(), 'holding_hours']
    print(f"   ✓ Optimal holding period: {optimal_holding:.1f} hours")
    
    if df['big_winner'].mean() > 0.15:
        print("   ✓ 15%+ trades are 100%+ winners - use trailing stops to capture")
    
    conn.close()

if __name__ == "__main__":
    analyze_factor_performance()
'''
    
    # Write with UTF-8 encoding to handle special characters
    with open('analyze_factors.py', 'w', encoding='utf-8') as f:
        f.write(analyzer_code)
    
    print("✅ Created factor analyzer: analyze_factors.py")

if __name__ == "__main__":
    # Apply optimizations
    optimize_citadel_parameters()
    create_factor_analyzer()
    
    print("\n📊 To apply optimizations:")
    print("1. Review config/trading_params_optimized.json")
    print("2. Copy to config/trading_params.json when ready")
    print("3. Run: python analyze_factors.py")
    print("4. Monitor performance with: python citadel_monitor_simple.py")