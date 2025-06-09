# citadel_barra_strategy.py
"""
Citadel-inspired multi-factor trading strategy incorporating Barra risk factors
for Solana token trading
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

@dataclass
class BarraFactors:
    """Barra-style risk factors adapted for crypto markets"""
    # Market factors
    market_beta: float  # Sensitivity to overall crypto market
    sol_beta: float     # Sensitivity to Solana ecosystem
    
    # Style factors
    momentum: float     # Price momentum factor
    volatility: float   # Volatility factor
    liquidity: float    # Liquidity provision factor
    size: float        # Market cap factor
    
    # Quality factors
    volume_stability: float  # Trading volume consistency
    holder_quality: float    # Holder distribution quality
    
    # Crypto-specific factors
    defi_correlation: float  # Correlation with DeFi sector
    meme_factor: float       # Meme token characteristics
    
    # Risk metrics
    idiosyncratic_risk: float  # Token-specific risk
    systematic_risk: float     # Market-wide risk exposure


class CitadelBarraStrategy:
    """
    Implements a Citadel-inspired multi-factor strategy with Barra risk management
    """
    
    def __init__(self, db, config, birdeye_api):
        self.db = db
        self.config = config
        self.birdeye_api = birdeye_api
        
        # Risk parameters
        self.max_factor_exposure = 2.0  # Maximum exposure to any single factor
        self.target_idiosyncratic_ratio = 0.6  # Target 60% idiosyncratic risk
        self.factor_limits = {
            'market_beta': (-1.5, 2.5),
            'volatility': (0, 3.0),
            'momentum': (-2.0, 3.0),
            'liquidity': (0.5, 5.0)
        }
        
        # Alpha generation parameters
        self.alpha_decay_halflife = 24  # hours
        self.signal_combination_weights = {
            'momentum': 0.3,
            'mean_reversion': 0.2,
            'volume_breakout': 0.2,
            'ml_prediction': 0.3
        }
        
        # Risk decomposition components
        self.factor_returns_history = []
        self.factor_loadings_cache = {}
        
    async def calculate_barra_factors(self, token_data: Dict) -> BarraFactors:
        """
        Calculate Barra-style risk factors for a token
        """
        try:
            # Get historical data for factor calculation
            contract_address = token_data.get('contract_address')
            
            # Market factors
            market_beta = self._calculate_market_beta(token_data)
            sol_beta = self._calculate_sol_beta(token_data)
            
            # Style factors
            momentum = self._calculate_momentum_factor(token_data)
            volatility = self._calculate_volatility_factor(token_data)
            liquidity = self._calculate_liquidity_factor(token_data)
            size = self._calculate_size_factor(token_data)
            
            # Quality factors
            volume_stability = self._calculate_volume_stability(token_data)
            holder_quality = self._calculate_holder_quality(token_data)
            
            # Crypto-specific factors
            defi_correlation = self._calculate_defi_correlation(token_data)
            meme_factor = self._calculate_meme_factor(token_data)
            
            # Risk decomposition
            systematic_risk, idiosyncratic_risk = self._decompose_risk(
                token_data, market_beta, sol_beta
            )
            
            return BarraFactors(
                market_beta=market_beta,
                sol_beta=sol_beta,
                momentum=momentum,
                volatility=volatility,
                liquidity=liquidity,
                size=size,
                volume_stability=volume_stability,
                holder_quality=holder_quality,
                defi_correlation=defi_correlation,
                meme_factor=meme_factor,
                idiosyncratic_risk=idiosyncratic_risk,
                systematic_risk=systematic_risk
            )
            
        except Exception as e:
            logger.error(f"Error calculating Barra factors: {e}")
            return self._get_default_factors()
    
    def generate_alpha_signals(self, token_data: Dict, factors: BarraFactors) -> Dict[str, float]:
        """
        Generate multiple alpha signals using Citadel-style approach
        """
        signals = {}
        
        # 1. Momentum Signal (trend following)
        signals['momentum'] = self._momentum_alpha(token_data, factors)
        
        # 2. Mean Reversion Signal (statistical arbitrage)
        signals['mean_reversion'] = self._mean_reversion_alpha(token_data, factors)
        
        # 3. Volume Breakout Signal (microstructure)
        signals['volume_breakout'] = self._volume_breakout_alpha(token_data)
        
        # 4. Cross-sectional Signal (relative value)
        signals['cross_sectional'] = self._cross_sectional_alpha(token_data, factors)
        
        # 5. Factor Timing Signal
        signals['factor_timing'] = self._factor_timing_alpha(factors)
        
        return signals
    
    def calculate_position_size(self, 
                              token_data: Dict,
                              factors: BarraFactors,
                              alpha_signals: Dict[str, float],
                              current_portfolio: Dict) -> float:
        """
        Calculate position size using risk-adjusted Kelly Criterion with factor constraints
        """
        # Base position from Kelly Criterion
        expected_return = self._combine_alpha_signals(alpha_signals)
        win_rate = self._estimate_win_rate(alpha_signals, factors)
        
        # Kelly fraction with safety margin
        kelly_fraction = self._modified_kelly_criterion(
            win_rate=win_rate,
            avg_win=token_data.get('avg_win_multiple', 3.62),  # Your historical average
            avg_loss=token_data.get('avg_loss_multiple', 0.95),
            confidence=alpha_signals.get('ml_prediction', 0.5)
        )
        
        # Adjust for risk factors
        risk_adjustment = self._calculate_risk_adjustment(factors)
        
        # Apply factor exposure constraints
        factor_constraint = self._apply_factor_constraints(
            factors, current_portfolio
        )
        
        # Volatility-based position sizing
        volatility_scalar = self._volatility_position_scalar(factors.volatility)
        
        # Final position size calculation
        base_position = self.config.get('max_position_size_pct', 0.04)
        
        position_size = (
            base_position *
            kelly_fraction *
            risk_adjustment *
            factor_constraint *
            volatility_scalar
        )
        
        # Apply limits
        min_size = self.config.get('min_position_size_pct', 0.03)
        max_size = self.config.get('max_position_size_pct', 0.05)
        
        return np.clip(position_size, min_size, max_size)
    
    def _calculate_market_beta(self, token_data: Dict) -> float:
        """Calculate token's beta relative to crypto market"""
        # Simplified calculation - in production, use historical returns
        price_change_24h = token_data.get('price_change_24h', 0)
        
        # Assume market moved 5% as baseline
        market_return = 5.0
        
        if market_return != 0:
            beta = price_change_24h / market_return
        else:
            beta = 1.0
            
        return np.clip(beta, -3, 3)
    
    def _calculate_sol_beta(self, token_data: Dict) -> float:
        """Calculate token's beta relative to Solana ecosystem"""
        # Simplified - in production, correlate with SOL price movements
        return self._calculate_market_beta(token_data) * 1.2  # Assume higher correlation with SOL
    
    def _calculate_momentum_factor(self, token_data: Dict) -> float:
        """Calculate momentum factor score"""
        # Multi-timeframe momentum
        momentum_1h = token_data.get('price_change_1h', 0) / 100
        momentum_6h = token_data.get('price_change_6h', 0) / 100
        momentum_24h = token_data.get('price_change_24h', 0) / 100
        
        # Weighted momentum score
        momentum = (
            0.2 * momentum_1h +
            0.3 * momentum_6h +
            0.5 * momentum_24h
        )
        
        # Normalize to factor score
        return np.tanh(momentum * 2)  # Bounded between -1 and 1
    
    def _calculate_volatility_factor(self, token_data: Dict) -> float:
        """Calculate volatility factor"""
        # Estimate from price changes
        changes = [
            token_data.get('price_change_1h', 0),
            token_data.get('price_change_6h', 0) / 6,
            token_data.get('price_change_24h', 0) / 24
        ]
        
        # Annualized volatility estimate
        hourly_vol = np.std(changes)
        annual_vol = hourly_vol * np.sqrt(24 * 365)
        
        # Normalize (typical crypto vol is 100-200%)
        return annual_vol / 100
    
    def _calculate_liquidity_factor(self, token_data: Dict) -> float:
        """Calculate liquidity factor score"""
        volume = token_data.get('volume_24h', 0)
        liquidity = token_data.get('liquidity_usd', 1)
        mcap = token_data.get('market_cap', 1)
        
        # Volume/Liquidity ratio
        vol_liq_ratio = volume / liquidity if liquidity > 0 else 0
        
        # Turnover ratio
        turnover = volume / mcap if mcap > 0 else 0
        
        # Combined liquidity score
        liquidity_score = np.log1p(vol_liq_ratio) + np.log1p(turnover * 100)
        
        return np.clip(liquidity_score / 5, 0, 5)  # Normalize to 0-5 range
    
    def _calculate_size_factor(self, token_data: Dict) -> float:
        """Calculate size factor score"""
        mcap = token_data.get('market_cap', 0)
        
        # Size buckets
        if mcap < 100000:  # < 100k
            return -2.0  # Micro cap
        elif mcap < 1000000:  # < 1M
            return -1.0  # Small cap
        elif mcap < 10000000:  # < 10M
            return 0.0   # Medium cap
        else:
            return 1.0    # Large cap
    
    def _calculate_volume_stability(self, token_data: Dict) -> float:
        """Calculate volume stability score"""
        # Simplified - in production, use historical volume data
        volume = token_data.get('volume_24h', 0)
        liquidity = token_data.get('liquidity_usd', 1)
        
        # Volume/liquidity ratio as stability proxy
        ratio = volume / liquidity if liquidity > 0 else 0
        
        # More stable if ratio is moderate (not too high or too low)
        if 0.5 <= ratio <= 2.0:
            return 0.8
        elif 0.2 <= ratio <= 5.0:
            return 0.5
        else:
            return 0.2
    
    def _calculate_holder_quality(self, token_data: Dict) -> float:
        """Calculate holder quality score"""
        holders = token_data.get('holders', 0)
        
        if holders >= 1000:
            return 0.9
        elif holders >= 500:
            return 0.7
        elif holders >= 100:
            return 0.5
        else:
            return 0.3
    
    def _calculate_defi_correlation(self, token_data: Dict) -> float:
        """Calculate correlation with DeFi sector"""
        # Simplified - in production, calculate actual correlations
        return 0.5  # Neutral correlation
    
    def _calculate_meme_factor(self, token_data: Dict) -> float:
        """Calculate meme token characteristics"""
        # Check for meme token indicators
        symbol = token_data.get('symbol', '').lower()
        name = token_data.get('name', '').lower()
        
        meme_keywords = ['doge', 'shiba', 'pepe', 'moon', 'rocket', 'cat', 'inu', 'floki', 'bonk', 'wif']
        
        for keyword in meme_keywords:
            if keyword in symbol or keyword in name:
                return 1.0
        
        return 0.0
    
    def _decompose_risk(self, token_data: Dict, market_beta: float, sol_beta: float) -> Tuple[float, float]:
        """Decompose risk into systematic and idiosyncratic components"""
        # Simplified risk decomposition
        # In production, use factor model with historical returns
        
        # Systematic risk increases with beta
        systematic_risk = np.sqrt((market_beta ** 2 + sol_beta ** 2) / 2) * 0.3
        
        # Idiosyncratic risk based on token-specific factors
        volatility = token_data.get('volatility_24h', 1.0)
        idiosyncratic_risk = volatility * 0.7
        
        return systematic_risk, idiosyncratic_risk
    
    def _modified_kelly_criterion(self, win_rate: float, avg_win: float, 
                                avg_loss: float, confidence: float) -> float:
        """
        Modified Kelly Criterion with confidence adjustment
        """
        if avg_loss <= 0:
            return 0
            
        # Basic Kelly formula
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss
        
        kelly = (p * b - q) / b
        
        # Apply confidence scaling and safety factor
        safety_factor = 0.25  # Use 25% of Kelly
        confidence_adj = 0.5 + (confidence * 0.5)  # Scale confidence to 0.5-1.0
        
        return max(0, kelly * safety_factor * confidence_adj)
    
    def _combine_alpha_signals(self, signals: Dict[str, float]) -> float:
        """
        Combine multiple alpha signals with time decay
        """
        combined_alpha = 0
        
        for signal_name, signal_value in signals.items():
            weight = self.signal_combination_weights.get(signal_name, 0.2)
            combined_alpha += weight * signal_value
            
        # Apply bounds
        return np.clip(combined_alpha, -1, 1)
    
    def _momentum_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """
        Generate momentum-based alpha signal
        """
        # Recent momentum
        short_momentum = token_data.get('price_change_1h', 0) / 100
        medium_momentum = token_data.get('price_change_6h', 0) / 600
        
        # Volume confirmation
        volume_ratio = token_data.get('volume_24h', 0) / max(
            token_data.get('avg_volume_7d', 1), 1
        )
        
        # Momentum quality (higher is better)
        momentum_quality = 1 / (1 + factors.volatility)
        
        # Combined signal
        signal = (
            (0.3 * short_momentum + 0.7 * medium_momentum) *
            min(volume_ratio, 2) *
            momentum_quality
        )
        
        return np.tanh(signal)
    
    def _mean_reversion_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """
        Generate mean reversion alpha signal
        """
        # Check for oversold/overbought conditions
        rsi = token_data.get('rsi', 50)
        
        # Mean reversion is stronger for less volatile tokens
        volatility_adj = 1 / (1 + factors.volatility)
        
        # Signal strength based on RSI extremes
        if rsi < 30:
            signal = (30 - rsi) / 30 * volatility_adj
        elif rsi > 70:
            signal = (70 - rsi) / 30 * volatility_adj
        else:
            signal = 0
            
        return np.clip(signal, -1, 1)
    
    def _volume_breakout_alpha(self, token_data: Dict) -> float:
        """
        Generate volume breakout alpha signal
        """
        # Get current and average volume
        current_volume = token_data.get('volume_24h', 0)
        
        # Use a simple average - in production, use rolling average
        avg_volume = token_data.get('avg_volume_7d', current_volume)
        if avg_volume == 0:
            avg_volume = current_volume
        
        # Calculate volume spike
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
        else:
            volume_ratio = 1.0
        
        # Generate signal
        if volume_ratio > 3.0:  # 3x average volume
            return 1.0
        elif volume_ratio > 2.0:  # 2x average volume
            return 0.5
        elif volume_ratio > 1.5:  # 1.5x average volume
            return 0.25
        else:
            return 0.0
    
    def _cross_sectional_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """
        Generate cross-sectional relative value signal
        """
        # Combine multiple factors for ranking
        # In production, compare against universe of tokens
        
        score = 0.0
        
        # Momentum contribution
        if factors.momentum > 0.5:
            score += 0.3
        
        # Liquidity contribution
        if factors.liquidity > 2.0:
            score += 0.2
        
        # Quality contribution
        if factors.volume_stability > 0.7 and factors.holder_quality > 0.7:
            score += 0.3
        
        # Volatility penalty
        if factors.volatility > 2.0:
            score -= 0.2
        
        return np.clip(score, -1, 1)
    
    def _factor_timing_alpha(self, factors: BarraFactors) -> float:
        """
        Generate factor timing signal based on current market regime
        """
        # In production, use regime detection
        # For now, simple rules based on factors
        
        timing_score = 0.0
        
        # High momentum regime
        if factors.momentum > 0.5:
            timing_score += 0.2
        
        # Low volatility regime (good for mean reversion)
        if factors.volatility < 1.0:
            timing_score += 0.1
        
        # High idiosyncratic risk (unique opportunities)
        if factors.idiosyncratic_risk > factors.systematic_risk * 1.5:
            timing_score += 0.2
        
        return np.clip(timing_score, -1, 1)
    
    def _estimate_win_rate(self, alpha_signals: Dict[str, float], factors: BarraFactors) -> float:
        """
        Estimate win rate based on signals and factors
        """
        # Base win rate from historical performance
        base_win_rate = 0.726  # Your historical 72.6%
        
        # Adjust based on signal strength
        signal_strength = self._combine_alpha_signals(alpha_signals)
        
        # Positive signals increase win rate
        if signal_strength > 0.5:
            win_rate_adj = base_win_rate + 0.1
        elif signal_strength > 0:
            win_rate_adj = base_win_rate + 0.05
        elif signal_strength < -0.5:
            win_rate_adj = base_win_rate - 0.1
        else:
            win_rate_adj = base_win_rate
        
        # Factor adjustments
        if factors.volatility > 2.0:
            win_rate_adj -= 0.05  # High volatility reduces win rate
        
        if factors.liquidity < 1.0:
            win_rate_adj -= 0.05  # Low liquidity reduces win rate
        
        return np.clip(win_rate_adj, 0.4, 0.9)
    
    def _calculate_risk_adjustment(self, factors: BarraFactors) -> float:
        """
        Calculate risk adjustment multiplier for position sizing
        """
        adjustment = 1.0
        
        # Volatility adjustment
        if factors.volatility > 2.0:
            adjustment *= 0.7  # Reduce size for high volatility
        elif factors.volatility < 0.5:
            adjustment *= 1.2  # Increase size for low volatility
        
        # Liquidity adjustment
        if factors.liquidity < 1.0:
            adjustment *= 0.8  # Reduce size for low liquidity
        elif factors.liquidity > 3.0:
            adjustment *= 1.1  # Increase size for high liquidity
        
        # Idiosyncratic risk preference
        total_risk = factors.systematic_risk + factors.idiosyncratic_risk
        if total_risk > 0:
            idio_ratio = factors.idiosyncratic_risk / total_risk
            if idio_ratio > 0.7:
                adjustment *= 1.1  # Prefer unique opportunities
        
        return np.clip(adjustment, 0.5, 1.5)
    
    def _volatility_position_scalar(self, volatility: float) -> float:
        """
        Scale position size based on volatility
        """
        # Inverse volatility scaling
        if volatility > 0:
            return np.clip(1.0 / volatility, 0.5, 2.0)
        else:
            return 1.0
    
    def _apply_factor_constraints(self, factors: BarraFactors, 
                                 current_portfolio: Dict) -> float:
        """
        Apply portfolio-level factor exposure constraints
        """
        constraint_multiplier = 1.0
        
        # Check each factor limit
        for factor_name, (min_limit, max_limit) in self.factor_limits.items():
            factor_value = getattr(factors, factor_name, 0)
            
            if factor_value < min_limit:
                constraint_multiplier *= 0.5
            elif factor_value > max_limit:
                constraint_multiplier *= 0.5
                
        # Check idiosyncratic risk ratio
        total_risk = factors.systematic_risk + factors.idiosyncratic_risk
        if total_risk > 0:
            idio_ratio = factors.idiosyncratic_risk / total_risk
            
            # Prefer tokens with higher idiosyncratic risk (unique opportunities)
            if idio_ratio > self.target_idiosyncratic_ratio:
                constraint_multiplier *= 1.2
            else:
                constraint_multiplier *= 0.8
                
        return constraint_multiplier
    
    def calculate_portfolio_risk_decomposition(self, positions: List[Dict]) -> Dict:
        """
        Decompose portfolio risk into systematic and idiosyncratic components
        """
        if not positions:
            return {
                'total_risk': 0,
                'systematic_risk': 0,
                'idiosyncratic_risk': 0,
                'factor_contributions': {}
            }
            
        # Calculate portfolio-weighted factor exposures
        total_value = sum(p['value'] for p in positions)
        
        weighted_factors = {}
        for factor in ['market_beta', 'sol_beta', 'momentum', 'volatility']:
            weighted_factors[factor] = sum(
                p['factors'].get(factor, 0) * p['value'] / total_value
                for p in positions
            )
            
        # Estimate risk contributions
        systematic_var = sum(
            weighted_factors[f] ** 2 * self._get_factor_volatility(f)
            for f in weighted_factors
        )
        
        # Portfolio variance
        portfolio_var = sum(
            (p['value'] / total_value) ** 2 * p['variance']
            for p in positions
        )
        
        idiosyncratic_var = max(0, portfolio_var - systematic_var)
        
        return {
            'total_risk': np.sqrt(portfolio_var),
            'systematic_risk': np.sqrt(systematic_var),
            'idiosyncratic_risk': np.sqrt(idiosyncratic_var),
            'factor_contributions': weighted_factors
        }
    
    def _get_factor_volatility(self, factor_name: str) -> float:
        """Get historical volatility of a factor"""
        # Simplified - in production, calculate from historical data
        factor_vols = {
            'market_beta': 0.15,
            'sol_beta': 0.20,
            'momentum': 0.25,
            'volatility': 0.10
        }
        return factor_vols.get(factor_name, 0.15)
    
    def _get_default_factors(self) -> BarraFactors:
        """Return default neutral factors"""
        return BarraFactors(
            market_beta=1.0,
            sol_beta=1.0,
            momentum=0.0,
            volatility=1.0,
            liquidity=1.0,
            size=0.0,
            volume_stability=0.5,
            holder_quality=0.5,
            defi_correlation=0.5,
            meme_factor=0.0,
            idiosyncratic_risk=0.5,
            systematic_risk=0.5
        )