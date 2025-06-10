#!/usr/bin/env python3
"""
Optimized Trading Strategy for Solana Bot
Based on 84.9% win rate performance
"""
import json
import os

def create_optimized_configs():
    """Create optimized configuration files"""
    
    # 1. Enhanced Trading Parameters
    trading_params = {
        "strategy_name": "Enhanced Citadel-Barra with Partial Exits",
        "version": "2.0",
        
        # Position Sizing (Optimized for higher profits)
        "position_sizing": {
            "min_position_size_pct": 4.0,      # Increased from 3%
            "default_position_size_pct": 5.0,   # Increased from 4%
            "max_position_size_pct": 7.0,       # Increased from 5%
            "absolute_min_sol": 0.4,            # Minimum 0.4 SOL per trade
            "absolute_max_sol": 2.0,            # Maximum 2 SOL per trade
            "use_kelly_criterion": True,        # Dynamic sizing
            "kelly_fraction": 0.25              # Conservative Kelly
        },
        
        # Entry Criteria (More selective)
        "entry_criteria": {
            "min_score": 0.75,                  # Higher threshold
            "min_volume_24h": 100000,           # $100k minimum volume
            "min_liquidity": 50000,             # $50k minimum liquidity
            "min_holders": 500,                 # At least 500 holders
            "max_price_impact": 2.0,            # Max 2% price impact
            "required_confirmations": 2         # Multiple signal confirmation
        },
        
        # Partial Exit Strategy (NEW)
        "partial_exits": {
            "enabled": True,
            "levels": [
                {"profit_pct": 20, "exit_pct": 25},   # Take 25% at 20% profit
                {"profit_pct": 50, "exit_pct": 25},   # Take 25% at 50% profit
                {"profit_pct": 100, "exit_pct": 25},  # Take 25% at 100% profit
                {"profit_pct": 200, "exit_pct": 25}   # Final 25% rides
            ],
            "trail_final_position": True,
            "trail_activation": 150,            # Start trailing at 150%
            "trail_distance": 20                # 20% trailing stop
        },
        
        # Risk Management
        "risk_management": {
            "stop_loss_pct": 8.0,               # Slightly wider stop
            "time_stop_hours": 48,              # Exit after 48 hours
            "max_open_positions": 8,            # Fewer, larger positions
            "max_portfolio_risk": 25.0,         # Max 25% at risk
            "use_volatility_stops": True,
            "volatility_multiplier": 2.5
        },
        
        # Token Filtering (Quality focus)
        "token_filters": {
            "blacklist_keywords": ["SCAM", "RUG", "TEST", "FAKE"],
            "min_social_score": 0.6,
            "require_verified": False,          # Many good tokens unverified
            "max_concentration": 50.0,          # Max 50% held by top wallet
            "min_transaction_count": 1000       # Active trading required
        },
        
        # ML Integration
        "ml_settings": {
            "enabled": True,
            "min_confidence": 0.7,
            "feature_importance_threshold": 0.1,
            "retrain_interval_days": 7,
            "min_samples_for_training": 1000
        },
        
        # Citadel-Barra Enhancements
        "citadel_barra": {
            "use_factor_models": True,
            "alpha_decay_halflife": 24,
            "factor_weights": {
                "momentum": 0.35,               # Increased momentum weight
                "mean_reversion": 0.15,
                "volume_breakout": 0.25,
                "ml_prediction": 0.25
            },
            "max_factor_exposure": 2.5,
            "risk_parity_weight": 0.3
        }
    }
    
    # 2. Market Making Configuration
    market_making = {
        "enabled": False,  # Can enable for additional profits
        "spreads": {
            "default": 0.5,                     # 0.5% spread
            "volatile": 1.0,                    # 1% in volatile conditions
            "min_spread": 0.3,
            "max_spread": 2.0
        },
        "inventory_management": {
            "target_inventory": 0.5,            # 50% of position size
            "rebalance_threshold": 0.2,
            "max_inventory_sol": 5.0
        }
    }
    
    # 3. Advanced Features
    advanced_features = {
        "twitter_sentiment": {
            "enabled": True,
            "weight": 0.15,
            "min_mentions": 10,
            "influencer_list": [
                "ansemtrades",
                "jasonpf",
                "solanafloor"
            ]
        },
        
        "whale_tracking": {
            "enabled": True,
            "min_whale_size": 100000,           # $100k minimum
            "follow_whale_trades": True,
            "whale_confidence_boost": 0.1
        },
        
        "dex_aggregation": {
            "enabled": True,
            "use_jupiter": True,
            "max_slippage": 1.0,
            "check_multiple_routes": True
        },
        
        "smart_routing": {
            "enabled": True,
            "preferred_dexes": ["Raydium", "Orca", "Serum"],
            "avoid_low_liquidity": True,
            "split_large_orders": True
        }
    }
    
    # 4. Performance Targets
    performance_targets = {
        "daily_profit_target": 5.0,             # 5 SOL daily target
        "weekly_profit_target": 30.0,           # 30 SOL weekly
        "max_daily_loss": 2.0,                  # Stop at 2 SOL loss
        "target_win_rate": 85.0,                # Maintain 85%+ win rate
        "target_sharpe_ratio": 2.5,
        "compound_profits": True,
        "reinvest_percentage": 50.0             # Reinvest 50% of profits
    }
    
    # Save configurations
    configs = {
        "config/trading_params_optimized.json": trading_params,
        "config/market_making.json": market_making,
        "config/advanced_features.json": advanced_features,
        "config/performance_targets.json": performance_targets
    }
    
    for filepath, config in configs.items():
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created {filepath}")
    
    # Create combined config
    combined_config = {
        **trading_params,
        "market_making": market_making,
        "advanced_features": advanced_features,
        "performance_targets": performance_targets
    }
    
    with open("config/strategy_v2_complete.json", 'w') as f:
        json.dump(combined_config, f, indent=2)
    print("✅ Created config/strategy_v2_complete.json")

