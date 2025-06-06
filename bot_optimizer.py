#!/usr/bin/env python3
"""
Trading Bot Optimizer
Analyzes performance and suggests parameter optimizations
"""
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from colorama import init, Fore, Style

init()

class TradingBotOptimizer:
    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.current_params = self._load_current_params()
        self.optimization_results = {}
        
    def _load_current_params(self) -> Dict:
        """Load current trading parameters"""
        params = {}
        
        # Load trading_params.json
        try:
            with open('config/trading_params.json', 'r') as f:
                params['trading'] = json.load(f)
        except:
            params['trading'] = {}
        
        # Load bot_control.json
        try:
            with open('config/bot_control.json', 'r') as f:
                params['control'] = json.load(f)
        except:
            params['control'] = {}
        
        # Load bot_control_real.json if exists
        try:
            with open('config/bot_control_real.json', 'r') as f:
                params['control_real'] = json.load(f)
        except:
            params['control_real'] = {}
        
        return params
    
    def analyze_performance_patterns(self) -> Dict:
        """Analyze trading patterns to identify optimization opportunities"""
        conn = sqlite3.connect(self.db_path)
        
        analysis = {
            'win_rate_by_hour': self._analyze_hourly_performance(conn),
            'win_rate_by_position_size': self._analyze_position_size_performance(conn),
            'token_characteristics': self._analyze_winning_token_patterns(conn),
            'exit_timing': self._analyze_exit_timing(conn),
            'drawdown_analysis': self._analyze_drawdowns(conn),
            'ml_performance': self._analyze_ml_accuracy(conn)
        }
        
        conn.close()
        return analysis
    
    def _analyze_hourly_performance(self, conn) -> pd.DataFrame:
        """Analyze performance by hour of day"""
        query = """
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as total_trades,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN action='SELL' AND gain_loss_sol < 0 THEN 1 ELSE 0 END) as losses,
                AVG(CASE WHEN action='SELL' THEN gain_loss_sol END) as avg_pnl,
                AVG(CASE WHEN action='SELL' THEN percentage_change END) as avg_pct_change
            FROM trades
            GROUP BY hour
            HAVING total_trades >= 5
            ORDER BY avg_pnl DESC
        """
        
        return pd.read_sql_query(query, conn)
    
    def _analyze_position_size_performance(self, conn) -> pd.DataFrame:
        """Analyze performance by position size"""
        query = """
            WITH position_analysis AS (
                SELECT 
                    t1.amount,
                    t1.amount * 100.0 / 10.0 as position_pct,  -- Assuming 10 SOL balance
                    t2.gain_loss_sol,
                    t2.percentage_change
                FROM trades t1
                JOIN trades t2 ON t1.contract_address = t2.contract_address
                WHERE t1.action = 'BUY' AND t2.action = 'SELL'
                AND t2.timestamp > t1.timestamp
            )
            SELECT 
                CASE 
                    WHEN position_pct < 2 THEN '<2%'
                    WHEN position_pct < 3 THEN '2-3%'
                    WHEN position_pct < 4 THEN '3-4%'
                    WHEN position_pct < 5 THEN '4-5%'
                    ELSE '>5%'
                END as size_range,
                COUNT(*) as trades,
                AVG(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) * 100 as win_rate,
                AVG(gain_loss_sol) as avg_pnl,
                AVG(percentage_change) as avg_pct
            FROM position_analysis
            GROUP BY size_range
            ORDER BY avg_pnl DESC
        """
        
        return pd.read_sql_query(query, conn)
    
    def _analyze_winning_token_patterns(self, conn) -> Dict:
        """Analyze characteristics of winning tokens"""
        query = """
            SELECT 
                tk.volume_24h,
                tk.liquidity_usd,
                tk.holders,
                tk.mcap,
                CASE WHEN tr.gain_loss_sol > 0 THEN 1 ELSE 0 END as is_winner
            FROM trades tr
            JOIN tokens tk ON tr.contract_address = tk.contract_address
            WHERE tr.action = 'SELL' AND tr.gain_loss_sol IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return {}
        
        # Calculate average characteristics for winners vs losers
        winners = df[df['is_winner'] == 1]
        losers = df[df['is_winner'] == 0]
        
        patterns = {
            'winner_avg_volume': winners['volume_24h'].mean() if not winners.empty else 0,
            'loser_avg_volume': losers['volume_24h'].mean() if not losers.empty else 0,
            'winner_avg_liquidity': winners['liquidity_usd'].mean() if not winners.empty else 0,
            'loser_avg_liquidity': losers['liquidity_usd'].mean() if not losers.empty else 0,
            'winner_avg_holders': winners['holders'].mean() if not winners.empty else 0,
            'loser_avg_holders': losers['holders'].mean() if not losers.empty else 0,
            'winner_avg_mcap': winners['mcap'].mean() if not winners.empty else 0,
            'loser_avg_mcap': losers['mcap'].mean() if not losers.empty else 0
        }
        
        return patterns
    
    def _analyze_exit_timing(self, conn) -> Dict:
        """Analyze exit timing effectiveness"""
        query = """
            WITH trade_pairs AS (
                SELECT 
                    t1.contract_address,
                    t1.timestamp as buy_time,
                    t2.timestamp as sell_time,
                    t2.percentage_change,
                    t2.gain_loss_sol,
                    CAST((julianday(t2.timestamp) - julianday(t1.timestamp)) * 24 AS INTEGER) as hold_hours
                FROM trades t1
                JOIN trades t2 ON t1.contract_address = t2.contract_address
                WHERE t1.action = 'BUY' AND t2.action = 'SELL'
                AND t2.timestamp > t1.timestamp
            )
            SELECT 
                hold_hours,
                COUNT(*) as count,
                AVG(percentage_change) as avg_pct,
                AVG(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) * 100 as win_rate
            FROM trade_pairs
            WHERE hold_hours >= 0 AND hold_hours <= 48
            GROUP BY hold_hours
            ORDER BY hold_hours
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return {}
        
        # Find optimal hold time
        optimal_hold = df.loc[df['avg_pct'].idxmax()]['hold_hours'] if not df.empty else 0
        avg_hold = df['hold_hours'].mean()
        
        return {
            'optimal_hold_hours': optimal_hold,
            'average_hold_hours': avg_hold,
            'best_performance_window': df.nlargest(3, 'avg_pct')[['hold_hours', 'avg_pct', 'win_rate']].to_dict('records')
        }
    
    def _analyze_drawdowns(self, conn) -> Dict:
        """Analyze drawdown patterns"""
        cursor = conn.cursor()
        
        # Get all trades ordered by time
        cursor.execute("""
            SELECT timestamp, action, amount, gain_loss_sol
            FROM trades
            ORDER BY timestamp
        """)
        
        trades = cursor.fetchall()
        balance = 10.0  # Starting balance
        peak_balance = balance
        drawdowns = []
        current_drawdown = 0
        
        for timestamp, action, amount, gain_loss in trades:
            if action == 'BUY':
                balance -= amount
            elif action == 'SELL':
                balance += amount
            
            if balance > peak_balance:
                if current_drawdown > 0:
                    drawdowns.append(current_drawdown)
                peak_balance = balance
                current_drawdown = 0
            else:
                current_drawdown = (peak_balance - balance) / peak_balance * 100
        
        if current_drawdown > 0:
            drawdowns.append(current_drawdown)
        
        return {
            'max_drawdown': max(drawdowns) if drawdowns else 0,
            'avg_drawdown': np.mean(drawdowns) if drawdowns else 0,
            'drawdown_count': len(drawdowns),
            'current_drawdown': current_drawdown
        }
    
    def _analyze_ml_accuracy(self, conn) -> Dict:
        """Analyze ML model performance"""
        # Get recent trades that were likely ML-driven
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN gain_loss_sol > 0 THEN 1 ELSE 0 END) as winners,
                AVG(percentage_change) as avg_return
            FROM trades
            WHERE action = 'SELL'
            AND gain_loss_sol IS NOT NULL
            AND timestamp > datetime('now', '-7 days')
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            return {
                'recent_trades': result[0],
                'recent_win_rate': (result[1] / result[0] * 100) if result[0] > 0 else 0,
                'recent_avg_return': result[2] or 0
            }
        
        return {'recent_trades': 0, 'recent_win_rate': 0, 'recent_avg_return': 0}
    
    def generate_optimization_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate specific optimization recommendations based on analysis"""
        recommendations = []
        
        # 1. Position Sizing Recommendations
        pos_analysis = analysis.get('win_rate_by_position_size')
        if not pos_analysis.empty:
            best_size_range = pos_analysis.loc[pos_analysis['win_rate'].idxmax()]['size_range']
            
            current_default = self.current_params['trading'].get('default_position_size_pct', 4.0)
            
            if best_size_range == '<2%' and current_default > 2:
                recommendations.append({
                    'category': 'Position Sizing',
                    'priority': 'HIGH',
                    'recommendation': 'Reduce position sizes',
                    'action': 'Set default_position_size_pct to 1.5-2%',
                    'reason': f'Best win rate ({pos_analysis.loc[pos_analysis["size_range"] == best_size_range]["win_rate"].values[0]:.1f}%) achieved with smaller positions',
                    'parameter': 'default_position_size_pct',
                    'current_value': current_default,
                    'suggested_value': 1.75
                })
            elif best_size_range == '>5%' and current_default < 5:
                recommendations.append({
                    'category': 'Position Sizing',
                    'priority': 'MEDIUM',
                    'recommendation': 'Increase position sizes',
                    'action': 'Set default_position_size_pct to 5-6%',
                    'reason': f'Best performance with larger positions',
                    'parameter': 'default_position_size_pct',
                    'current_value': current_default,
                    'suggested_value': 5.5
                })
        
        # 2. Trading Hours Optimization
        hourly = analysis.get('win_rate_by_hour')
        if not hourly.empty:
            best_hours = hourly.nlargest(3, 'avg_pnl')['hour'].tolist()
            worst_hours = hourly.nsmallest(3, 'avg_pnl')['hour'].tolist()
            
            if hourly['avg_pnl'].std() > 0.001:  # Significant variation
                recommendations.append({
                    'category': 'Trading Hours',
                    'priority': 'MEDIUM',
                    'recommendation': 'Implement time-based trading',
                    'action': f'Focus trading on hours: {best_hours}',
                    'reason': f'Best performance during these hours, avoid hours: {worst_hours}',
                    'parameter': 'preferred_trading_hours',
                    'current_value': 'all',
                    'suggested_value': best_hours
                })
        
        # 3. Exit Strategy Optimization
        exit_timing = analysis.get('exit_timing', {})
        if exit_timing.get('optimal_hold_hours'):
            current_tp = self.current_params['trading'].get('take_profit_pct', 0.5) * 100
            
            if exit_timing['optimal_hold_hours'] < 2 and current_tp > 30:
                recommendations.append({
                    'category': 'Exit Strategy',
                    'priority': 'HIGH',
                    'recommendation': 'Reduce take profit target',
                    'action': 'Set take_profit_pct to 0.20-0.25 (20-25%)',
                    'reason': f'Best returns achieved in {exit_timing["optimal_hold_hours"]} hours - quick profits work better',
                    'parameter': 'take_profit_pct',
                    'current_value': current_tp / 100,
                    'suggested_value': 0.22
                })
            elif exit_timing['optimal_hold_hours'] > 12 and current_tp < 50:
                recommendations.append({
                    'category': 'Exit Strategy',
                    'priority': 'MEDIUM',
                    'recommendation': 'Increase take profit target',
                    'action': 'Set take_profit_pct to 0.60-0.80 (60-80%)',
                    'reason': 'Longer holds yield better returns',
                    'parameter': 'take_profit_pct',
                    'current_value': current_tp / 100,
                    'suggested_value': 0.70
                })
        
        # 4. Token Selection Criteria
        patterns = analysis.get('token_characteristics', {})
        if patterns:
            current_min_volume = self.current_params['trading'].get('min_volume_24h', 30000)
            
            if patterns.get('winner_avg_volume', 0) > current_min_volume * 2:
                recommendations.append({
                    'category': 'Token Selection',
                    'priority': 'HIGH',
                    'recommendation': 'Increase minimum volume requirement',
                    'action': f'Set min_volume_24h to ${patterns["winner_avg_volume"] * 0.7:,.0f}',
                    'reason': f'Winning trades average ${patterns["winner_avg_volume"]:,.0f} volume vs ${patterns["loser_avg_volume"]:,.0f} for losers',
                    'parameter': 'min_volume_24h',
                    'current_value': current_min_volume,
                    'suggested_value': int(patterns["winner_avg_volume"] * 0.7)
                })
        
        # 5. Risk Management
        drawdown = analysis.get('drawdown_analysis', {})
        if drawdown.get('max_drawdown', 0) > 20:
            current_sl = self.current_params['trading'].get('stop_loss_pct', 0.05) * 100
            
            if current_sl > 5:
                recommendations.append({
                    'category': 'Risk Management',
                    'priority': 'HIGH',
                    'recommendation': 'Tighten stop loss',
                    'action': 'Set stop_loss_pct to 0.03-0.04 (3-4%)',
                    'reason': f'Max drawdown of {drawdown["max_drawdown"]:.1f}% is too high',
                    'parameter': 'stop_loss_pct',
                    'current_value': current_sl / 100,
                    'suggested_value': 0.035
                })
        
        # 6. ML Confidence Threshold
        ml_perf = analysis.get('ml_performance', {})
        current_ml_threshold = self.current_params['trading'].get('ml_confidence_threshold', 0.65)
        
        if ml_perf.get('recent_win_rate', 0) < 60 and ml_perf.get('recent_trades', 0) > 20:
            recommendations.append({
                'category': 'ML Settings',
                'priority': 'HIGH',
                'recommendation': 'Increase ML confidence threshold',
                'action': 'Set ml_confidence_threshold to 0.75-0.80',
                'reason': f'Recent win rate of {ml_perf["recent_win_rate"]:.1f}% is too low',
                'parameter': 'ml_confidence_threshold',
                'current_value': current_ml_threshold,
                'suggested_value': 0.75
            })
        elif ml_perf.get('recent_win_rate', 0) > 85 and ml_perf.get('recent_trades', 0) > 20:
            recommendations.append({
                'category': 'ML Settings',
                'priority': 'MEDIUM',
                'recommendation': 'Decrease ML confidence threshold',
                'action': 'Set ml_confidence_threshold to 0.55-0.60',
                'reason': f'Excellent win rate of {ml_perf["recent_win_rate"]:.1f}% - can trade more opportunities',
                'parameter': 'ml_confidence_threshold',
                'current_value': current_ml_threshold,
                'suggested_value': 0.58
            })
        
        return recommendations
    
    def apply_optimizations(self, recommendations: List[Dict], mode: str = 'simulation'):
        """Apply recommended optimizations to configuration"""
        if not recommendations:
            print(f"{Fore.YELLOW}No optimizations to apply{Style.RESET_ALL}")
            return
        
        # Load current config
        config_file = 'config/trading_params.json'
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {}
        
        # Apply high priority recommendations
        applied = []
        for rec in recommendations:
            if rec['priority'] == 'HIGH' and rec.get('parameter'):
                old_value = config.get(rec['parameter'])
                config[rec['parameter']] = rec['suggested_value']
                applied.append({
                    'parameter': rec['parameter'],
                    'old_value': old_value,
                    'new_value': rec['suggested_value'],
                    'reason': rec['reason']
                })
        
        if applied:
            # Backup current config
            backup_file = f'config/trading_params_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(backup_file, 'w') as f:
                json.dump(self.current_params['trading'], f, indent=2)
            
            # Save new config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n{Fore.GREEN}✅ Applied {len(applied)} optimizations:{Style.RESET_ALL}")
            for opt in applied:
                print(f"  • {opt['parameter']}: {opt['old_value']} → {opt['new_value']}")
                print(f"    Reason: {opt['reason']}")
            
            print(f"\n{Fore.CYAN}Backup saved to: {backup_file}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No HIGH priority optimizations found{Style.RESET_ALL}")
    
    def display_optimization_report(self):
        """Display comprehensive optimization report"""
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔧 TRADING BOT OPTIMIZATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
        
        # Analyze performance
        print(f"{Fore.CYAN}Analyzing performance patterns...{Style.RESET_ALL}")
        analysis = self.analyze_performance_patterns()
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(analysis)
        
        # Display current configuration
        print(f"\n{Fore.CYAN}📋 CURRENT CONFIGURATION{Style.RESET_ALL}")
        print(f"{'─'*50}")
        
        key_params = [
            ('default_position_size_pct', 'Position Size'),
            ('take_profit_pct', 'Take Profit'),
            ('stop_loss_pct', 'Stop Loss'),
            ('ml_confidence_threshold', 'ML Threshold'),
            ('min_volume_24h', 'Min Volume'),
            ('min_liquidity', 'Min Liquidity')
        ]
        
        for param, label in key_params:
            value = self.current_params['trading'].get(param, 'N/A')
            if param.endswith('_pct') and isinstance(value, (int, float)):
                print(f"{label}: {value * 100:.1f}%")
            elif param.startswith('min_') and isinstance(value, (int, float)):
                print(f"{label}: ${value:,.0f}")
            else:
                print(f"{label}: {value}")
        
        # Display analysis results
        print(f"\n{Fore.CYAN}📊 PERFORMANCE ANALYSIS{Style.RESET_ALL}")
        print(f"{'─'*50}")
        
        # Win rate by position size
        pos_analysis = analysis.get('win_rate_by_position_size')
        if not pos_analysis.empty:
            print(f"\n{Fore.WHITE}Position Size Analysis:{Style.RESET_ALL}")
            print(f"{'Size Range':<12} {'Trades':>8} {'Win Rate':>12} {'Avg P&L':>12}")
            print("─" * 45)
            for _, row in pos_analysis.iterrows():
                win_color = Fore.GREEN if row['win_rate'] > 70 else Fore.YELLOW if row['win_rate'] > 50 else Fore.RED
                print(f"{row['size_range']:<12} {int(row['trades']):>8} "
                      f"{win_color}{row['win_rate']:>11.1f}%{Style.RESET_ALL} "
                      f"{row['avg_pnl']:>12.4f}")
        
        # ML Performance
        ml_perf = analysis.get('ml_performance', {})
        if ml_perf.get('recent_trades', 0) > 0:
            print(f"\n{Fore.WHITE}ML Model Performance (Last 7 Days):{Style.RESET_ALL}")
            print(f"Trades: {ml_perf['recent_trades']} | "
                  f"Win Rate: {ml_perf['recent_win_rate']:.1f}% | "
                  f"Avg Return: {ml_perf['recent_avg_return']:.1f}%")
        
        # Risk Metrics
        drawdown = analysis.get('drawdown_analysis', {})
        if drawdown:
            print(f"\n{Fore.WHITE}Risk Metrics:{Style.RESET_ALL}")
            dd_color = Fore.GREEN if drawdown['max_drawdown'] < 10 else Fore.YELLOW if drawdown['max_drawdown'] < 20 else Fore.RED
            print(f"Max Drawdown: {dd_color}{drawdown['max_drawdown']:.1f}%{Style.RESET_ALL} | "
                  f"Avg Drawdown: {drawdown['avg_drawdown']:.1f}% | "
                  f"Drawdown Events: {drawdown['drawdown_count']}")
        
        # Display recommendations
        print(f"\n{Fore.CYAN}💡 OPTIMIZATION RECOMMENDATIONS{Style.RESET_ALL}")
        print(f"{'─'*50}")
        
        if recommendations:
            # Group by priority
            high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
            medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
            low_priority = [r for r in recommendations if r['priority'] == 'LOW']
            
            if high_priority:
                print(f"\n{Fore.RED}🔴 HIGH PRIORITY{Style.RESET_ALL}")
                for i, rec in enumerate(high_priority, 1):
                    print(f"\n{i}. {rec['recommendation']}")
                    print(f"   Category: {rec['category']}")
                    print(f"   Action: {rec['action']}")
                    print(f"   Reason: {rec['reason']}")
            
            if medium_priority:
                print(f"\n{Fore.YELLOW}🟡 MEDIUM PRIORITY{Style.RESET_ALL}")
                for i, rec in enumerate(medium_priority, 1):
                    print(f"\n{i}. {rec['recommendation']}")
                    print(f"   Category: {rec['category']}")
                    print(f"   Action: {rec['action']}")
                    print(f"   Reason: {rec['reason']}")
            
            if low_priority:
                print(f"\n{Fore.GREEN}🟢 LOW PRIORITY{Style.RESET_ALL}")
                for i, rec in enumerate(low_priority, 1):
                    print(f"\n{i}. {rec['recommendation']}")
                    print(f"   Category: {rec['category']}")
                    print(f"   Action: {rec['action']}")
        else:
            print(f"\n{Fore.GREEN}✅ Current configuration appears well-optimized!{Style.RESET_ALL}")
            print("Continue monitoring performance for fine-tuning opportunities.")
        
        # Export option
        print(f"\n{Fore.CYAN}{'─'*100}{Style.RESET_ALL}")
        
        # Save detailed report
        report = {
            'generated_at': datetime.now().isoformat(),
            'current_configuration': self.current_params,
            'analysis_results': {
                'position_size_analysis': pos_analysis.to_dict('records') if not pos_analysis.empty else [],
                'ml_performance': ml_perf,
                'drawdown_analysis': drawdown,
                'exit_timing': analysis.get('exit_timing', {}),
                'token_patterns': analysis.get('token_characteristics', {})
            },
            'recommendations': recommendations
        }
        
        report_file = f'optimization_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n{Fore.GREEN}✅ Full report saved to: {report_file}{Style.RESET_ALL}")
        
        return recommendations
    
    def interactive_optimization(self):
        """Interactive optimization session"""
        print(f"\n{Fore.YELLOW}Would you like to apply HIGH priority optimizations? (y/n):{Style.RESET_ALL} ", end='')
        
        try:
            response = input().lower()
            if response == 'y':
                recommendations = self.display_optimization_report()
                self.apply_optimizations(recommendations)
                
                print(f"\n{Fore.YELLOW}Restart the bot for changes to take effect.{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.CYAN}Optimization report generated without applying changes.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Optimization cancelled.{Style.RESET_ALL}")

def main():
    """Run the optimizer"""
    optimizer = TradingBotOptimizer()
    
    print(f"{Fore.CYAN}Trading Bot Optimizer{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")
    print("\nOptions:")
    print("1. Generate optimization report only")
    print("2. Generate report and apply optimizations")
    print("3. Exit")
    
    try:
        choice = input("\nSelect option (1-3): ")
        
        if choice == '1':
            optimizer.display_optimization_report()
        elif choice == '2':
            optimizer.interactive_optimization()
        else:
            print("Exiting...")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
