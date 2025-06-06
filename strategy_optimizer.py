#!/usr/bin/env python3
"""
Strategy Optimization Script for Solana Trading Bot
Analyzes performance and optimizes parameters based on historical data
"""

import pandas as pd
import numpy as np
import json
import sqlite3
from datetime import datetime, timedelta
from sklearn.model_selection import ParameterGrid
from colorama import init, Fore, Style

# Initialize colorama
init()

class StrategyOptimizer:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.current_params = self._load_current_params()
        
    def _load_current_params(self):
        """Load current trading parameters"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def analyze_current_performance(self):
        """Analyze current strategy performance"""
        print(f"{Fore.CYAN}{'='*60}")
        print("CURRENT STRATEGY PERFORMANCE ANALYSIS")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Load trades
        trades_df = pd.read_sql_query("""
            SELECT * FROM trades 
            WHERE action = 'SELL' 
            AND gain_loss_sol IS NOT NULL
            ORDER BY timestamp
        """, self.conn)
        
        if trades_df.empty:
            print(f"{Fore.RED}No completed trades found!{Style.RESET_ALL}")
            return None
        
        # Convert timestamp
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        
        # Calculate metrics
        total_trades = len(trades_df)
        profitable_trades = len(trades_df[trades_df['gain_loss_sol'] > 0])
        win_rate = profitable_trades / total_trades * 100
        
        avg_win = trades_df[trades_df['gain_loss_sol'] > 0]['gain_loss_sol'].mean()
        avg_loss = abs(trades_df[trades_df['gain_loss_sol'] < 0]['gain_loss_sol'].mean())
        risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
        
        total_pnl = trades_df['gain_loss_sol'].sum()
        avg_position_size = trades_df['amount'].mean()
        
        # Best and worst trades
        best_trade = trades_df.loc[trades_df['percentage_change'].idxmax()]
        worst_trade = trades_df.loc[trades_df['percentage_change'].idxmin()]
        
        # Print analysis
        print(f"{Fore.GREEN}Performance Metrics:{Style.RESET_ALL}")
        print(f"  Total Trades: {total_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Risk/Reward: {risk_reward:.2f}:1")
        print(f"  Total P&L: {total_pnl:.4f} SOL")
        print(f"  Average Position: {avg_position_size:.4f} SOL")
        print(f"  Average Win: {avg_win:.4f} SOL ({trades_df[trades_df['gain_loss_sol'] > 0]['percentage_change'].mean():.1f}%)")
        print(f"  Average Loss: {avg_loss:.4f} SOL ({trades_df[trades_df['gain_loss_sol'] < 0]['percentage_change'].mean():.1f}%)")
        
        print(f"\n{Fore.GREEN}Notable Trades:{Style.RESET_ALL}")
        print(f"  Best Trade: +{best_trade['percentage_change']:.1f}% ({best_trade['gain_loss_sol']:.4f} SOL)")
        print(f"  Worst Trade: {worst_trade['percentage_change']:.1f}% ({worst_trade['gain_loss_sol']:.4f} SOL)")
        
        # Analyze by time periods
        print(f"\n{Fore.GREEN}Performance by Time:{Style.RESET_ALL}")
        
        # Hourly performance
        trades_df['hour'] = trades_df['timestamp'].dt.hour
        hourly_stats = trades_df.groupby('hour').agg({
            'gain_loss_sol': ['mean', 'count'],
            'percentage_change': lambda x: (x > 0).sum() / len(x) * 100
        }).round(4)
        
        print("\nBest Trading Hours (UTC):")
        # Sort by average P&L
        hourly_sorted = hourly_stats['gain_loss_sol']['mean'].sort_values(ascending=False)
        
        for i, (hour, avg_pnl) in enumerate(hourly_sorted.head(5).items()):
            count = hourly_stats.loc[hour, ('gain_loss_sol', 'count')]
            wr = hourly_stats.loc[hour, ('percentage_change', '<lambda>')]
            print(f"  {i+1}. Hour {hour:02d}: {avg_pnl:.4f} SOL avg, {wr:.1f}% WR ({count} trades)")
        
        return trades_df
    
    def optimize_position_sizing(self, trades_df):
        """Optimize position sizing based on Kelly Criterion and other methods"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("POSITION SIZING OPTIMIZATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Calculate win probability and average win/loss ratio
        win_rate = (trades_df['gain_loss_sol'] > 0).mean()
        
        # Use percentage changes for more accurate Kelly calculation
        winning_trades = trades_df[trades_df['percentage_change'] > 0]
        losing_trades = trades_df[trades_df['percentage_change'] < 0]
        
        avg_win_pct = winning_trades['percentage_change'].mean() / 100 if len(winning_trades) > 0 else 0
        avg_loss_pct = abs(losing_trades['percentage_change'].mean()) / 100 if len(losing_trades) > 0 else 0
        
        # Kelly Criterion: f = (p*b - q) / b
        # where p = win probability, q = loss probability, b = win/loss ratio
        if avg_loss_pct > 0 and avg_win_pct > 0:
            b = avg_win_pct / avg_loss_pct
            p = win_rate
            q = 1 - p
            kelly_pct = (p * b - q) / b
            kelly_pct = max(0, min(kelly_pct, 0.25))  # Cap at 25%
        else:
            kelly_pct = 0.02  # Default 2%
        
        # Conservative Kelly (half Kelly)
        conservative_kelly = kelly_pct / 2
        
        # Additional safety for high variance
        trade_variance = trades_df['percentage_change'].std() / 100
        if trade_variance > 0.5:  # High variance
            conservative_kelly *= 0.75
            kelly_pct *= 0.75
        
        print(f"{Fore.GREEN}Position Sizing Analysis:{Style.RESET_ALL}")
        print(f"  Win Rate: {win_rate*100:.1f}%")
        print(f"  Avg Win: {avg_win_pct*100:.1f}%")
        print(f"  Avg Loss: {avg_loss_pct*100:.1f}%")
        print(f"  Win/Loss Ratio: {avg_win_pct/avg_loss_pct:.2f}:1" if avg_loss_pct > 0 else "  Win/Loss Ratio: N/A")
        
        print(f"\n{Fore.GREEN}Optimal Position Sizing:{Style.RESET_ALL}")
        print(f"  Current: {self.current_params.get('default_position_size_pct', 4)}%")
        print(f"  Kelly Criterion: {kelly_pct*100:.1f}%")
        print(f"  Conservative Kelly: {conservative_kelly*100:.1f}%")
        print(f"  Recommended Range: {conservative_kelly*100:.1f}-{kelly_pct*100:.1f}%")
        
        # Simulate different position sizes
        print(f"\n{Fore.GREEN}Position Size Simulation (10 SOL starting):{Style.RESET_ALL}")
        position_sizes = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]
        
        best_size = 0
        best_return = -float('inf')
        
        for size in position_sizes:
            # Calculate returns for each trade with this position size
            returns = []
            balance = 10.0
            
            for _, trade in trades_df.iterrows():
                position = balance * size
                trade_return = position * (trade['percentage_change'] / 100)
                balance += trade_return
                returns.append(trade_return)
            
            total_return = balance - 10.0
            avg_return = np.mean(returns)
            
            # Calculate Sharpe-like ratio (return/risk)
            if np.std(returns) > 0:
                sharpe = avg_return / np.std(returns)
            else:
                sharpe = 0
            
            highlight = "***" if size == conservative_kelly else ""
            print(f"  {size*100:>4.0f}%: Final: {balance:>7.2f} SOL, P&L: {total_return:>7.4f} SOL, Sharpe: {sharpe:>5.2f} {highlight}")
            
            if total_return > best_return:
                best_return = total_return
                best_size = size
        
        print(f"\n{Fore.YELLOW}Best Historical Size: {best_size*100:.0f}% (returned {best_return:.4f} SOL){Style.RESET_ALL}")
        
        return conservative_kelly, kelly_pct
    
    def optimize_exit_strategy(self, trades_df):
        """Optimize take profit and stop loss levels"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("EXIT STRATEGY OPTIMIZATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Analyze actual gains/losses distribution
        gains = trades_df[trades_df['percentage_change'] > 0]['percentage_change']
        losses = abs(trades_df[trades_df['percentage_change'] < 0]['percentage_change'])
        
        print(f"{Fore.GREEN}Current Exit Distribution:{Style.RESET_ALL}")
        if len(gains) > 0:
            print(f"  Gains:")
            print(f"    Average: {gains.mean():.1f}%")
            print(f"    Median: {gains.median():.1f}%")
            print(f"    75th percentile: {gains.quantile(0.75):.1f}%")
            print(f"    90th percentile: {gains.quantile(0.90):.1f}%")
            print(f"    Max: {gains.max():.1f}%")
        
        if len(losses) > 0:
            print(f"  Losses:")
            print(f"    Average: {losses.mean():.1f}%")
            print(f"    Median: {losses.median():.1f}%")
            print(f"    75th percentile: {losses.quantile(0.75):.1f}%")
            print(f"    Max: {losses.max():.1f}%")
        
        # Calculate optimal levels based on distribution
        if len(gains) > 0:
            # Use 75th percentile for TP (capture most gains)
            optimal_tp = gains.quantile(0.75)
            # Alternative: use average + 0.5 * std
            alternative_tp = gains.mean() + 0.5 * gains.std()
        else:
            optimal_tp = 30
            alternative_tp = 30
        
        if len(losses) > 0:
            # Use 60th percentile for SL (avoid most losses)
            optimal_sl = losses.quantile(0.60)
        else:
            optimal_sl = 5
        
        print(f"\n{Fore.GREEN}Optimal Exit Levels:{Style.RESET_ALL}")
        print(f"  Current TP: {self.current_params.get('take_profit_pct', 0.5)*100:.0f}%")
        print(f"  Optimal TP (75th %ile): {optimal_tp:.0f}%")
        print(f"  Alternative TP (mean+0.5σ): {alternative_tp:.0f}%")
        print(f"  Current SL: {self.current_params.get('stop_loss_pct', 0.05)*100:.0f}%")
        print(f"  Optimal SL (60th %ile): {optimal_sl:.0f}%")
        
        # Simulate different TP/SL combinations
        print(f"\n{Fore.GREEN}Exit Strategy Simulation:{Style.RESET_ALL}")
        print(f"{'TP/SL':<10} {'Trades':<8} {'Win Rate':<10} {'Avg Win':<10} {'Avg Loss':<10} {'Expectancy':<12}")
        print("-" * 70)
        
        tp_levels = [20, 30, 40, 50, 75]
        sl_levels = [3, 5, 7, 10]
        
        best_combo = None
        best_expectancy = -float('inf')
        
        for tp in tp_levels:
            for sl in sl_levels:
                # Simulate trades with these levels
                simulated_wins = gains[gains <= tp] if len(gains) > 0 else pd.Series()
                simulated_losses = losses[losses <= sl] if len(losses) > 0 else pd.Series()
                
                total_simulated = len(simulated_wins) + len(simulated_losses)
                
                if total_simulated > 0:
                    win_rate = len(simulated_wins) / total_simulated
                    avg_win = simulated_wins.mean() if len(simulated_wins) > 0 else 0
                    avg_loss = simulated_losses.mean() if len(simulated_losses) > 0 else 0
                    
                    # Cap at the TP/SL levels
                    avg_win = min(avg_win, tp)
                    avg_loss = min(avg_loss, sl)
                    
                    expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss
                    
                    if expectancy > best_expectancy:
                        best_expectancy = expectancy
                        best_combo = (tp, sl)
                    
                    # Print selected combinations
                    if (tp in [30, 50] and sl in [5, 7]) or (tp == best_combo[0] and sl == best_combo[1]):
                        print(f"{tp:>2}%/{sl:>2}%    {total_simulated:<8} {win_rate*100:<10.1f} "
                              f"{avg_win:<10.1f} {avg_loss:<10.1f} {expectancy:<12.2f}")
        
        print(f"\n{Fore.YELLOW}Optimal Exit Strategy: TP {best_combo[0]}%, SL {best_combo[1]}% "
              f"(Expectancy: {best_expectancy:.2f}%){Style.RESET_ALL}")
        
        # Suggest trailing stop
        if gains.max() > 100:
            print(f"\n{Fore.GREEN}Trailing Stop Recommendation:{Style.RESET_ALL}")
            print(f"  Activate after: 30% gain")
            print(f"  Trail distance: 15%")
            print(f"  Reason: You've captured gains up to {gains.max():.0f}%!")
        
        return best_combo
    
    def optimize_entry_filters(self, trades_df=None):
        """Optimize entry criteria based on historical performance"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("ENTRY FILTER OPTIMIZATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Get token data with trade results
        query = """
            SELECT DISTINCT
                t.contract_address,
                t.volume_24h,
                t.liquidity_usd,
                t.holders,
                t.safety_score,
                tr.gain_loss_sol,
                tr.percentage_change
            FROM tokens t
            INNER JOIN trades tr ON t.contract_address = tr.contract_address
            WHERE tr.action = 'SELL'
            AND tr.gain_loss_sol IS NOT NULL
        """
        
        tokens_df = pd.read_sql_query(query, self.conn)
        
        if tokens_df.empty:
            print(f"{Fore.RED}No token data found!{Style.RESET_ALL}")
            return
        
        # Analyze each factor
        print(f"{Fore.GREEN}Factor Analysis:{Style.RESET_ALL}")
        
        factors = {
            'volume_24h': 'min_volume_24h',
            'liquidity_usd': 'min_liquidity',
            'holders': 'min_holders',
            'safety_score': 'min_safety_score'
        }
        
        recommendations = {}
        
        for factor, param_name in factors.items():
            if factor in tokens_df.columns and tokens_df[factor].notna().sum() > 10:
                # Remove outliers for better analysis
                factor_data = tokens_df[tokens_df[factor].notna()].copy()
                
                # Calculate profitability correlation
                profitable = (factor_data['gain_loss_sol'] > 0).astype(int)
                
                if factor_data[factor].std() > 0:
                    correlation = factor_data[factor].corr(profitable)
                else:
                    correlation = 0
                
                # Find optimal threshold by testing different percentiles
                percentiles = [10, 25, 40, 50, 60, 75]
                best_threshold = None
                best_score = 0
                
                for pct in percentiles:
                    threshold = factor_data[factor].quantile(pct/100)
                    
                    above = factor_data[factor_data[factor] >= threshold]
                    below = factor_data[factor_data[factor] < threshold]
                    
                    if len(above) >= 10 and len(below) >= 10:
                        above_wr = (above['gain_loss_sol'] > 0).mean()
                        below_wr = (below['gain_loss_sol'] > 0).mean()
                        
                        # Score based on win rate difference and sample size
                        score = (above_wr - below_wr) * np.sqrt(len(above))
                        
                        if score > best_score:
                            best_score = score
                            best_threshold = threshold
                            best_above_wr = above_wr
                            best_below_wr = below_wr
                            best_above_count = len(above)
                
                current_threshold = self.current_params.get(param_name, 0)
                
                print(f"\n  {factor}:")
                print(f"    Correlation with profit: {correlation:.3f}")
                print(f"    Current minimum: {current_threshold:,.0f}")
                
                if best_threshold is not None:
                    print(f"    Suggested minimum: {best_threshold:,.0f}")
                    print(f"    Win rate above threshold: {best_above_wr*100:.1f}% ({best_above_count} trades)")
                    print(f"    Win rate below threshold: {best_below_wr*100:.1f}%")
                    recommendations[param_name] = best_threshold
        
        # ML confidence analysis
        print(f"\n{Fore.GREEN}ML Confidence Analysis:{Style.RESET_ALL}")
        current_ml_threshold = self.current_params.get('ml_confidence_threshold', 0.65)
        print(f"  Current threshold: {current_ml_threshold}")
        print(f"  Recommended for real trading: 0.75-0.80")
        print(f"  Reason: Higher confidence = higher win rate in volatile markets")
        
        return recommendations
    
    def create_optimized_config(self, position_size, exit_strategy, entry_filters=None):
        """Create optimized configuration file"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print("CREATING OPTIMIZED CONFIGURATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Copy current params
        optimized_params = self.current_params.copy()
        
        # Update with optimized values
        optimized_params['default_position_size_pct'] = round(position_size[0] * 100, 1)
        optimized_params['min_position_size_pct'] = round(position_size[0] * 100 * 0.75, 1)
        optimized_params['max_position_size_pct'] = round(position_size[1] * 100, 1)
        
        optimized_params['take_profit_pct'] = exit_strategy[0] / 100
        optimized_params['stop_loss_pct'] = exit_strategy[1] / 100
        
        # Update entry filters if provided
        if entry_filters:
            for param, value in entry_filters.items():
                if param in optimized_params:
                    optimized_params[param] = float(value)
        
        # Ensure safety for real trading
        if not self.current_params.get('simulation_mode', True):
            optimized_params['ml_confidence_threshold'] = max(0.75, optimized_params.get('ml_confidence_threshold', 0.75))
            optimized_params['max_daily_loss_pct'] = min(0.05, optimized_params.get('max_daily_loss_pct', 0.05))
        
        # Save to file
        with open('config/trading_params_optimized.json', 'w') as f:
            json.dump(optimized_params, f, indent=2)
        
        print(f"{Fore.GREEN}✅ Optimized configuration saved to: config/trading_params_optimized.json{Style.RESET_ALL}")
        
        # Show comparison
        print(f"\n{Fore.GREEN}Key Parameter Changes:{Style.RESET_ALL}")
        print(f"{'Parameter':<30} {'Current':>12} {'Optimized':>12} {'Change':>10}")
        print("-" * 66)
        
        params_to_compare = [
            ('default_position_size_pct', 'Position Size (%)', 1, '%'),
            ('take_profit_pct', 'Take Profit', 100, '%'),
            ('stop_loss_pct', 'Stop Loss', 100, '%'),
            ('ml_confidence_threshold', 'ML Threshold', 1, ''),
            ('min_volume_24h', 'Min Volume', 1, ''),
            ('min_liquidity', 'Min Liquidity', 1, ''),
        ]
        
        for param, name, multiplier, suffix in params_to_compare:
            current = self.current_params.get(param, 0)
            optimized = optimized_params.get(param, 0)
            
            current_val = current * multiplier
            optimized_val = optimized * multiplier
            change = optimized_val - current_val
            
            if param in ['min_volume_24h', 'min_liquidity']:
                current_str = f"{current_val:,.0f}"
                optimized_str = f"{optimized_val:,.0f}"
                change_str = f"{change:+,.0f}"
            else:
                current_str = f"{current_val:.1f}{suffix}"
                optimized_str = f"{optimized_val:.1f}{suffix}"
                change_str = f"{change:+.1f}{suffix}"
            
            print(f"{name:<30} {current_str:>12} {optimized_str:>12} {change_str:>10}")
    
    def generate_report(self):
        """Generate comprehensive optimization report"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'SOLANA TRADING BOT STRATEGY OPTIMIZATION':^80}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
        # Analyze current performance
        trades_df = self.analyze_current_performance()
        
        if trades_df is None or len(trades_df) < 20:
            print(f"\n{Fore.RED}Insufficient data for optimization. Need at least 20 completed trades.{Style.RESET_ALL}")
            return
        
        # Optimize components
        position_size = self.optimize_position_sizing(trades_df)
        exit_strategy = self.optimize_exit_strategy(trades_df)
        entry_filters = self.optimize_entry_filters()
        
        # Create optimized config
        self.create_optimized_config(position_size, exit_strategy, entry_filters)
        
        # Final recommendations
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'IMPLEMENTATION RECOMMENDATIONS':^80}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}📊 1. Position Sizing:{Style.RESET_ALL}")
        print(f"   • Start with Conservative Kelly: {position_size[0]*100:.1f}%")
        print(f"   • Scale up to Full Kelly: {position_size[1]*100:.1f}% after 100 profitable trades")
        print(f"   • Never exceed {min(position_size[1]*100*1.5, 15):.0f}% per position")
        
        print(f"\n{Fore.YELLOW}🎯 2. Exit Strategy:{Style.RESET_ALL}")
        print(f"   • Take Profit: {exit_strategy[0]}%")
        print(f"   • Stop Loss: {exit_strategy[1]}%")
        print(f"   • Enable trailing stop after 30% gain (15% trail)")
        
        print(f"\n{Fore.YELLOW}🔍 3. Entry Filters:{Style.RESET_ALL}")
        print(f"   • Increase ML confidence threshold to 0.75+ for real trading")
        print(f"   • Trade during profitable hours (check performance analysis)")
        print(f"   • Adjust minimum liquidity/volume based on analysis above")
        
        print(f"\n{Fore.YELLOW}🛡️ 4. Risk Management:{Style.RESET_ALL}")
        print(f"   • Daily loss limit: 5% of capital")
        print(f"   • Maximum {min(5, self.current_params.get('max_open_positions', 10))} concurrent positions")
        print(f"   • Reduce position size by 50% after 3 consecutive losses")
        print(f"   • Stop trading for the day after hitting daily loss limit")
        
        print(f"\n{Fore.YELLOW}📈 5. Scaling Strategy:{Style.RESET_ALL}")
        print(f"   • Week 1-2: Use 50% of recommended position size")
        print(f"   • Week 3-4: Scale to 75% if profitable")
        print(f"   • Month 2+: Full recommended size if consistently profitable")
        
        print(f"\n{Fore.GREEN}✅ Next Steps:{Style.RESET_ALL}")
        print("1. Review the optimized configuration")
        print("2. Run in simulation for 100+ more trades")
        print("3. Compare performance metrics")
        print("4. If improved, copy optimized config:")
        print(f"   {Fore.CYAN}cp config/trading_params_optimized.json config/trading_params.json{Style.RESET_ALL}")
        print("5. Start with small real capital to verify live performance")
        
        # Calculate potential improvement
        current_avg_position = trades_df['amount'].mean()
        new_position_pct = position_size[0]
        potential_multiplier = (new_position_pct * 10) / current_avg_position  # Assuming 10 SOL balance
        
        if potential_multiplier > 1:
            print(f"\n{Fore.MAGENTA}💰 Potential Impact:{Style.RESET_ALL}")
            print(f"   With optimized settings, your profits could be {potential_multiplier:.1f}x higher!")
            print(f"   (Based on larger position sizes with same win rate)")

def main():
    """Run the strategy optimizer"""
    try:
        print(f"\n{Fore.CYAN}🚀 Solana Trading Bot Strategy Optimizer v1.0{Style.RESET_ALL}")
        print("="*50)
        
        optimizer = StrategyOptimizer()
        optimizer.generate_report()
        
        print(f"\n{Fore.GREEN}✅ Optimization complete!{Style.RESET_ALL}")
        print(f"\n💡 Tip: Always test optimized settings in simulation before real trading!")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error during optimization: {e}{Style.RESET_ALL}")
        print(f"Make sure the bot has completed some trades before running optimization.")

if __name__ == "__main__":
    main()