def create_strategy_monitor():
    """Create a strategy-specific monitoring script"""
    
    monitor_code = '''#!/usr/bin/env python3
"""
Strategy Performance Monitor
Tracks partial exits and advanced metrics
"""
import sqlite3
import json
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import pandas as pd

init()

class StrategyMonitor:
    def __init__(self):
        self.db_path = 'data/db/sol_bot.db'
        
    def analyze_partial_exits(self):
        """Analyze partial exit performance"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT 
            token_symbol,
            entry_price,
            exit_price,
            profit_percentage,
            amount_sol,
            timestamp
        FROM trades
        WHERE status = 'closed'
        AND profit_percentage > 0
        ORDER BY timestamp DESC
        LIMIT 50
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return None
            
        # Calculate metrics
        avg_profit = df['profit_percentage'].mean()
        total_profit_sol = df['amount_sol'].sum() * (df['profit_percentage'].mean() / 100)
        
        # Identify multi-exit trades
        multi_exits = df.groupby('token_symbol').size()
        multi_exit_tokens = multi_exits[multi_exits > 1]
        
        return {
            'avg_profit': avg_profit,
            'total_profit_sol': total_profit_sol,
            'multi_exit_count': len(multi_exit_tokens),
            'best_performer': df.loc[df['profit_percentage'].idxmax()]
        }
    
    def display_analysis(self):
        """Display strategy analysis"""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 STRATEGY PERFORMANCE ANALYSIS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\\n")
        
        analysis = self.analyze_partial_exits()
        if not analysis:
            print("No data available yet")
            return
            
        print(f"{Fore.GREEN}PARTIAL EXIT PERFORMANCE:{Style.RESET_ALL}")
        print(f"Average Profit: {analysis['avg_profit']:.1f}%")
        print(f"Total SOL Gained: {analysis['total_profit_sol']:.4f}")
        print(f"Multi-Exit Trades: {analysis['multi_exit_count']}\\n")
        
        print(f"{Fore.GREEN}BEST PERFORMER:{Style.RESET_ALL}")
        best = analysis['best_performer']
        print(f"Token: {best['token_symbol']}")
        print(f"Profit: {best['profit_percentage']:.1f}%")
        print(f"Amount: {best['amount_sol']:.4f} SOL")

if __name__ == "__main__":
    monitor = StrategyMonitor()
    monitor.display_analysis()
'''
    
    with open('strategy_monitor.py', 'w') as f:
        f.write(monitor_code)
    
    os.chmod('strategy_monitor.py', 0o755)
    print("✅ Created strategy_monitor.py")

def create_quick_commands():
    """Create quick command scripts"""
    
    # Start simulation
    with open('start_simulation.sh', 'w') as f:
        f.write('''#!/bin/bash
echo "Starting Solana Trading Bot in SIMULATION mode..."
python start_enhanced_bot.py simulation
''')
    os.chmod('start_simulation.sh', 0o755)
    
    # Start real trading
    with open('start_real.sh', 'w') as f:
        f.write('''#!/bin/bash
echo "⚠️  WARNING: Starting REAL TRADING mode!"
echo "Press Ctrl+C within 5 seconds to cancel..."
sleep 5
python start_enhanced_bot.py real
''')
    os.chmod('start_real.sh', 0o755)
    
    # Monitor performance
    with open('monitor.sh', 'w') as f:
        f.write('''#!/bin/bash
python simple_monitor.py
''')
    os.chmod('monitor.sh', 0o755)
    
    print("✅ Created quick command scripts")

def main():
    """Create all optimized configurations"""
    print("Creating Optimized Strategy Configuration...")
    print("="*50)
    
    create_optimized_configs()
    create_strategy_monitor()
    create_quick_commands()
    
    print("\\n" + "="*50)
    print("✅ Strategy optimization complete!")
    print("\\nKey improvements:")
    print("- Partial exit strategy (take profits at 20%, 50%, 100%, 200%)")
    print("- Larger position sizes (4-7% vs 3-5%)")
    print("- Higher entry threshold (0.75 score)")
    print("- Advanced features ready (Twitter, whale tracking)")
    print("\\nQuick commands:")
    print("- ./start_simulation.sh - Start in simulation mode")
    print("- ./start_real.sh - Start real trading")
    print("- ./monitor.sh - Monitor performance")

if __name__ == "__main__":
    main()
