# monitor_trades.py
"""
Monitor why trades aren't executing in real-time
"""

import json
import sqlite3
import time
from datetime import datetime

def monitor_bot_activity():
    """Check bot status and why trades aren't happening"""
    
    print("🔍 TRADE EXECUTION MONITOR")
    print("="*50)
    
    # 1. Check config
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    print(f"Min score threshold: {config.get('min_token_score', 0.5)}")
    print(f"Citadel enabled: {config.get('use_citadel_strategy', False)}")
    print(f"Position size: {config.get('position_size_min', 0.03)*100:.0f}-{config.get('position_size_max', 0.05)*100:.0f}%")
    
    # 2. Check database for analyzed tokens
    conn = sqlite3.connect('data/db/trading_bot.db')
    cursor = conn.cursor()
    
    # Recent token analyses
    cursor.execute("""
        SELECT contract_address, safety_score, buy_recommendation, 
               datetime(analysis_time) as time
        FROM token_analysis 
        ORDER BY analysis_time DESC 
        LIMIT 10
    """)
    
    analyses = cursor.fetchall()
    print(f"\n📊 Recent Token Analyses: {len(analyses)}")
    
    for addr, score, buy_rec, time in analyses[:5]:
        print(f"  {addr[:8]}... Score: {score:.2f} Buy: {buy_rec}")
    
    # 3. Check trades
    cursor.execute("SELECT COUNT(*) FROM trades")
    trade_count = cursor.fetchone()[0]
    print(f"\n💰 Total Trades Executed: {trade_count}")
    
    # 4. Recommendations
    print("\n🚨 ISSUES FOUND:")
    
    if config.get('use_citadel_strategy', False):
        print("  ❌ Citadel strategy is blocking trades (returns 0 alpha)")
        print("     Fix: Run 'python simple_trading_fix.py'")
    
    if not analyses or all(score < config.get('min_token_score', 0.5) for _, score, _, _ in analyses):
        print("  ❌ No tokens meeting score threshold")
        print(f"     Current threshold: {config.get('min_token_score', 0.5)}")
        print("     Fix: Lower min_token_score in config")
    
    if trade_count == 0:
        print("  ❌ No trades executed yet")
        print("     Fix: Run 'python force_trades.py' to modify analyzer")
    
    conn.close()

if __name__ == "__main__":
    monitor_bot_activity()