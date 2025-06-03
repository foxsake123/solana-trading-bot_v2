#!/usr/bin/env python3
"""
Trading Parameter Optimizer
Analyzes historical performance and suggests optimal trading parameters
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta

class ParameterOptimizer:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.current_params = self.load_current_params()
        
    def load_current_params(self):
        """Load current trading parameters"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def analyze_position_sizing(self):
        """Analyze optimal position sizing based on Kelly Criterion and historical data"""
        print("\n" + "="*60)
        print("POSITION SIZING ANALYSIS")
        print("="*60)
        
        # Get trade data
        query = """
        SELECT 
            amount,
            gain_loss_sol,
            percentage_change
        FROM trades
        WHERE action = 'SELL' AND gain_loss_sol IS NOT NULL
        ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        if len(df) < 50:
            print("⚠️  Need at least 50 completed trades for reliable analysis")
            return
        
        # Calculate win rate and average win/loss
        wins = df[df['gain_loss_sol'] > 0]
        losses = df[df['gain_loss_sol'] < 0]
        
        win_rate = len(wins) / len(df)
        avg_win_pct = wins['percentage_change'].mean() / 100
        avg_loss_pct = abs(losses['percentage_change'].mean()) / 100
        
        print(f"\nCurrent Performance:")
        print(f"  Win Rate: {win_rate:.1%}")
        print(f"  Average Win: {avg_win_pct:.1%}")
        print(f"  Average Loss: {avg_loss_pct:.1%}")
        
        # Kelly Criterion calculation
        if avg_loss_pct > 0:
            kelly_pct = (win_rate * avg_win_pct - (1 - win_rate) * avg_loss_pct) / avg_win_pct
            kelly_pct = max(0, kelly_pct)  # Don't recommend negative sizing
            
            # Conservative Kelly (25% of full Kelly)
            conservative_kelly = kelly_pct * 0.25
            
            print(f"\nKelly Criterion Analysis:")
            print(f"  Full Kelly: {kelly_pct:.1%} of balance")
            print(f"  Conservative Kelly (25%): {conservative_kelly:.1%} of balance")
        
        # Analyze performance by position size
        df['position_pct'] = df['amount'] / df['amount'].sum() * 100
        df['size_bucket'] = pd.qcut(df['amount'], q=5, labels=['XS', 'S', 'M', 'L', 'XL'])
        
        size_performance = df.groupby('size_bucket').agg({
            'gain_loss_sol': ['mean', 'count'],
            'percentage_change': 'mean'
        })
        
        print(f"\nPerformance by Position Size:")
        print(size_performance)
        
        # Recommendations
        print(f"\n" + "="*60)
        print("POSITION SIZING RECOMMENDATIONS")
        print("="*60)
        
        current_default = self.current_params.get('default_position_size_pct', 4.0)
        
        if win_rate > 0.7 and conservative_kelly > current_default:
            print(f"✅ INCREASE position sizes:")
            print(f"   Current: {current_default}%")
            print(f"   Recommended: {min(conservative_kelly, 7.0):.1f}%")
            print(f"   Reason: High win rate ({win_rate:.1%}) supports larger positions")
        
        elif win_rate < 0.5:
            print(f"⚠️  DECREASE position sizes:")
            print(f"   Current: {current_default}%")
            print(f"   Recommended: {max(conservative_kelly, 2.0):.1f}%")
            print(f"   Reason: Low win rate ({win_rate:.1%}) requires smaller positions")
        
        else:
            print(f"✅ Current position sizing appears appropriate")
        
        # Risk per trade analysis
        max_consecutive_losses = self._find_max_consecutive_losses(df)
        print(f"\nRisk Management:")
        print(f"  Max consecutive losses observed: {max_consecutive_losses}")
        print(f"  Recommended max risk per trade: {100 / (max_consecutive_losses * 4):.1f}%")
        
        return {
            'win_rate': win_rate,
            'kelly_pct': conservative_kelly if 'conservative_kelly' in locals() else current_default / 100,
            'recommended_size': min(conservative_kelly, 7.0) if 'conservative_kelly' in locals() else current_default
        }
    
    def _find_max_consecutive_losses(self, df):
        """Find maximum consecutive losses"""
        losses = (df['gain_loss_sol'] < 0).astype(int)
        max_consecutive = 0
        current_consecutive = 0
        
        for loss in losses:
            if loss:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def analyze_exit_strategy(self):
        """Analyze optimal take profit and stop loss levels"""
        print("\n" + "="*60)
        print("EXIT STRATEGY ANALYSIS")
        print("="*60)
        
        # Get all trades to analyze price movements
        query = """
        SELECT 
            contract_address,
            action,
            price,
            timestamp,
            percentage_change,
            gain_loss_sol
        FROM trades
        ORDER BY contract_address, timestamp
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Group by token and analyze price paths
        token_groups = df.groupby('contract_address')
        
        max_gains = []
        max_drawdowns = []
        actual_exits = []
        
        for token, group in token_groups:
            buys = group[group['action'] == 'BUY']
            sells = group[group['action'] == 'SELL']
            
            if len(buys) > 0 and len(sells) > 0:
                # For simplicity, assume single buy/sell per token
                entry_price = buys.iloc[0]['price']
                exit_data = sells.iloc[0]
                
                if exit_data['percentage_change'] is not None:
                    actual_exits.append(exit_data['percentage_change'])
                
                # In real implementation, we'd track intraday price movements
                # For now, simulate based on exit percentage
                if exit_data['percentage_change'] > 0:
                    # Assume max gain was 20% higher than exit
                    max_gains.append(exit_data['percentage_change'] * 1.2)
                else:
                    max_gains.append(abs(exit_data['percentage_change']) * 0.5)
                
                # Assume max drawdown was exit percentage if loss, or 5% if profit
                if exit_data['percentage_change'] < 0:
                    max_drawdowns.append(abs(exit_data['percentage_change']))
                else:
                    max_drawdowns.append(5.0)
        
        if actual_exits:
            print(f"\nExit Analysis (based on {len(actual_exits)} trades):")
            print(f"  Average exit: {np.mean(actual_exits):.1f}%")
            print(f"  Median exit: {np.median(actual_exits):.1f}%")
            print(f"  Best exit: {max(actual_exits):.1f}%")
            print(f"  Worst exit: {min(actual_exits):.1f}%")
            
            # Analyze premature exits
            profitable_exits = [e for e in actual_exits if e > 0]
            if profitable_exits:
                print(f"\nProfitable Trade Analysis:")
                print(f"  Average profitable exit: {np.mean(profitable_exits):.1f}%")
                print(f"  Could have gained (est): {np.mean(profitable_exits) * 1.5:.1f}%")
        
        # Current parameters
        current_tp = self.current_params.get('take_profit_pct', 0.5) * 100
        current_sl = self.current_params.get('stop_loss_pct', 0.05) * 100
        
        print(f"\nCurrent Exit Parameters:")
        print(f"  Take Profit: {current_tp:.0f}%")
        print(f"  Stop Loss: {current_sl:.0f}%")
        
        # Recommendations
        print(f"\n" + "="*60)
        print("EXIT STRATEGY RECOMMENDATIONS")
        print("="*60)
        
        if profitable_exits and np.mean(profitable_exits) > 100:
            print(f"✅ INCREASE take profit targets:")
            print(f"   Current: {current_tp:.0f}%")
            print(f"   Recommended: {min(np.percentile(profitable_exits, 75), 100):.0f}%")
            print(f"   Reason: Historical data shows larger gains are possible")
        
        if max_drawdowns and np.mean(max_drawdowns) < current_sl:
            print(f"✅ TIGHTEN stop loss:")
            print(f"   Current: {current_sl:.0f}%")
            print(f"   Recommended: {max(np.mean(max_drawdowns), 3):.0f}%")
            print(f"   Reason: Most losses occur before current stop loss level")
        
        # Trailing stop analysis
        if self.current_params.get('trailing_stop_enabled', True):
            print(f"\n✅ Trailing Stop Analysis:")
            activation = self.current_params.get('trailing_stop_activation_pct', 0.3) * 100
            distance = self.current_params.get('trailing_stop_distance_pct', 0.15) * 100
            
            print(f"   Current activation: {activation:.0f}%")
            print(f"   Current distance: {distance:.0f}%")
            
            if profitable_exits and np.percentile(profitable_exits, 75) > activation * 2:
                print(f"   Recommendation: Increase activation to {activation * 1.5:.0f}%")
                print(f"   Reason: Many trades exceed current activation significantly")
    
    def analyze_token_selection(self):
        """Analyze which token characteristics lead to profitable trades"""
        print("\n" + "="*60)
        print("TOKEN SELECTION ANALYSIS")
        print("="*60)
        
        # Get token data with trade outcomes
        query = """
        SELECT 
            t.contract_address,
            tk.volume_24h,
            tk.liquidity_usd,
            tk.holders,
            tk.safety_score,
            tk.mcap,
            AVG(CASE WHEN t.action='SELL' THEN t.gain_loss_sol END) as avg_pnl,
            COUNT(CASE WHEN t.action='SELL' AND t.gain_loss_sol > 0 THEN 1 END) as wins,
            COUNT(CASE WHEN t.action='SELL' AND t.gain_loss_sol < 0 THEN 1 END) as losses
        FROM trades t
        LEFT JOIN tokens tk ON t.contract_address = tk.contract_address
        WHERE tk.volume_24h IS NOT NULL
        GROUP BY t.contract_address
        HAVING COUNT(CASE WHEN t.action='SELL' THEN 1 END) > 0
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        if len(df) < 10:
            print("⚠️  Need more token data for reliable analysis")
            return
        
        # Calculate win rate per token
        df['total_trades'] = df['wins'] + df['losses']
        df['win_rate'] = df['wins'] / df['total_trades']
        df['profitable'] = df['avg_pnl'] > 0
        
        # Analyze correlations
        print(f"\nToken Characteristics vs Profitability:")
        
        # Volume analysis
        profitable_tokens = df[df['profitable']]
        unprofitable_tokens = df[~df['profitable']]
        
        if len(profitable_tokens) > 0 and len(unprofitable_tokens) > 0:
            print(f"\nProfitable tokens (n={len(profitable_tokens)}):")
            print(f"  Avg Volume: ${profitable_tokens['volume_24h'].mean():,.0f}")
            print(f"  Avg Liquidity: ${profitable_tokens['liquidity_usd'].mean():,.0f}")
            print(f"  Avg Holders: {profitable_tokens['holders'].mean():.0f}")
            print(f"  Avg Safety Score: {profitable_tokens['safety_score'].mean():.1f}")
            
            print(f"\nUnprofitable tokens (n={len(unprofitable_tokens)}):")
            print(f"  Avg Volume: ${unprofitable_tokens['volume_24h'].mean():,.0f}")
            print(f"  Avg Liquidity: ${unprofitable_tokens['liquidity_usd'].mean():,.0f}")
            print(f"  Avg Holders: {unprofitable_tokens['holders'].mean():.0f}")
            print(f"  Avg Safety Score: {unprofitable_tokens['safety_score'].mean():.1f}")
        
        # Find optimal thresholds
        print(f"\n" + "="*60)
        print("TOKEN SELECTION RECOMMENDATIONS")
        print("="*60)
        
        current_min_volume = self.current_params.get('min_volume_24h', 30000)
        current_min_liquidity = self.current_params.get('min_liquidity', 20000)
        current_min_holders = self.current_params.get('min_holders', 75)
        
        # Volume threshold analysis
        if len(profitable_tokens) > 5:
            optimal_volume = profitable_tokens['volume_24h'].quantile(0.25)
            if optimal_volume > current_min_volume * 1.5:
                print(f"✅ INCREASE minimum volume requirement:")
                print(f"   Current: ${current_min_volume:,}")
                print(f"   Recommended: ${optimal_volume:,.0f}")
                print(f"   Reason: Higher volume tokens more profitable")
            
            # Liquidity threshold
            optimal_liquidity = profitable_tokens['liquidity_usd'].quantile(0.25)
            if optimal_liquidity > current_min_liquidity * 1.5:
                print(f"\n✅ INCREASE minimum liquidity requirement:")
                print(f"   Current: ${current_min_liquidity:,}")
                print(f"   Recommended: ${optimal_liquidity:,.0f}")
                print(f"   Reason: Better liquidity improves profitability")
            
            # Holder threshold
            optimal_holders = profitable_tokens['holders'].quantile(0.25)
            if optimal_holders > current_min_holders * 1.5:
                print(f"\n✅ INCREASE minimum holders requirement:")
                print(f"   Current: {current_min_holders}")
                print(f"   Recommended: {int(optimal_holders)}")
                print(f"   Reason: More holders indicates stability")
    
    def analyze_timing(self):
        """Analyze optimal trading times and frequency"""
        print("\n" + "="*60)
        print("TIMING ANALYSIS")
        print("="*60)
        
        # Get trades with timestamps
        query = """
        SELECT 
            timestamp,
            action,
            gain_loss_sol,
            percentage_change
        FROM trades
        WHERE action = 'SELL' AND gain_loss_sol IS NOT NULL
        ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, self.conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['profitable'] = df['gain_loss_sol'] > 0
        
        # Hourly analysis
        hourly_stats = df.groupby('hour').agg({
            'profitable': ['sum', 'count', 'mean'],
            'gain_loss_sol': 'mean'
        })
        
        hourly_stats.columns = ['wins', 'total', 'win_rate', 'avg_pnl']
        hourly_stats = hourly_stats[hourly_stats['total'] >= 5]  # Min 5 trades
        
        print("\nPerformance by Hour (UTC):")
        best_hours = hourly_stats.nlargest(5, 'win_rate')
        for hour, stats in best_hours.iterrows():
            print(f"  Hour {int(hour):02d}: {stats['win_rate']:.1%} win rate, "
                  f"{stats['avg_pnl']:.4f} SOL avg P&L ({int(stats['total'])} trades)")
        
        # Day of week analysis
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_stats = df.groupby('day_of_week').agg({
            'profitable': ['sum', 'count', 'mean'],
            'gain_loss_sol': 'mean'
        })
        
        daily_stats.columns = ['wins', 'total', 'win_rate', 'avg_pnl']
        
        print("\nPerformance by Day of Week:")
        for day, stats in daily_stats.iterrows():
            if stats['total'] >= 5:
                print(f"  {day_names[int(day)]}: {stats['win_rate']:.1%} win rate, "
                      f"{stats['avg_pnl']:.4f} SOL avg P&L ({int(stats['total'])} trades)")
        
        # Trading frequency analysis
        df['date'] = df['timestamp'].dt.date
        daily_trades = df.groupby('date').size()
        
        print(f"\nTrading Frequency:")
        print(f"  Average trades per day: {daily_trades.mean():.1f}")
        print(f"  Max trades per day: {daily_trades.max()}")
        print(f"  Days with no trades: {(daily_trades == 0).sum()}")
        
        # Recommendations
        print(f"\n" + "="*60)
        print("TIMING RECOMMENDATIONS")
        print("="*60)
        
        if len(best_hours) > 0:
            best_hour_list = best_hours.index.tolist()
            print(f"✅ Focus trading during these hours (UTC): {best_hour_list}")
            
            if hasattr(self.current_params, 'get') and 'avoid_low_volume_hours' in self.current_params:
                current_avoided = self.current_params.get('low_volume_hours', [])
                recommended_avoid = [h for h in range(24) if h not in best_hour_list and 
                                   hourly_stats.get(h, {'win_rate': 0})['win_rate'] < 0.5]
                if recommended_avoid != current_avoided:
                    print(f"\n✅ Update low volume hours to avoid:")
                    print(f"   Current: {current_avoided}")
                    print(f"   Recommended: {recommended_avoid[:6]}")  # Limit to 6 hours
    
    def generate_optimized_config(self):
        """Generate optimized configuration file based on analysis"""
        print("\n" + "="*60)
        print("GENERATING OPTIMIZED CONFIGURATION")
        print("="*60)
        
        # Run all analyses
        position_analysis = self.analyze_position_sizing()
        
        # Create optimized config
        optimized = self.current_params.copy()
        
        # Update position sizing if recommended
        if position_analysis and 'recommended_size' in position_analysis:
            optimized['default_position_size_pct'] = round(position_analysis['recommended_size'], 1)
            optimized['min_position_size_pct'] = round(position_analysis['recommended_size'] * 0.75, 1)
            optimized['max_position_size_pct'] = round(position_analysis['recommended_size'] * 1.25, 1)
        
        # Save optimized config
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'config/trading_params_optimized_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(optimized, f, indent=4)
        
        print(f"\n✅ Optimized configuration saved to: {filename}")
        print("\nKey changes:")
        
        for key in ['default_position_size_pct', 'take_profit_pct', 'stop_loss_pct', 
                    'min_volume_24h', 'min_liquidity', 'min_holders']:
            if key in optimized and key in self.current_params:
                if optimized[key] != self.current_params[key]:
                    print(f"  {key}: {self.current_params[key]} → {optimized[key]}")
        
        print("\n⚠️  Review changes carefully before applying to live trading!")
        print("To apply: Copy optimized file to config/trading_params.json")
    
    def generate_report(self):
        """Generate comprehensive optimization report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE PARAMETER OPTIMIZATION REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run all analyses
        self.analyze_position_sizing()
        self.analyze_exit_strategy()
        self.analyze_token_selection()
        self.analyze_timing()
        
        # Generate optimized config
        self.generate_optimized_config()
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("\n1. Continue collecting data in simulation mode")
        print("2. Review and test optimized parameters")
        print("3. Gradually implement changes")
        print("4. Monitor performance closely")
        print("\n✅ Optimization complete!")

def main():
    """Run parameter optimization"""
    optimizer = ParameterOptimizer()
    optimizer.generate_report()

if __name__ == "__main__":
    main()