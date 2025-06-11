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
    
    def __init__(self, config: Dict, db):
        self.config = config
        self.db = db
        
        # Factor weights and limits
        self.factor_weights = config.get('signal_weights', {
            'momentum': 0.3,
            'mean_reversion': 0.2,
            'volume_breakout': 0.2,
            'ml_prediction': 0.3
        })
        
        self.factor_limits = config.get('factor_limits', {
            'market_beta': [-1.5, 2.5],
            'volatility': [0, 3.0],
            'momentum': [-2.0, 3.0],
            'liquidity': [0.5, 5.0]
        })
        
        # Risk parameters
        self.max_factor_exposure = config.get('max_factor_exposure', 2.0)
        self.target_idiosyncratic_ratio = config.get('target_idiosyncratic_ratio', 0.6)
        self.kelly_safety_factor = config.get('kelly_safety_factor', 0.25)
        
        # Alpha decay parameters
        self.alpha_decay_halflife = config.get('alpha_decay_halflife_hours', 24) * 3600
        self.alpha_threshold = config.get('alpha_exhaustion_threshold', -0.2)
        
        # Market data cache
        self.market_data_cache = {}
        self.factor_history = []
        
        logger.info("Citadel-Barra Strategy initialized with multi-factor model")
    
    def calculate_barra_factors(self, token_data: Dict) -> BarraFactors:
        """Calculate Barra-style risk factors for a token"""
        
        # Market betas
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
        
        # Crypto-specific
        defi_correlation = self._calculate_defi_correlation(token_data)
        meme_factor = self._calculate_meme_factor(token_data)
        
        # Risk decomposition
        systematic_risk = abs(market_beta) * 0.6 + abs(sol_beta) * 0.4
        idiosyncratic_risk = 1.0 - min(systematic_risk, 0.8)
        
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
    
    def generate_alpha_signals(self, token_data: Dict, factors: BarraFactors) -> Dict[str, float]:
        """Generate multiple alpha signals using different strategies"""
        
        signals = {}
        
        # 1. Momentum alpha (trend following)
        signals['momentum'] = self._momentum_alpha(token_data, factors)
        
        # 2. Mean reversion alpha
        signals['mean_reversion'] = self._mean_reversion_alpha(token_data, factors)
        
        # 3. Volume breakout alpha
        signals['volume_breakout'] = self._volume_breakout_alpha(token_data, factors)
        
        # 4. ML prediction alpha (using existing ML model)
        signals['ml_prediction'] = self._ml_prediction_alpha(token_data)
        
        return signals
    
    def calculate_position_size(self, token_data: Dict, factors: BarraFactors, 
                              alpha_signals: Dict[str, float], portfolio_value: float) -> float:
        """
        Calculate optimal position size using Kelly criterion with risk constraints
        """
        
        # Combine alpha signals
        combined_alpha = sum(
            signal * self.factor_weights.get(name, 0)
            for name, signal in alpha_signals.items()
        )
        
        # Base position size (percentage of portfolio)
        base_size = self.config.get('default_position_size_pct', 5.0) / 100
        
        # Kelly criterion adjustment
        win_rate = 0.72  # Historical win rate
        avg_win = 3.62   # Average win multiplier
        avg_loss = 0.25  # Average loss
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_adjusted = kelly_fraction * self.kelly_safety_factor
        
        # Risk adjustments
        risk_adjustment = self._calculate_risk_adjustment(factors)
        
        # Factor constraint adjustment
        factor_constraint = self._calculate_factor_constraint(factors)
        
        # Volatility adjustment
        vol_scalar = 1.0 / (1.0 + factors.volatility)
        
        # Calculate final position size
        position_size_pct = (
            base_size * 
            kelly_adjusted * 
            risk_adjustment * 
            factor_constraint * 
            vol_scalar *
            min(combined_alpha * 2, 2.0)  # Alpha multiplier capped at 2x
        )
        
        # Apply limits
        min_size = self.config.get('min_position_size_pct', 1.0) / 100
        max_size = self.config.get('max_position_size_pct', 10.0) / 100
        
        position_size_pct = max(min_size, min(max_size, position_size_pct))
        
        # Convert to SOL amount
        position_size_sol = portfolio_value * position_size_pct
        
        # Apply absolute limits
        abs_min = self.config.get('absolute_min_sol', 0.1)
        abs_max = self.config.get('absolute_max_sol', 5.0)
        
        return max(abs_min, min(abs_max, position_size_sol))
    
    def should_exit_position(self, position: Dict, current_data: Dict, 
                           entry_factors: BarraFactors) -> Tuple[bool, str]:
        """
        Determine if position should be exited based on multiple criteria
        """
        
        # Calculate current factors
        current_factors = self.calculate_barra_factors(current_data)
        
        # 1. Traditional stop loss / take profit
        pnl_pct = (current_data['price'] - position['entry_price']) / position['entry_price']
        
        if pnl_pct <= -self.config.get('stop_loss_pct', 0.05):
            return True, f"Stop loss hit: {pnl_pct:.1%}"
        
        # Adjust take profit by remaining alpha
        alpha_decay = self._calculate_alpha_decay(position['entry_time'])
        adjusted_tp = self.config.get('take_profit_pct', 0.5) * (1 + alpha_decay)
        
        if pnl_pct >= adjusted_tp:
            return True, f"Take profit hit: {pnl_pct:.1%}"
        
        # 2. Alpha exhaustion
        current_alpha = self.generate_alpha_signals(current_data, current_factors)
        combined_alpha = sum(
            signal * self.factor_weights.get(name, 0)
            for name, signal in current_alpha.items()
        )
        
        if combined_alpha < self.alpha_threshold:
            return True, f"Alpha exhausted: {combined_alpha:.3f}"
        
        # 3. Risk-based exits
        if current_factors.volatility > entry_factors.volatility * 2:
            return True, "Volatility spike: 2x entry volatility"
        
        if current_factors.systematic_risk > 0.8:
            return True, f"High systematic risk: {current_factors.systematic_risk:.2f}"
        
        # 4. Better opportunity exists
        if self._has_better_opportunity(position, combined_alpha):
            return True, "Better opportunity available"
        
        return False, ""
    
    # === Factor Calculation Methods ===
    
    def _calculate_market_beta(self, token_data: Dict) -> float:
        """Calculate beta relative to overall crypto market"""
        # Simplified: use correlation with price changes
        if 'price_change_24h' in token_data:
            # Assume market moved 2% on average
            market_return = 0.02
            token_return = token_data['price_change_24h'] / 100
            beta = token_return / market_return if market_return != 0 else 1.0
            return np.clip(beta, -2.0, 3.0)
        return 1.0
    
    def _calculate_sol_beta(self, token_data: Dict) -> float:
        """Calculate beta relative to Solana ecosystem"""
        # This would ideally use correlation with SOL price
        # For now, use a simplified approach
        return self._calculate_market_beta(token_data) * 0.8
    
    def _calculate_momentum_factor(self, token_data: Dict) -> float:
        """Calculate momentum using multiple timeframes"""
        momentum_score = 0.0
        weights = {'1h': 0.2, '6h': 0.3, '24h': 0.5}
        
        for timeframe, weight in weights.items():
            key = f'price_change_{timeframe}'
            if key in token_data:
                change = token_data[key] / 100
                momentum_score += change * weight
        
        return np.tanh(momentum_score * 2)  # Normalize to [-1, 1]
    
    def _calculate_volatility_factor(self, token_data: Dict) -> float:
        """Calculate volatility factor"""
        # Estimate from price changes
        changes = []
        for tf in ['1h', '6h', '24h']:
            key = f'price_change_{tf}'
            if key in token_data:
                changes.append(abs(token_data[key]))
        
        if changes:
            # Annualized volatility estimate
            avg_change = np.mean(changes)
            volatility = avg_change * np.sqrt(365)
            return volatility / 100
        return 1.0
    
    def _calculate_liquidity_factor(self, token_data: Dict) -> float:
        """Calculate liquidity factor"""
        volume = token_data.get('volume_24h', 0)
        liquidity = token_data.get('liquidity_usd', 1)
        mcap = token_data.get('mcap', 1)
        
        # Volume to liquidity ratio
        vol_liq_ratio = volume / liquidity if liquidity > 0 else 0
        
        # Turnover ratio
        turnover = volume / mcap if mcap > 0 else 0
        
        # Combined liquidity score
        liquidity_score = (vol_liq_ratio * 0.6 + turnover * 0.4)
        
        return np.clip(liquidity_score, 0, 5.0)
    
    def _calculate_size_factor(self, token_data: Dict) -> float:
        """Calculate size factor (market cap based)"""
        mcap = token_data.get('mcap', 0)
        
        if mcap < 100_000:
            return -1.0  # Micro cap
        elif mcap < 1_000_000:
            return -0.5  # Small cap
        elif mcap < 10_000_000:
            return 0.0   # Mid cap
        else:
            return 0.5   # Large cap
    
    def _calculate_volume_stability(self, token_data: Dict) -> float:
        """Calculate volume stability score"""
        # This would ideally use historical volume data
        # For now, use a heuristic based on volume/mcap ratio
        volume = token_data.get('volume_24h', 0)
        mcap = token_data.get('mcap', 1)
        
        vol_mcap_ratio = volume / mcap if mcap > 0 else 0
        
        # Stable if ratio is between 0.1 and 2.0
        if 0.1 <= vol_mcap_ratio <= 2.0:
            return 1.0
        elif vol_mcap_ratio < 0.1:
            return vol_mcap_ratio / 0.1
        else:
            return 2.0 / vol_mcap_ratio
    
    def _calculate_holder_quality(self, token_data: Dict) -> float:
        """Calculate holder distribution quality"""
        holders = token_data.get('holders', 0)
        
        if holders < 50:
            return 0.0
        elif holders < 500:
            return 0.5
        else:
            return min(1.0, holders / 1000)
    
    def _calculate_defi_correlation(self, token_data: Dict) -> float:
        """Calculate correlation with DeFi sector"""
        # Simplified: check if it's a DeFi-related token
        # In practice, this would use actual correlation data
        return 0.5  # Neutral for now
    
    def _calculate_meme_factor(self, token_data: Dict) -> float:
        """Calculate meme token characteristics"""
        # High volatility + high volume + many holders = meme characteristics
        volatility = self._calculate_volatility_factor(token_data)
        liquidity = self._calculate_liquidity_factor(token_data)
        holders = token_data.get('holders', 0)
        
        meme_score = 0.0
        
        if volatility > 2.0:
            meme_score += 0.3
        if liquidity > 2.0:
            meme_score += 0.3
        if holders > 1000:
            meme_score += 0.4
            
        return meme_score
    
    # === Alpha Generation Methods ===
    
    def _momentum_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """Generate momentum-based alpha signal"""
        base_momentum = factors.momentum
        
        # Quality adjustment
        quality_adj = factors.volume_stability * factors.holder_quality
        
        # Trend strength
        trend_strength = 0.0
        if all(key in token_data for key in ['price_change_1h', 'price_change_6h', 'price_change_24h']):
            changes = [token_data['price_change_1h'], token_data['price_change_6h'], token_data['price_change_24h']]
            if all(c > 0 for c in changes):  # All positive
                trend_strength = 1.0
            elif all(c < 0 for c in changes):  # All negative
                trend_strength = -1.0
        
        return base_momentum * quality_adj * (1 + trend_strength * 0.5)
    
    def _mean_reversion_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """Generate mean reversion alpha signal"""
        # RSI-based mean reversion
        rsi = token_data.get('rsi', 50)
        
        if rsi < 30:
            signal = (30 - rsi) / 30  # Oversold
        elif rsi > 70:
            signal = (70 - rsi) / 30  # Overbought
        else:
            signal = 0.0
        
        # Adjust by volatility (mean reversion works better in low volatility)
        vol_adj = 1.0 / (1.0 + factors.volatility)
        
        return signal * vol_adj
    
    def _volume_breakout_alpha(self, token_data: Dict, factors: BarraFactors) -> float:
        """Generate volume breakout alpha signal"""
        # Look for unusual volume
        volume = token_data.get('volume_24h', 0)
        avg_volume = token_data.get('avg_volume_7d', volume)  # Fallback to current if no average
        
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio > 2.0:  # 2x normal volume
                return min(1.0, (volume_ratio - 2.0) / 3.0)
        
        return 0.0
    
    def _ml_prediction_alpha(self, token_data: Dict) -> float:
        """Get alpha signal from ML model"""
        # This would interface with your existing ML predictor
        # For now, return neutral signal
        return 0.0
    
    # === Risk Management Methods ===
    
    def _calculate_risk_adjustment(self, factors: BarraFactors) -> float:
        """Calculate risk-based position adjustment"""
        # Prefer idiosyncratic risk over systematic risk
        idio_ratio = factors.idiosyncratic_risk / (factors.idiosyncratic_risk + factors.systematic_risk)
        
        if idio_ratio >= self.target_idiosyncratic_ratio:
            return 1.0
        else:
            return idio_ratio / self.target_idiosyncratic_ratio
    
    def _calculate_factor_constraint(self, factors: BarraFactors) -> float:
        """Apply factor exposure constraints"""
        constraint = 1.0
        
        # Check each factor against limits
        factor_dict = {
            'market_beta': factors.market_beta,
            'volatility': factors.volatility,
            'momentum': factors.momentum,
            'liquidity': factors.liquidity
        }
        
        for factor_name, value in factor_dict.items():
            if factor_name in self.factor_limits:
                min_val, max_val = self.factor_limits[factor_name]
                if value < min_val or value > max_val:
                    # Reduce position size for out-of-bounds factors
                    constraint *= 0.5
        
        return constraint
    
    def _calculate_alpha_decay(self, entry_time: datetime) -> float:
        """Calculate alpha decay since entry"""
        time_elapsed = (datetime.now(timezone.utc) - entry_time).total_seconds()
        decay = np.exp(-time_elapsed / self.alpha_decay_halflife)
        return decay
    
    def _has_better_opportunity(self, position: Dict, current_alpha: float) -> bool:
        """Check if better opportunities exist in the market"""
        # This would scan other tokens and compare alpha
        # For now, use a simple threshold
        return current_alpha < 0.1 and position.get('unrealized_pnl', 0) > 0
    
    async def analyze_token(self, token_data: Dict) -> Dict:
        """Main analysis method for the enhanced bot"""
        
        # Calculate factors
        factors = self.calculate_barra_factors(token_data)
        
        # Generate alpha signals
        alpha_signals = self.generate_alpha_signals(token_data, factors)
        
        # Combine signals
        combined_alpha = sum(
            signal * self.factor_weights.get(name, 0)
            for name, signal in alpha_signals.items()
        )
        
        # Make recommendation
        recommendation = combined_alpha > 0.3  # Threshold for entry
        
        return {
            'recommendation': recommendation,
            'factors': factors,
            'alpha_signals': alpha_signals,
            'combined_alpha': combined_alpha,
            'final_score': combined_alpha,
            'reasons': self._generate_reasons(factors, alpha_signals)
        }
    
    def _generate_reasons(self, factors: BarraFactors, signals: Dict[str, float]) -> List[str]:
        """Generate human-readable reasons for the decision"""
        reasons = []
        
        # Factor-based reasons
        if factors.momentum > 0.5:
            reasons.append(f"Strong momentum ({factors.momentum:.2f})")
        if factors.volume_stability > 0.8:
            reasons.append("Stable volume pattern")
        if factors.idiosyncratic_risk > 0.6:
            reasons.append("High idiosyncratic opportunity")
        
        # Signal-based reasons
        for signal_name, value in signals.items():
            if value > 0.5:
                reasons.append(f"{signal_name.replace('_', ' ').title()} signal: {value:.2f}")
        
        return reasons
