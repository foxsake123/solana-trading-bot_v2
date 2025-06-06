#!/usr/bin/env python3
"""
Citadel-Inspired Advanced Risk Management System
Implements sophisticated risk metrics and portfolio optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class CitadelRiskManager:
    """Advanced risk management system inspired by Citadel's approach"""
    
    def __init__(self, config: Dict, db):
        self.config = config
        self.db = db
        self.risk_config = config.get('citadel_mode', {}).get('risk_metrics', {})
        
        # Risk limits
        self.var_confidence = self.risk_config.get('var_confidence', 0.95)
        self.cvar_confidence = self.risk_config.get('cvar_confidence', 0.95)
        self.sharpe_target = self.risk_config.get('sharpe_target', 2.0)
        self.sortino_target = self.risk_config.get('sortino_target', 3.0)
        self.max_leverage = self.risk_config.get('max_leverage', 2.0)
        self.correlation_limit = self.risk_config.get('correlation_limit', 0.7)
        
        # Risk tracking
        self.risk_metrics = {
            'var_1d': 0.0,
            'cvar_1d': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'correlation_matrix': None,
            'beta_to_market': 0.0,
            'volatility': 0.0,
            'downside_volatility': 0.0,
            'last_update': datetime.now()
        }
        
        # Portfolio optimization parameters
        self.optimization_window = 30  # days
        self.rebalance_threshold = 0.1  # 10% deviation triggers rebalance
        
    async def assess_portfolio_risk(self, positions: Dict, market_data: Dict) -> Dict:
        """Comprehensive portfolio risk assessment"""
        
        if not positions:
            return {
                'risk_score': 0.0,
                'can_trade': True,
                'warnings': [],
                'metrics': self.risk_metrics
            }
        
        # Get returns data
        returns_data = await self._get_portfolio_returns(positions)
        
        if returns_data.empty:
            return {
                'risk_score': 0.0,
                'can_trade': True,
                'warnings': ['Insufficient data for risk assessment'],
                'metrics': self.risk_metrics
            }
        
        # Calculate risk metrics
        self._update_risk_metrics(returns_data, market_data)
        
        # Assess risk levels
        risk_assessment = self._assess_risk_levels()
        
        # Check correlations
        correlation_risk = self._check_correlations(positions)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(risk_assessment, correlation_risk)
        
        # Determine if we can trade
        can_trade = risk_score < 0.8 and not any(assessment['critical'] for assessment in risk_assessment.values())
        
        # Generate warnings
        warnings = self._generate_warnings(risk_assessment, correlation_risk)
        
        return {
            'risk_score': risk_score,
            'can_trade': can_trade,
            'warnings': warnings,
            'metrics': self.risk_metrics,
            'assessment_details': risk_assessment,
            'optimization_needed': self._needs_rebalancing(positions)
        }
    
    def calculate_position_size_advanced(self, 
                                       signal_strength: float,
                                       token_volatility: float,
                                       portfolio_value: float,
                                       current_positions: Dict) -> float:
        """Calculate position size using Kelly Criterion and risk parity"""
        
        # Base position size from config
        base_size_pct = self.config.get('default_position_size_pct', 3.0)
        
        # Kelly Criterion adjustment
        kelly_fraction = self._calculate_kelly_fraction(signal_strength, token_volatility)
        
        # Risk parity adjustment
        risk_parity_weight = self._calculate_risk_parity_weight(
            token_volatility, 
            current_positions
        )
        
        # Combine methods
        position_size_pct = base_size_pct * kelly_fraction * risk_parity_weight
        
        # Apply limits
        min_size_pct = self.config.get('min_position_size_pct', 2.0)
        max_size_pct = self.config.get('max_position_size_pct', 5.0)
        
        position_size_pct = np.clip(position_size_pct, min_size_pct, max_size_pct)
        
        # Convert to SOL amount
        position_size = portfolio_value * (position_size_pct / 100.0)
        
        # Check against portfolio risk limits
        if self._would_exceed_risk_limits(position_size, current_positions):
            position_size *= 0.5  # Reduce size if risk limits would be exceeded
        
        return position_size
    
    def _calculate_kelly_fraction(self, signal_strength: float, volatility: float) -> float:
        """Calculate Kelly fraction for position sizing"""
        # Simplified Kelly criterion
        # f = (p*b - q)/b where p=win_prob, q=loss_prob, b=win/loss ratio
        
        win_prob = 0.5 + signal_strength * 0.3  # Convert signal to probability
        loss_prob = 1 - win_prob
        
        # Assume win/loss ratio based on historical performance
        win_loss_ratio = 3.57  # From your historical data
        
        kelly_f = (win_prob * win_loss_ratio - loss_prob) / win_loss_ratio
        
        # Apply Kelly fraction with safety factor
        safety_factor = 0.25  # Use 25% of Kelly
        kelly_fraction = max(0, kelly_f * safety_factor)
        
        # Adjust for volatility
        vol_adjustment = 1 / (1 + volatility * 10)  # Higher vol = smaller position
        
        return kelly_fraction * vol_adjustment
    
    def _calculate_risk_parity_weight(self, token_volatility: float, positions: Dict) -> float:
        """Calculate risk parity weight for the new position"""
        if not positions:
            return 1.0
        
        # Get volatilities of current positions
        position_vols = []
        for pos in positions.values():
            position_vols.append(pos.get('volatility', 0.2))  # Default 20% vol
        
        # Calculate average volatility
        avg_volatility = np.mean(position_vols) if position_vols else token_volatility
        
        # Risk parity weight inversely proportional to volatility
        risk_parity_weight = avg_volatility / token_volatility if token_volatility > 0 else 1.0
        
        # Limit adjustment
        return np.clip(risk_parity_weight, 0.5, 2.0)
    
    def _update_risk_metrics(self, returns_data: pd.DataFrame, market_data: Dict):
        """Update all risk metrics"""
        
        # Basic statistics
        returns = returns_data['portfolio_return'].values
        self.risk_metrics['volatility'] = np.std(returns) * np.sqrt(252)
        
        # VaR and CVaR
        self.risk_metrics['var_1d'] = self._calculate_var(returns, self.var_confidence)
        self.risk_metrics['cvar_1d'] = self._calculate_cvar(returns, self.cvar_confidence)
        
        # Sharpe and Sortino ratios
        self.risk_metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(returns)
        self.risk_metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns)
        
        # Maximum drawdown
        self.risk_metrics['max_drawdown'] = self._calculate_max_drawdown(returns_data)
        
        # Downside volatility
        negative_returns = returns[returns < 0]
        self.risk_metrics['downside_volatility'] = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        # Beta to market
        if 'market_return' in market_data:
            self.risk_metrics['beta_to_market'] = self._calculate_beta(
                returns, 
                market_data['market_return']
            )
        
        self.risk_metrics['last_update'] = datetime.now()
    
    def _calculate_var(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate Value at Risk"""
        return np.percentile(returns, (1 - confidence) * 100) * np.sqrt(252)
    
    def _calculate_cvar(self, returns: np.ndarray, confidence: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var = self._calculate_var(returns, confidence)
        return np.mean(returns[returns <= var]) * np.sqrt(252)
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns) * 252
        volatility = np.std(returns) * np.sqrt(252)
        
        return mean_return / volatility if volatility > 0 else 0.0
    
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns) * 252
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_vol = np.std(downside_returns) * np.sqrt(252)
        
        return mean_return / downside_vol if downside_vol > 0 else 0.0
    
    def _calculate_max_drawdown(self, returns_data: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns_data['portfolio_return']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        return abs(drawdown.min())
    
    def _calculate_beta(self, returns: np.ndarray, market_returns: np.ndarray) -> float:
        """Calculate beta to market"""
        if len(returns) != len(market_returns) or len(returns) < 2:
            return 1.0
        
        covariance = np.cov(returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        return covariance / market_variance if market_variance > 0 else 1.0
    
    def _assess_risk_levels(self) -> Dict[str, Dict]:
        """Assess if risk metrics are within acceptable ranges"""
        assessments = {}
        
        # VaR assessment
        var_limit = 0.05  # 5% daily VaR limit
        assessments['var'] = {
            'value': self.risk_metrics['var_1d'],
            'limit': var_limit,
            'exceeded': abs(self.risk_metrics['var_1d']) > var_limit,
            'critical': abs(self.risk_metrics['var_1d']) > var_limit * 1.5
        }
        
        # Sharpe ratio assessment
        assessments['sharpe'] = {
            'value': self.risk_metrics['sharpe_ratio'],
            'target': self.sharpe_target,
            'below_target': self.risk_metrics['sharpe_ratio'] < self.sharpe_target,
            'critical': self.risk_metrics['sharpe_ratio'] < 0.5
        }
        
        # Drawdown assessment
        dd_limit = 0.15  # 15% max drawdown
        assessments['drawdown'] = {
            'value': self.risk_metrics['max_drawdown'],
            'limit': dd_limit,
            'exceeded': self.risk_metrics['max_drawdown'] > dd_limit,
            'critical': self.risk_metrics['max_drawdown'] > dd_limit * 1.5
        }
        
        # Volatility assessment
        vol_limit = 0.50  # 50% annualized volatility
        assessments['volatility'] = {
            'value': self.risk_metrics['volatility'],
            'limit': vol_limit,
            'exceeded': self.risk_metrics['volatility'] > vol_limit,
            'critical': self.risk_metrics['volatility'] > vol_limit * 1.5
        }
        
        return assessments
    
    def _check_correlations(self, positions: Dict) -> Dict:
        """Check portfolio correlations"""
        if len(positions) < 2:
            return {'high_correlations': [], 'avg_correlation': 0.0}
        
        # Get correlation matrix from database or calculate
        correlation_matrix = self._get_correlation_matrix(list(positions.keys()))
        
        # Find high correlations
        high_correlations = []
        total_correlation = 0
        count = 0
        
        for i in range(len(correlation_matrix)):
            for j in range(i + 1, len(correlation_matrix)):
                corr = correlation_matrix[i, j]
                total_correlation += abs(corr)
                count += 1
                
                if abs(corr) > self.correlation_limit:
                    high_correlations.append({
                        'pair': (list(positions.keys())[i], list(positions.keys())[j]),
                        'correlation': corr
                    })
        
        avg_correlation = total_correlation / count if count > 0 else 0
        
        return {
            'high_correlations': high_correlations,
            'avg_correlation': avg_correlation,
            'concentration_risk': avg_correlation > 0.5
        }
    
    def _calculate_risk_score(self, risk_assessment: Dict, correlation_risk: Dict) -> float:
        """Calculate overall risk score (0-1)"""
        score = 0.0
        
        # Risk metric contributions
        if risk_assessment['var']['exceeded']:
            score += 0.2
        if risk_assessment['var']['critical']:
            score += 0.1
        
        if risk_assessment['sharpe']['below_target']:
            score += 0.15
        if risk_assessment['sharpe']['critical']:
            score += 0.1
        
        if risk_assessment['drawdown']['exceeded']:
            score += 0.2
        if risk_assessment['drawdown']['critical']:
            score += 0.1
        
        if risk_assessment['volatility']['exceeded']:
            score += 0.1
        
        # Correlation risk
        if correlation_risk['concentration_risk']:
            score += 0.2
        
        if len(correlation_risk['high_correlations']) > 0:
            score += 0.1 * min(len(correlation_risk['high_correlations']) / 3, 1)
        
        return min(score, 1.0)
    
    def _generate_warnings(self, risk_assessment: Dict, correlation_risk: Dict) -> List[str]:
        """Generate risk warnings"""
        warnings = []
        
        if risk_assessment['var']['exceeded']:
            warnings.append(f"VaR exceeds limit: {abs(risk_assessment['var']['value']):.2%} > {risk_assessment['var']['limit']:.2%}")
        
        if risk_assessment['sharpe']['below_target']:
            warnings.append(f"Sharpe ratio below target: {risk_assessment['sharpe']['value']:.2f} < {self.sharpe_target}")
        
        if risk_assessment['drawdown']['exceeded']:
            warnings.append(f"Max drawdown exceeds limit: {risk_assessment['drawdown']['value']:.2%}")
        
        if risk_assessment['volatility']['exceeded']:
            warnings.append(f"Portfolio volatility high: {risk_assessment['volatility']['value']:.2%}")
        
        if correlation_risk['concentration_risk']:
            warnings.append(f"High portfolio concentration: avg correlation {correlation_risk['avg_correlation']:.2f}")
        
        for high_corr in correlation_risk['high_correlations']:
            warnings.append(f"High correlation between {high_corr['pair'][0][:8]} and {high_corr['pair'][1][:8]}: {high_corr['correlation']:.2f}")
        
        return warnings
    
    def _would_exceed_risk_limits(self, new_position_size: float, current_positions: Dict) -> bool:
        """Check if new position would exceed risk limits"""
        # Calculate total exposure
        total_exposure = sum(pos['amount'] for pos in current_positions.values())
        total_exposure += new_position_size
        
        # Check leverage
        portfolio_value = self._get_portfolio_value()
        leverage = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        if leverage > self.max_leverage:
            return True
        
        # Check position count
        if len(current_positions) >= self.config.get('max_open_positions', 10):
            return True
        
        return False
    
    def _needs_rebalancing(self, positions: Dict) -> bool:
        """Check if portfolio needs rebalancing"""
        if not positions:
            return False
        
        # Calculate target weights (equal weight for simplicity)
        target_weight = 1.0 / len(positions)
        
        # Check deviation from targets
        total_value = sum(pos['amount'] * pos.get('current_price', 1.0) for pos in positions.values())
        
        for position in positions.values():
            current_value = position['amount'] * position.get('current_price', 1.0)
            current_weight = current_value / total_value if total_value > 0 else 0
            
            if abs(current_weight - target_weight) > self.rebalance_threshold:
                return True
        
        return False
    
    async def optimize_portfolio(self, positions: Dict, market_data: Dict) -> Dict:
        """Optimize portfolio using mean-variance optimization"""
        if len(positions) < 2:
            return {'optimized': False, 'reason': 'Insufficient positions'}
        
        # Get historical returns
        returns_matrix = await self._get_returns_matrix(positions)
        
        if returns_matrix.empty:
            return {'optimized': False, 'reason': 'Insufficient data'}
        
        # Calculate expected returns and covariance
        expected_returns = returns_matrix.mean() * 252
        cov_matrix = returns_matrix.cov() * 252
        
        # Optimization constraints
        n_assets = len(positions)
        initial_weights = np.array([1/n_assets] * n_assets)
        
        # Constraints: weights sum to 1, all weights between 0 and 0.3
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
        ]
        bounds = [(0, 0.3) for _ in range(n_assets)]
        
        # Objective: maximize Sharpe ratio
        def neg_sharpe(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
        
        # Optimize
        result = minimize(
            neg_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x
            
            # Calculate new positions
            total_value = sum(pos['amount'] * pos.get('current_price', 1.0) for pos in positions.values())
            
            recommendations = {}
            for i, (token, position) in enumerate(positions.items()):
                target_value = total_value * optimal_weights[i]
                current_value = position['amount'] * position.get('current_price', 1.0)
                
                change_pct = (target_value - current_value) / current_value if current_value > 0 else 0
                
                recommendations[token] = {
                    'current_weight': current_value / total_value if total_value > 0 else 0,
                    'optimal_weight': optimal_weights[i],
                    'action': 'increase' if change_pct > 0.1 else 'decrease' if change_pct < -0.1 else 'hold',
                    'change_pct': change_pct
                }
            
            return {
                'optimized': True,
                'recommendations': recommendations,
                'expected_sharpe': -result.fun
            }
        
        return {'optimized': False, 'reason': 'Optimization failed'}
    
    async def _get_portfolio_returns(self, positions: Dict) -> pd.DataFrame:
        """Get portfolio returns from database"""
        # This would query your database
        # Returning mock structure for now
        return pd.DataFrame()
    
    def _get_correlation_matrix(self, tokens: List[str]) -> np.ndarray:
        """Get correlation matrix for tokens"""
        # This would calculate from historical data
        # Returning mock data for now
        n = len(tokens)
        return np.eye(n)
    
    def _get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        # This would query your database
        return 10.0  # Mock value
    
    async def _get_returns_matrix(self, positions: Dict) -> pd.DataFrame:
        """Get returns matrix for portfolio optimization"""
        # This would query your database
        return pd.DataFrame()
