#!/usr/bin/env python3
"""
integrate_enhancements.py - Quick setup for enhanced trading bot
"""

import os
import json
import shutil
from datetime import datetime

def create_directories():
    """Create required directories"""
    dirs = [
        'core/analysis',
        'core/strategies', 
        'core/data',
        'ml/training',
        'config'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✅ Directories created")

def setup_config():
    """Setup configuration files"""
    
    # Twitter config
    twitter_config = {
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", ""),
        "tracked_accounts": [
            "ansemtrades",
            "thecryptoskull", 
            "solbuckets",
            "solanalegend"
        ],
        "bullish_threshold": 0.7,
        "bearish_threshold": 0.3
    }
    
    # Update trading_params.json
    try:
        with open('config/trading_params.json', 'r') as f:
            params = json.load(f)
    except:
        params = {}
    
    params.update({
        'twitter': twitter_config,
        'use_partial_exits': True,
        'use_jupiter': True,
        'ml_auto_retrain': True
    })
    
    with open('config/trading_params.json', 'w') as f:
        json.dump(params, f, indent=2)
    
    # Create optimized_strategy_v2.json
    partial_exits = {
        "partial_exits": {
            "enabled": True,
            "levels": [
                {"profit_pct": 0.5, "exit_pct": 0.3},
                {"profit_pct": 1.0, "exit_pct": 0.4},
                {"profit_pct": 2.0, "exit_pct": 0.3}
            ],
            "trailing_stop": {
                "enabled": True,
                "activation": 3.0,
                "distance": 0.2
            }
        }
    }
    
    with open('config/optimized_strategy_v2.json', 'w') as f:
        json.dump(partial_exits, f, indent=2)
    
    print("✅ Configuration files created")

def update_database():
    """Add new tables for enhanced features"""
    import sqlite3
    
    conn = sqlite3.connect('data/db/sol_bot.db')
    cursor = conn.cursor()
    
    # Partial exits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partial_exits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_address TEXT,
        symbol TEXT,
        buy_timestamp TIMESTAMP,
        amount REAL,
        price REAL,
        profit_sol REAL,
        reason TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Sentiment tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentiment_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_symbol TEXT,
        sentiment_score REAL,
        confidence REAL,
        signal TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database tables created")

def install_packages():
    """Install required packages"""
    packages = [
        "transformers",
        "tweepy",
        "torch"
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        os.system(f"pip install {package}")

def main():
    print("🚀 ENHANCED TRADING BOT INTEGRATION")
    print("="*50)
    
    # 1. Create directories
    create_directories()
    
    # 2. Setup config
    setup_config()
    
    # 3. Update database
    update_database()
    
    # 4. Copy artifact files to project
    print("\n📋 Files to manually add:")
    print("1. Copy TwitterSentimentAnalyzer → core/analysis/sentiment_analyzer.py")
    print("2. Copy PartialExitManager → core/strategies/partial_exits.py") 
    print("3. Copy EnhancedTradingBot → enhanced_trading_bot.py")
    
    # 5. Update start script
    print("\n✏️  Update start_bot.py:")
    print("   Replace: from core.trading.trading_bot import TradingBot")
    print("   With: from enhanced_trading_bot import EnhancedTradingBot")
    
    print("\n✅ Integration ready!")
    print("\nNext steps:")
    print("1. Add TWITTER_BEARER_TOKEN to .env")
    print("2. Run: python start_bot.py simulation")
    print("3. Monitor: python citadel_performance_monitor.py")

if __name__ == "__main__":
    main()
