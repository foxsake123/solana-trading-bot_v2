#!/usr/bin/env python3
"""
Advanced Performance Dashboard for Solana Trading Bot
Tracks both simulation and real trading with advanced analytics
"""
import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back
import pandas as pd
import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional
import asyncio
import aiohttp

# Initialize colorama
init()

class AdvancedPerformanceDashboard:
    def __init__(self, db_path='data/db/sol_bot.db', real_db_path='data/db/sol_bot_real.db'):
        self.sim_db_path = db_path
        self.real_db_path = real_db_path if os.path.exists(real_db_path) else db_path
        
        # Performance tracking
        self.performance_history = {
            'simulation': deque(maxlen=1000),
            'real': deque(maxlen=1000)
        }
        
        # Detect modes and balances
        self.sim_balance = self._get_initial_balance('simulation')
        self.real_balance = self._get_initial_balance('real')
        
        # Advanced metrics storage
        self.metrics_cache = {}
        self.last_update = datetime.now()
        
        # Real wallet tracking
        self.real_wallet = "16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf"
        self.initial_real_balance = 1.0014
        
    def _get_initial_balance(self, mode: str) -> float:
        """Get initial balance for specified mode"""
        if mode == 'real':
            # Check for real config
            try:
                with open('config/bot_control_real.json', 'r') as f:
                    config = json.load(f)
                    return config.get('starting_balance', 1.0014)
            except:
                return 1.0014
        else:
            # Simulation config
            try:
                with open('config/bot_control.json', 'r') as f:
                    config = json.load(f)
                    return config.get('starting_simulation_balance', 9.05)
            except:
                return 9.05
    
    def get_connection(self, mode: str = 'simulation'):
        """Get database connection for specified mode"""
        db_path = self.real_db_path if mode == 'real' else self.sim_db_path
        return sqlite3.connect(db_path)
    
    def detect_active_modes(self) -> Dict[str, bool]:
        """Detect which modes are actively trading"""
        modes = {'simulation': False, 'real': False}
        
        # Check simulation
        try:
            conn = self.get_connection('simulation')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            recent_sim = cursor.fetchone()[0]
            modes['simulation'] = recent_sim > 0
            conn.close()
        except:
            pass
        
        # Check real
        try:
            conn = self.get_connection('real')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE tx_hash IS NOT NULL 
                AND tx_hash != 'simulated'
                AND timestamp > datetime('now', '-24 hours')
            """)
            recent_real = cursor.fetchone()[0]
            modes['real'] = recent_real > 0
            conn.close()
        except:
            # If no real trades yet, check if bot is running in real mode
            if os.path.exists('data/safety_state.json'):
                with open('data/safety_state.json', 'r') as f:
                    safety = json.load(f)
                    modes['real'] = not safety.get('is_paused', True)
        
        return modes
    
    def calculate_comprehensive_metrics(self, mode: str) -> Dict:
        """Calculate comprehensive metrics for a trading mode"""
        conn = self.get_connection(mode)
        cursor = conn.cursor()
        metrics = {}
        
        try:
            # Get initial balance
            initial_balance = self.real_balance if mode == 'real' else self.sim_balance
            
            # Calculate current balance
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN action='BUY' THEN -amount ELSE amount END) as net_flow
                FROM trades
            """)
            net_flow = cursor.fetchone()[0] or 0
            current_balance = initial_balance + net_flow
            
            # Get open positions
            cursor.execute("""
                SELECT 
                    contract_address,
                    SUM(CASE WHEN action='BUY' THEN amount ELSE -amount END) as net_amount,
                    AVG(CASE WHEN action='BUY' THEN price END) as avg_entry_price,
                    COUNT(CASE WHEN action='BUY' THEN 1 END) as buy_count
                FROM trades
                GROUP BY contract_address
                HAVING net_amount > 0.001
            """)
            
            open_positions = cursor.fetchall()
            position_value = sum(float(pos[1]) for pos in open_positions)
            
            # Performance metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(DISTINCT contract_address) as unique_tokens,
                    COUNT(CASE WHEN action='BUY' THEN 1 END) as total_buys,
                    COUNT(CASE WHEN action='SELL' THEN 1 END) as total_sells,
                    SUM(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN action='SELL' AND gain_loss_sol < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as realized_pnl,
                    MAX(CASE WHEN action='SELL' THEN gain_loss_sol ELSE NULL END) as best_trade,
                    MIN(CASE WHEN action='SELL' THEN gain_loss_sol ELSE NULL END) as worst_trade,
                    AVG(CASE WHEN action='SELL' AND gain_loss_sol > 0 THEN gain_loss_sol END) as avg_win,
                    AVG(CASE WHEN action='SELL' AND gain_loss_sol < 0 THEN gain_loss_sol END) as avg_loss,
                    MAX(CASE WHEN action='SELL' THEN percentage_change ELSE NULL END) as best_pct,
                    MIN(CASE WHEN action='SELL' THEN percentage_change ELSE NULL END) as worst_pct
                FROM trades
            """)
            
            perf = cursor.fetchone()
            
            # Build metrics dictionary
            metrics = {
                'mode': mode,
                'initial_balance': initial_balance,
                'current_balance': current_balance,
                'available_balance': current_balance - position_value,
                'position_value': position_value,
                'open_positions_count': len(open_positions),
                'total_value': current_balance,
                'unrealized_pnl': 0,  # Would need current prices
                'realized_pnl': perf[6] or 0,
                'total_pnl': perf[6] or 0,
                'total_trades': perf[0] or 0,
                'unique_tokens': perf[1] or 0,
                'total_buys': perf[2] or 0,
                'total_sells': perf[3] or 0,
                'wins': perf[4] or 0,
                'losses': perf[5] or 0,
                'best_trade': perf[7] or 0,
                'worst_trade': perf[8] or 0,
                'avg_win': perf[9] or 0,
                'avg_loss': perf[10] or 0,
                'best_pct': perf[11] or 0,
                'worst_pct': perf[12] or 0,
                'win_rate': 0,
                'risk_reward': 0,
                'profit_factor': 0,
                'expectancy': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
            
            # Calculate derived metrics
            total_completed = metrics['wins'] + metrics['losses']
            if total_completed > 0:
                metrics['win_rate'] = (metrics['wins'] / total_completed) * 100
                
                if metrics['avg_loss'] != 0:
                    metrics['risk_reward'] = abs(metrics['avg_win'] / metrics['avg_loss'])
                
                # Profit factor
                total_wins_value = metrics['wins'] * abs(metrics['avg_win']) if metrics['avg_win'] else 0
                total_losses_value = metrics['losses'] * abs(metrics['avg_loss']) if metrics['avg_loss'] else 0
                metrics['profit_factor'] = total_wins_value / total_losses_value if total_losses_value > 0 else 0
                
                # Expectancy
                win_prob = metrics['win_rate'] / 100
                loss_prob = 1 - win_prob
                metrics['expectancy'] = (win_prob * abs(metrics['avg_win'])) - (loss_prob * abs(metrics['avg_loss']))
            
            # Time-based metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as trades_24h,
                    SUM(CASE WHEN action='SELL' THEN gain_loss_sol ELSE 0 END) as pnl_24h,
                    COUNT(CASE WHEN action='BUY' THEN 1 END) as buys_24h
                FROM trades
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            
            time_metrics = cursor.fetchone()
            metrics['trades_24h'] = time_metrics[0] or 0
            metrics['pnl_24h'] = time_metrics[1] or 0
            metrics['buys_24h'] = time_metrics[2] or 0
            
            # Position sizing analysis
            cursor.execute("""
                SELECT 
                    AVG(amount) as avg_position_size,
                    MIN(amount) as min_position_size,
                    MAX(amount) as max_position_size,
                    AVG(amount * 100.0 / ?) as avg_position_pct
                FROM trades
                WHERE action='BUY'
            """, (initial_balance,))
            
            pos_metrics = cursor.fetchone()
            metrics['avg_position_size'] = pos_metrics[0] or 0
            metrics['min_position_size'] = pos_metrics[1] or 0
            metrics['max_position_size'] = pos_metrics[2] or 0
            metrics['avg_position_pct'] = pos_metrics[3] or 0
            
            # Calculate max drawdown
            metrics['max_drawdown'] = self._calculate_max_drawdown(conn, initial_balance)
            
            # ML performance
            metrics['ml_accuracy'] = self._calculate_ml_accuracy(conn)
            
            return metrics
            
        except Exception as e:
            print(f"{Fore.RED}Error calculating metrics for {mode}: {e}{Style.RESET_ALL}")
            return {}
        finally:
            conn.close()
    
    def _calculate_max_drawdown(self, conn, initial_balance: float) -> float:
        """Calculate maximum drawdown"""
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                action,
                amount,
                gain_loss_sol
            FROM trades
            ORDER BY timestamp
        """)
        
        trades = cursor.fetchall()
        balance = initial_balance
        peak_balance = initial_balance
        max_drawdown = 0
        
        for timestamp, action, amount, gain_loss in trades:
            if action == 'BUY':
                balance -= amount
            elif action == 'SELL':
                balance += amount
            
            if balance > peak_balance:
                peak_balance = balance
            
            drawdown = (peak_balance - balance) / peak_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown * 100  # Return as percentage
    
    def _calculate_ml_accuracy(self, conn) -> float:
        """Estimate ML accuracy from trade outcomes"""
        cursor = conn.cursor()
        
        # Look for trades in last 100 that were likely ML-driven
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN gain_loss_sol > 0 THEN 1 END) as ml_wins,
                COUNT(*) as ml_total
            FROM (
                SELECT gain_loss_sol
                FROM trades
                WHERE action = 'SELL'
                AND gain_loss_sol IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 100
            )
        """)
        
        result = cursor.fetchone()
        if result and result[1] > 0:
            return (result[0] / result[1]) * 100
        return 0
    
    def get_comparative_analysis(self) -> Dict:
        """Compare simulation vs real performance"""
        sim_metrics = self.calculate_comprehensive_metrics('simulation')
        real_metrics = self.calculate_comprehensive_metrics('real')
        
        comparison = {
            'win_rate_diff': real_metrics.get('win_rate', 0) - sim_metrics.get('win_rate', 0),
            'risk_reward_diff': real_metrics.get('risk_reward', 0) - sim_metrics.get('risk_reward', 0),
            'avg_position_diff': real_metrics.get('avg_position_size', 0) - sim_metrics.get('avg_position_size', 0),
            'pnl_correlation': self._calculate_correlation(sim_metrics, real_metrics)
        }
        
        return comparison
    
    def _calculate_correlation(self, sim: Dict, real: Dict) -> float:
        """Calculate correlation between sim and real performance"""
        # Simplified correlation based on win rates and risk/reward
        if sim.get('total_trades', 0) > 10 and real.get('total_trades', 0) > 10:
            sim_score = sim.get('win_rate', 0) * sim.get('risk_reward', 1)
            real_score = real.get('win_rate', 0) * real.get('risk_reward', 1)
            
            if sim_score > 0:
                return min(real_score / sim_score, 2.0)  # Cap at 200%
        return 0
    
    def get_risk_analysis(self, mode: str) -> Dict:
        """Analyze risk metrics for a mode"""
        metrics = self.calculate_comprehensive_metrics(mode)
        
        risk_analysis = {
            'current_risk_level': 'LOW',
            'position_concentration': 0,
            'daily_loss_risk': 0,
            'recommendations': []
        }
        
        # Position concentration risk
        if metrics['available_balance'] > 0:
            risk_analysis['position_concentration'] = (metrics['position_value'] / 
                                                      (metrics['available_balance'] + metrics['position_value'])) * 100
        
        # Daily loss risk
        if metrics['pnl_24h'] < -0.05:  # Lost more than 0.05 SOL in 24h
            risk_analysis['daily_loss_risk'] = abs(metrics['pnl_24h'])
            risk_analysis['current_risk_level'] = 'MEDIUM'
        
        # Risk level assessment
        if risk_analysis['position_concentration'] > 70:
            risk_analysis['current_risk_level'] = 'HIGH'
            risk_analysis['recommendations'].append("Reduce position concentration")
        
        if metrics['max_drawdown'] > 20:
            risk_analysis['current_risk_level'] = 'HIGH'
            risk_analysis['recommendations'].append("Review stop loss settings")
        
        if metrics['win_rate'] < 50 and metrics['total_trades'] > 20:
            risk_analysis['recommendations'].append("Review entry criteria")
        
        if metrics['avg_position_pct'] > 5:
            risk_analysis['recommendations'].append("Consider reducing position sizes")
        
        return risk_analysis
    
    def get_ml_performance_analysis(self) -> Dict:
        """Analyze ML model performance"""
        analysis = {
            'simulation_ml_accuracy': 0,
            'real_ml_accuracy': 0,
            'ml_confidence_analysis': {},
            'ml_recommendations': []
        }
        
        # Get ML accuracy for both modes
        sim_metrics = self.calculate_comprehensive_metrics('simulation')
        real_metrics = self.calculate_comprehensive_metrics('real')
        
        analysis['simulation_ml_accuracy'] = sim_metrics.get('ml_accuracy', 0)
        analysis['real_ml_accuracy'] = real_metrics.get('ml_accuracy', 0)
        
        # Analyze ML confidence thresholds
        for mode in ['simulation', 'real']:
            conn = self.get_connection(mode)
            cursor = conn.cursor()
            
            # This would need ML confidence tracking in database
            # For now, use win rate as proxy
            metrics = sim_metrics if mode == 'simulation' else real_metrics
            
            if metrics.get('win_rate', 0) > 80:
                analysis['ml_recommendations'].append(f"Lower ML threshold in {mode} mode")
            elif metrics.get('win_rate', 0) < 60:
                analysis['ml_recommendations'].append(f"Increase ML threshold in {mode} mode")
            
            conn.close()
        
        return analysis
    
    def display_advanced_dashboard(self):
        """Display the advanced performance dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Detect active modes
        active_modes = self.detect_active_modes()
        
        # Get metrics for active modes
        sim_metrics = self.calculate_comprehensive_metrics('simulation') if active_modes['simulation'] else {}
        real_metrics = self.calculate_comprehensive_metrics('real') if active_modes['real'] else {}
        
        # Header
        print(f"{Fore.CYAN}{Back.BLACK}{'='*140}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚀 ADVANCED SOLANA TRADING BOT DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{'='*140}{Style.RESET_ALL}\n")
        
        # Active modes indicator
        sim_status = f"{Fore.GREEN}● ACTIVE{Style.RESET_ALL}" if active_modes['simulation'] else f"{Fore.RED}● INACTIVE{Style.RESET_ALL}"
        real_status = f"{Fore.GREEN}● ACTIVE{Style.RESET_ALL}" if active_modes['real'] else f"{Fore.RED}● INACTIVE{Style.RESET_ALL}"
        
        print(f"Trading Modes: Simulation {sim_status}  |  Real {real_status}")
        print(f"{'─'*140}\n")
        
        # Display metrics for each active mode
        for mode, metrics in [('SIMULATION', sim_metrics), ('REAL', real_metrics)]:
            if not metrics:
                continue
            
            mode_color = Fore.CYAN if mode == 'SIMULATION' else Fore.MAGENTA
            print(f"{mode_color}{'='*60} {mode} MODE {'='*60}{Style.RESET_ALL}\n")
            
            # Balance section
            total_value = metrics['current_balance']
            pnl = metrics['total_pnl']
            pnl_pct = (pnl / metrics['initial_balance']) * 100 if metrics['initial_balance'] > 0 else 0
            balance_color = Fore.GREEN if pnl >= 0 else Fore.RED
            
            print(f"{Fore.WHITE}💰 BALANCE & P&L{Style.RESET_ALL}")
            print(f"┌{'─'*45}┬{'─'*45}┬{'─'*45}┐")
            print(f"│ Total Value: {balance_color}{total_value:>20.4f} SOL{Style.RESET_ALL}    │"
                  f" Available: {metrics['available_balance']:>22.4f} SOL    │"
                  f" In Positions: {metrics['position_value']:>19.4f} SOL    │")
            print(f"│ Initial: {metrics['initial_balance']:>24.4f} SOL    │"
                  f" Realized P&L: {balance_color}{pnl:>19.4f} SOL{Style.RESET_ALL}    │"
                  f" P&L %: {balance_color}{pnl_pct:>23.1f}%{Style.RESET_ALL}    │")
            print(f"└{'─'*45}┴{'─'*45}┴{'─'*45}┘\n")
            
            # Performance metrics
            print(f"{Fore.WHITE}📊 PERFORMANCE METRICS{Style.RESET_ALL}")
            win_color = Fore.GREEN if metrics['win_rate'] > 65 else Fore.YELLOW if metrics['win_rate'] > 50 else Fore.RED
            
            print(f"Win Rate: {win_color}{metrics['win_rate']:.1f}%{Style.RESET_ALL} ({metrics['wins']}W/{metrics['losses']}L) | "
                  f"Risk/Reward: {metrics['risk_reward']:.2f}:1 | "
                  f"Profit Factor: {metrics['profit_factor']:.2f} | "
                  f"Expectancy: {metrics['expectancy']:.4f} SOL")
            
            print(f"Best Trade: {Fore.GREEN}+{metrics['best_trade']:.4f} SOL ({metrics['best_pct']:.1f}%){Style.RESET_ALL} | "
                  f"Worst: {Fore.RED}{metrics['worst_trade']:.4f} SOL ({metrics['worst_pct']:.1f}%){Style.RESET_ALL} | "
                  f"Max Drawdown: {metrics['max_drawdown']:.1f}%\n")
            
            # Position sizing
            print(f"{Fore.WHITE}📏 POSITION SIZING{Style.RESET_ALL}")
            print(f"Average: {metrics['avg_position_size']:.4f} SOL ({metrics['avg_position_pct']:.1f}%) | "
                  f"Range: {metrics['min_position_size']:.4f} - {metrics['max_position_size']:.4f} SOL\n")
            
            # 24h Performance
            pnl_24h_color = Fore.GREEN if metrics['pnl_24h'] > 0 else Fore.RED
            print(f"{Fore.WHITE}📈 LAST 24 HOURS{Style.RESET_ALL}")
            print(f"Trades: {metrics['trades_24h']} ({metrics['buys_24h']} buys) | "
                  f"P&L: {pnl_24h_color}{metrics['pnl_24h']:+.4f} SOL{Style.RESET_ALL}\n")
            
            # Risk analysis
            risk = self.get_risk_analysis(mode.lower())
            risk_color = Fore.GREEN if risk['current_risk_level'] == 'LOW' else Fore.YELLOW if risk['current_risk_level'] == 'MEDIUM' else Fore.RED
            print(f"{Fore.WHITE}⚠️  RISK ANALYSIS{Style.RESET_ALL}")
            print(f"Risk Level: {risk_color}{risk['current_risk_level']}{Style.RESET_ALL} | "
                  f"Position Concentration: {risk['position_concentration']:.1f}%")
            
            if risk['recommendations']:
                print("Recommendations: " + " • ".join(risk['recommendations']))
            
            print()
        
        # Comparative analysis if both modes active
        if active_modes['simulation'] and active_modes['real']:
            print(f"\n{Fore.YELLOW}{'='*60} COMPARATIVE ANALYSIS {'='*60}{Style.RESET_ALL}\n")
            
            comparison = self.get_comparative_analysis()
            
            # Win rate comparison
            wr_color = Fore.GREEN if comparison['win_rate_diff'] > 0 else Fore.RED
            print(f"Win Rate Difference (Real vs Sim): {wr_color}{comparison['win_rate_diff']:+.1f}%{Style.RESET_ALL}")
            
            # Risk/Reward comparison
            rr_color = Fore.GREEN if comparison['risk_reward_diff'] > 0 else Fore.RED
            print(f"Risk/Reward Difference: {rr_color}{comparison['risk_reward_diff']:+.2f}{Style.RESET_ALL}")
            
            # Correlation
            corr = comparison['pnl_correlation']
            corr_assessment = "Strong" if corr > 0.8 else "Moderate" if corr > 0.5 else "Weak"
            print(f"Performance Correlation: {corr:.1%} ({corr_assessment})")
            
            print()
        
        # ML Analysis
        ml_analysis = self.get_ml_performance_analysis()
        print(f"\n{Fore.CYAN}🤖 ML MODEL PERFORMANCE{Style.RESET_ALL}")
        print(f"Simulation Accuracy: ~{ml_analysis['simulation_ml_accuracy']:.1f}% | "
              f"Real Accuracy: ~{ml_analysis['real_ml_accuracy']:.1f}%")
        
        if ml_analysis['ml_recommendations']:
            print("ML Recommendations: " + " • ".join(ml_analysis['ml_recommendations']))
        
        # Footer with key insights
        print(f"\n{Fore.CYAN}{'─'*140}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 KEY INSIGHTS & ACTIONS{Style.RESET_ALL}\n")
        
        # Dynamic insights based on current performance
        insights = []
        
        # Real mode specific insights
        if active_modes['real'] and real_metrics:
            if real_metrics['available_balance'] < 0.2:
                insights.append(f"{Fore.RED}⚠️  CRITICAL: Real balance very low ({real_metrics['available_balance']:.4f} SOL) - add funds or reduce positions{Style.RESET_ALL}")
            
            if real_metrics['win_rate'] > 75 and real_metrics['avg_position_size'] < 0.03:
                insights.append(f"{Fore.GREEN}✨ Real mode win rate excellent ({real_metrics['win_rate']:.1f}%) - consider increasing position sizes{Style.RESET_ALL}")
            
            if real_metrics['pnl_24h'] < -0.05:
                insights.append(f"{Fore.YELLOW}⚡ Monitor closely - real mode lost {abs(real_metrics['pnl_24h']):.4f} SOL in last 24h{Style.RESET_ALL}")
        
        # Simulation insights
        if active_modes['simulation'] and sim_metrics:
            if sim_metrics['best_pct'] > 1000:
                insights.append(f"{Fore.GREEN}🚀 Simulation found {sim_metrics['best_pct']:.0f}% gain - strategy working well{Style.RESET_ALL}")
        
        # General insights
        if len(insights) == 0:
            insights.append(f"{Fore.GREEN}✅ All systems operating normally{Style.RESET_ALL}")
        
        for insight in insights:
            print(f"  {insight}")
        
        # Safety state if in real mode
        if active_modes['real']:
            try:
                with open('data/safety_state.json', 'r') as f:
                    safety = json.load(f)
                    if safety.get('is_paused'):
                        print(f"\n{Fore.RED}🚨 SAFETY: Real trading is PAUSED - {safety.get('pause_reason', 'Unknown reason')}{Style.RESET_ALL}")
            except:
                pass
    
    def export_detailed_report(self):
        """Export detailed performance report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'active_modes': self.detect_active_modes(),
            'simulation_metrics': self.calculate_comprehensive_metrics('simulation'),
            'real_metrics': self.calculate_comprehensive_metrics('real'),
            'comparative_analysis': self.get_comparative_analysis(),
            'ml_analysis': self.get_ml_performance_analysis(),
            'risk_analysis': {
                'simulation': self.get_risk_analysis('simulation'),
                'real': self.get_risk_analysis('real')
            },
            'wallet_address': self.real_wallet
        }
        
        filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n{Fore.GREEN}✅ Detailed report exported to {filename}{Style.RESET_ALL}")
        
        # Also create a human-readable summary
        self._export_summary_report(report)
    
    def _export_summary_report(self, report: Dict):
        """Export human-readable summary"""
        filename = f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w') as f:
            f.write("SOLANA TRADING BOT PERFORMANCE SUMMARY\n")
            f.write(f"Generated: {report['generated_at']}\n")
            f.write("="*60 + "\n\n")
            
            # Real mode summary
            if report['real_metrics']:
                rm = report['real_metrics']
                f.write("REAL TRADING PERFORMANCE\n")
                f.write(f"Balance: {rm['current_balance']:.4f} SOL (Started: {rm['initial_balance']:.4f})\n")
                f.write(f"P&L: {rm['total_pnl']:+.4f} SOL ({(rm['total_pnl']/rm['initial_balance']*100):+.1f}%)\n")
                f.write(f"Win Rate: {rm['win_rate']:.1f}% ({rm['wins']}W/{rm['losses']}L)\n")
                f.write(f"Risk/Reward: {rm['risk_reward']:.2f}:1\n")
                f.write(f"Best Trade: +{rm['best_trade']:.4f} SOL ({rm['best_pct']:.1f}%)\n")
                f.write("\n")
            
            # Simulation summary
            if report['simulation_metrics']:
                sm = report['simulation_metrics']
                f.write("SIMULATION PERFORMANCE\n")
                f.write(f"Balance: {sm['current_balance']:.4f} SOL (Started: {sm['initial_balance']:.4f})\n")
                f.write(f"P&L: {sm['total_pnl']:+.4f} SOL ({(sm['total_pnl']/sm['initial_balance']*100):+.1f}%)\n")
                f.write(f"Win Rate: {sm['win_rate']:.1f}% ({sm['wins']}W/{sm['losses']}L)\n")
                f.write(f"Risk/Reward: {sm['risk_reward']:.2f}:1\n")
                f.write("\n")
            
            # Key recommendations
            f.write("KEY RECOMMENDATIONS\n")
            for mode in ['real', 'simulation']:
                if report['risk_analysis'][mode].get('recommendations'):
                    f.write(f"\n{mode.upper()}:\n")
                    for rec in report['risk_analysis'][mode]['recommendations']:
                        f.write(f"- {rec}\n")
        
        print(f"{Fore.GREEN}✅ Summary report exported to {filename}{Style.RESET_ALL}")
    
    def run(self):
        """Run the advanced dashboard"""
        print(f"{Fore.CYAN}Starting Advanced Performance Dashboard...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Commands: [Q]uit | [E]xport Report | [R]efresh{Style.RESET_ALL}\n")
        
        time.sleep(2)
        
        while True:
            try:
                self.display_advanced_dashboard()
                
                # Non-blocking keyboard input
                if os.name == 'nt':  # Windows
                    import msvcrt
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                        if key == 'Q':
                            break
                        elif key == 'E':
                            self.export_detailed_report()
                            time.sleep(3)
                        elif key == 'R':
                            continue
                
                time.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Dashboard stopped.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

if __name__ == "__main__":
    dashboard = AdvancedPerformanceDashboard()
    dashboard.run()
