# update_config_citadel.py
"""
Update configuration for Citadel-Barra strategy implementation
"""

import json
import os

def update_trading_params():
    """Update trading_params.json with Citadel-inspired parameters"""
    
    # Read existing config
    config_path = 'config/trading_params.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Add Citadel-Barra specific parameters
    citadel_params = {
        # Multi-factor strategy parameters
        "use_citadel_strategy": True,
        "alpha_decay_halflife_hours": 24,
        "max_factor_exposure": 2.0,
        "target_idiosyncratic_ratio": 0.6,
        
        # Signal weights (must sum to 1.0)
        "signal_weights": {
            "momentum": 0.3,
            "mean_reversion": 0.2,
            "volume_breakout": 0.2,
            "ml_prediction": 0.3
        },
        
        # Factor exposure limits
        "factor_limits": {
            "market_beta": [-1.5, 2.5],
            "volatility": [0, 3.0],
            "momentum": [-2.0, 3.0],
            "liquidity": [0.5, 5.0]
        },
        
        # Enhanced risk management
        "dynamic_position_sizing": True,
        "use_kelly_criterion": True,
        "kelly_safety_factor": 0.25,
        
        # Exit strategy enhancements
        "use_dynamic_exits": True,
        "alpha_exhaustion_threshold": -0.2,
        "volatility_exit_multiplier": 2.0,
        
        # Portfolio constraints
        "max_portfolio_risk_pct": 30.0,
        "min_idiosyncratic_positions": 3,
        
        # Rebalancing parameters
        "rebalance_enabled": True,
        "rebalance_frequency_hours": 24,
        "rebalance_threshold": 0.1
    }
    
    # Merge with existing config
    config.update(citadel_params)
    
    # Adjust existing parameters for better integration
    config["take_profit_pct"] = 0.5  # 50% base, adjusted by alpha
    config["stop_loss_pct"] = 0.05   # 5% stop loss
    config["min_position_size_pct"] = 3.0  # Minimum 3% position
    config["default_position_size_pct"] = 4.0  # Default 4%
    config["max_position_size_pct"] = 5.0  # Maximum 5%
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"✅ Updated {config_path} with Citadel-Barra parameters")
    
    # Create backup
    backup_path = config_path.replace('.json', '_pre_citadel.json')
    with open(backup_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"📁 Backup saved to {backup_path}")

def create_factor_models_config():
    """Create configuration for factor models"""
    
    factor_config = {
        "factor_models": {
            "market_factors": {
                "crypto_market_beta": {
                    "description": "Sensitivity to overall crypto market",
                    "calculation": "regression_vs_total_market_cap",
                    "update_frequency": "hourly"
                },
                "sol_ecosystem_beta": {
                    "description": "Sensitivity to Solana ecosystem",
                    "calculation": "regression_vs_sol_price",
                    "update_frequency": "hourly"
                }
            },
            
            "style_factors": {
                "momentum": {
                    "timeframes": ["1h", "6h", "24h"],
                    "weights": [0.2, 0.3, 0.5]
                },
                "volatility": {
                    "window": 24,
                    "annualization_factor": 8760
                },
                "liquidity": {
                    "components": ["volume_ratio", "bid_ask_spread", "market_depth"]
                },
                "size": {
                    "buckets": ["micro", "small", "medium", "large"],
                    "thresholds": [100000, 1000000, 10000000, 100000000]
                }
            },
            
            "quality_factors": {
                "holder_distribution": {
                    "metrics": ["gini_coefficient", "whale_concentration", "unique_holders"]
                },
                "volume_stability": {
                    "lookback_days": 7,
                    "cv_threshold": 0.5
                }
            },
            
            "crypto_specific_factors": {
                "defi_correlation": {
                    "reference_tokens": ["JUP", "RAY", "ORCA"],
                    "correlation_window": 168
                },
                "meme_characteristics": {
                    "indicators": ["social_volume", "price_volatility", "holder_turnover"]
                }
            }
        },
        
        "risk_decomposition": {
            "method": "principal_components",
            "num_components": 5,
            "explain_variance_threshold": 0.85
        },
        
        "factor_returns": {
            "estimation_window": 30,
            "update_frequency": "daily"
        }
    }
    
    # Save factor models config
    factor_config_path = 'config/factor_models.json'
    with open(factor_config_path, 'w') as f:
        json.dump(factor_config, f, indent=4)
    
    print(f"✅ Created {factor_config_path}")

