# enhanced_trading_config.py

import json
from typing import Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class TradingParameters:
    """Enhanced trading parameters with best practices"""
    
    # Position Sizing
    max_position_size_pct: float = 0.02  # 2% per position
    min_position_size_sol: float = 0.01
    max_position_size_sol: float = 0.5
    max_open_positions: int = 10
    
    # Risk Management
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.15  # 15% take profit
    trailing_stop_enabled: bool = True
    trailing_stop_activation_pct: float = 0.10  # Activate at 10% profit
    trailing_stop_distance_pct: float = 0.05  # Trail by 5%
    max_daily_loss_pct: float = 0.10  # 10% daily loss limit
    max_drawdown_pct: float = 0.20  # 20% max drawdown
    
    # Entry Criteria
    min_safety_score: float = 60.0
    min_volume_24h: float = 50000.0
    min_liquidity: float = 25000.0
    min_holders: int = 100
    min_price_change_1h: float = -10.0  # Max 10% drop in 1h
    max_price_change_24h: float = 100.0  # Max 100% gain in 24h
    
    # ML Parameters
    ml_confidence_threshold: float = 0.70  # 70% confidence for ML signals
    use_ml_predictions: bool = True
    ml_weight_in_decision: float = 0.40  # 40% weight to ML signal
    
    # Technical Indicators
    use_technical_analysis: bool = True
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    volume_spike_threshold: float = 2.0  # 2x average volume
    
    # Market Conditions
    avoid_low_volume_hours: bool = True
    low_volume_hours: list = [0, 1, 2, 3, 4, 5]  # UTC hours
    
    # Token Filtering
    blacklist_keywords: list = None
    min_market_cap: float = 100000.0
    max_market_cap: float = 100000000.0  # 100M cap
    
    # Execution
    slippage_tolerance: float = 0.02  # 2% slippage
    gas_limit_multiplier: float = 1.5
    retry_attempts: int = 3
    
    # Timing
    min_hold_time_minutes: int = 5
    max_hold_time_hours: int = 24
    rebalance_interval_minutes: int = 60
    
    def __post_init__(self):
        if self.blacklist_keywords is None:
            self.blacklist_keywords = [
                'test', 'fake', 'scam', 'rug', 'honey'
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @classmethod
    def load_from_file(cls, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)


class RiskManager:
    """Risk management system with position sizing and portfolio protection"""
    
    def __init__(self, params: TradingParameters, initial_balance: float):
        self.params = params
        self.initial_balance = initial_balance
        self.daily_loss = 0.0
        self.peak_balance = initial_balance
        self.positions = {}
        self.daily_reset_time = None
        
    def calculate_position_size(self, 
                              current_balance: float,
                              token_volatility: float,
                              confidence_score: float) -> float:
        """
        Calculate position size using Kelly Criterion and risk parity
        """
        # Base position size (percentage of portfolio)
        base_size = self.params.max_position_size_pct
        
        # Adjust for confidence
        confidence_adj = confidence_score / 100.0
        
        # Adjust for volatility (inverse relationship)
        volatility_adj = min(1.0, 20.0 / max(token_volatility, 10.0))
        
        # Adjust for current drawdown
        drawdown = (self.peak_balance - current_balance) / self.peak_balance
        drawdown_adj = max(0.3, 1.0 - (drawdown * 2))
        
        # Calculate final position size
        position_pct = base_size * confidence_adj * volatility_adj * drawdown_adj
        position_size = current_balance * position_pct
        
        # Apply limits
        position_size = max(self.params.min_position_size_sol, position_size)
        position_size = min(self.params.max_position_size_sol, position_size)
        
        return round(position_size, 4)
    
    def check_risk_limits(self, current_balance: float) -> Dict[str, bool]:
        """Check if any risk limits are breached"""
        # Update peak balance
        self.peak_balance = max(self.peak_balance, current_balance)
        
        # Calculate metrics
        daily_loss_pct = self.daily_loss / self.initial_balance
        drawdown_pct = (self.peak_balance - current_balance) / self.peak_balance
        
        return {
            'can_trade': (
                daily_loss_pct < self.params.max_daily_loss_pct and
                drawdown_pct < self.params.max_drawdown_pct and
                len(self.positions) < self.params.max_open_positions
            ),
            'daily_loss_exceeded': daily_loss_pct >= self.params.max_daily_loss_pct,
            'max_drawdown_exceeded': drawdown_pct >= self.params.max_drawdown_pct,
            'max_positions_reached': len(self.positions) >= self.params.max_open_positions
        }
    
    def calculate_stop_loss(self, entry_price: float, 
                          token_volatility: float) -> float:
        """Dynamic stop loss based on volatility"""
        # Base stop loss
        base_stop = self.params.stop_loss_pct
        
        # Adjust for volatility
        volatility_factor = min(2.0, token_volatility / 20.0)
        adjusted_stop = base_stop * (1 + volatility_factor * 0.5)
        
        # Cap at maximum
        adjusted_stop = min(adjusted_stop, 0.15)  # Max 15% stop
        
        return entry_price * (1 - adjusted_stop)
    
    def update_trailing_stop(self, position_id: str, 
                           current_price: float) -> Optional[float]:
        """Update trailing stop for a position"""
        if position_id not in self.positions:
            return None
            
        position = self.positions[position_id]
        entry_price = position['entry_price']
        current_stop = position.get('stop_loss', 0)
        
        # Check if trailing stop should be activated
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct >= self.params.trailing_stop_activation_pct:
            # Calculate new trailing stop
            trailing_stop = current_price * (1 - self.params.trailing_stop_distance_pct)
            
            # Only update if higher than current stop
            if trailing_stop > current_stop:
                position['stop_loss'] = trailing_stop
                position['trailing_stop_active'] = True
                return trailing_stop
                
        return current_stop


class TechnicalAnalyzer:
    """Technical analysis indicators for entry/exit signals"""
    
    @staticmethod
    def calculate_rsi(prices: list, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0  # Neutral
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def detect_volume_spike(current_volume: float, 
                          avg_volume: float,
                          threshold: float = 2.0) -> bool:
        """Detect unusual volume spikes"""
        if avg_volume == 0:
            return False
        return current_volume > (avg_volume * threshold)
    
    @staticmethod
    def calculate_momentum(prices: list, period: int = 10) -> float:
        """Calculate price momentum"""
        if len(prices) < period:
            return 0.0
            
        return (prices[-1] - prices[-period]) / prices[-period] * 100


# Example usage
if __name__ == "__main__":
    # Create enhanced parameters
    params = TradingParameters()
    
    # Save to file
    params.save_to_file("config/trading_params.json")
    
    # Initialize risk manager
    risk_mgr = RiskManager(params, initial_balance=10.0)
    
    # Example position sizing
    position_size = risk_mgr.calculate_position_size(
        current_balance=10.0,
        token_volatility=30.0,  # 30% daily volatility
        confidence_score=85.0   # 85% confidence
    )
    
    print(f"Recommended position size: {position_size} SOL")