def create_strategy_monitor():
    """Create a monitoring script for the Citadel-Barra strategy"""
    
    monitor_code = '''#!/usr/bin/env python3
"""
Monitor for Citadel-Barra strategy performance
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

init()

class CitadelStrategyMonitor:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
    
    def analyze_factor_performance(self):
        """Analyze performance attribution by factors"""
        conn = sqlite3.connect(self.db_path)
        
        # Get trades with factor data
        query = """
        SELECT 
            t.*,
            json_extract(t.metadata, '$.factors.market_beta') as market_beta,
            json_extract(t.metadata, '$.factors.momentum') as momentum,
            json_extract(t.metadata, '$.factors.volatility') as volatility,
            json_extract(t.metadata, '$.alpha_signals.expected_alpha') as expected_alpha
        FROM trades t
        WHERE t.metadata IS NOT NULL
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print(f"{Fore.YELLOW}No trades with factor data found{Style.RESET_ALL}")
            return
        
        # Calculate factor attribution
        print(f"\\n{Fore.CYAN}FACTOR PERFORMANCE ANALYSIS{Style.RESET_ALL}")
        print("="*50)
        
        # Group by factor buckets
        for factor in ['market_beta', 'momentum', 'volatility']:
            if factor in df.columns:
                # Create buckets
                df[f'{factor}_bucket'] = pd.qcut(df[factor], q=3, labels=['Low', 'Medium', 'High'])
                
                # Calculate performance by bucket
                perf = df.groupby(f'{factor}_bucket')['gain_loss_sol'].agg(['mean', 'count', 'sum'])
                
                print(f"\\n{factor.upper()}:")
                for bucket, row in perf.iterrows():
                    color = Fore.GREEN if row['mean'] > 0 else Fore.RED
                    print(f"  {bucket}: {color}{row['mean']:.4f} SOL{Style.RESET_ALL} "
                          f"(n={row['count']}, total={row['sum']:.4f})")
    
    def calculate_sharpe_ratio(self):
        """Calculate Sharpe ratio and other risk metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Get daily returns
        query = """
        SELECT 
            DATE(timestamp) as date,
            SUM(gain_loss_sol) as daily_pnl
        FROM trades
        WHERE action = 'SELL'
        GROUP BY DATE(timestamp)
        ORDER BY date
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 2:
            print(f"{Fore.YELLOW}Insufficient data for Sharpe ratio{Style.RESET_ALL}")
            return
        
        # Calculate metrics
        daily_returns = df['daily_pnl'].values
        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        
        # Annualized Sharpe (crypto trades 24/7)
        sharpe = (avg_return / std_return) * np.sqrt(365) if std_return > 0 else 0
        
        # Max drawdown
        cumulative = np.cumsum(daily_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        print(f"\\n{Fore.CYAN}RISK-ADJUSTED PERFORMANCE{Style.RESET_ALL}")
        print("="*50)
        print(f"Sharpe Ratio: {Fore.GREEN if sharpe > 1 else Fore.YELLOW}{sharpe:.2f}{Style.RESET_ALL}")
        print(f"Max Drawdown: {Fore.RED}{max_drawdown:.1%}{Style.RESET_ALL}")
        print(f"Daily Avg Return: {avg_return:.4f} SOL")
        print(f"Daily Volatility: {std_return:.4f} SOL")
    
    def show_alpha_decay(self):
        """Visualize alpha decay over time"""
        conn = sqlite3.connect(self.db_path)
        
        # Get positions with holding time
        query = """
        SELECT 
            contract_address,
            MIN(timestamp) as entry_time,
            MAX(timestamp) as exit_time,
            SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as total_pnl
        FROM trades
        GROUP BY contract_address
        HAVING COUNT(*) > 1
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return
        
        # Calculate holding periods
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        df['holding_hours'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
        
        # Analyze P&L by holding period
        print(f"\\n{Fore.CYAN}ALPHA DECAY ANALYSIS{Style.RESET_ALL}")
        print("="*50)
        
        # Group by holding period buckets
        buckets = [0, 6, 12, 24, 48, 168]  # hours
        labels = ['0-6h', '6-12h', '12-24h', '24-48h', '48h+']
        
        df['holding_bucket'] = pd.cut(df['holding_hours'], bins=buckets, labels=labels)
        
        perf_by_holding = df.groupby('holding_bucket')['total_pnl'].agg(['mean', 'count'])
        
        for bucket, row in perf_by_holding.iterrows():
            if row['count'] > 0:
                color = Fore.GREEN if row['mean'] > 0 else Fore.RED
                print(f"{bucket}: {color}{row['mean']:.4f} SOL{Style.RESET_ALL} (n={row['count']})")
    
    def run(self):
        """Run all analyses"""
        print(f"{Fore.CYAN}CITADEL-BARRA STRATEGY MONITOR{Style.RESET_ALL}")
        print("="*60)
        
        self.analyze_factor_performance()
        self.calculate_sharpe_ratio()
        self.show_alpha_decay()

if __name__ == "__main__":
    monitor = CitadelStrategyMonitor()
    monitor.run()
'''
    
    # Save monitor script with explicit UTF-8 encoding
    monitor_path = 'citadel_strategy_monitor.py'
    with open(monitor_path, 'w', encoding='utf-8') as f:
        f.write(monitor_code)
    
    print(f"✅ Created {monitor_path}")
    
    # Make it executable on Unix-like systems
    import stat
    try:
        os.chmod(monitor_path, os.stat(monitor_path).st_mode | stat.S_IEXEC)
    except:
        pass  # Windows doesn't support chmod

def main():
    """Run all configuration updates"""
    print("🏛️  Updating configuration for Citadel-Barra strategy...")
    
    update_trading_params()
    create_factor_models_config()
    create_strategy_monitor()
    
    print("\n✅ Configuration updates complete!")
    print("\nNext steps:")
    print("1. Review updated config/trading_params.json")
    print("2. Run python citadel_strategy_monitor.py to monitor performance")
    print("3. Update start_bot.py to use EnhancedTradingBot instead of TradingBot")
    print("4. Test in simulation mode first")

if __name__ == "__main__":
    main()