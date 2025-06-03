#!/usr/bin/env python3
"""
Position Size Calculator - Single source of truth
Reads from trading_params.json and calculates position sizes
"""
import json
import logging

logger = logging.getLogger(__name__)

class PositionCalculator:
    """Calculate position sizes based on percentage of balance"""
    
    def __init__(self, config_path="config/trading_params.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from trading_params.json"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Default values if config fails
            return {
                "min_position_size_pct": 3.0,
                "default_position_size_pct": 4.0,
                "max_position_size_pct": 5.0,
                "absolute_min_sol": 0.1,
                "absolute_max_sol": 2.0,
            }
    
    def calculate_position_size(self, balance: float, 
                               confidence: float = None,
                               volatility: float = None) -> float:
        """
        Calculate position size based on balance and optional factors
        
        Args:
            balance: Current SOL balance
            confidence: ML confidence score (0-1)
            volatility: Token volatility metric
            
        Returns:
            Position size in SOL
        """
        # Reload config to get latest values
        self.config = self._load_config()
        
        # Start with default percentage
        position_pct = self.config["default_position_size_pct"]
        
        # Adjust based on confidence if provided
        if confidence is not None:
            # Higher confidence = larger position (within bounds)
            min_pct = self.config["min_position_size_pct"]
            max_pct = self.config["max_position_size_pct"]
            position_pct = min_pct + (max_pct - min_pct) * confidence
        
        # Calculate position size
        position_size = balance * (position_pct / 100.0)
        
        # Apply absolute limits
        position_size = max(self.config["absolute_min_sol"], position_size)
        position_size = min(self.config["absolute_max_sol"], position_size)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"({position_pct:.1f}% of {balance:.4f} SOL balance)")
        
        return round(position_size, 4)
    
    def get_max_positions(self) -> int:
        """Get maximum number of open positions allowed"""
        return self.config.get("max_open_positions", 10)
    
    def check_portfolio_risk(self, open_positions: int, balance: float) -> bool:
        """Check if we can open another position based on portfolio risk"""
        max_risk_pct = self.config.get("max_portfolio_risk_pct", 30.0)
        position_size = self.calculate_position_size(balance)
        
        # Calculate total risk if we open another position
        total_risk = (open_positions + 1) * position_size
        risk_pct = (total_risk / balance) * 100
        
        return risk_pct <= max_risk_pct

# Global instance
position_calculator = PositionCalculator()

# Convenience function
def calculate_position_size(balance: float, **kwargs) -> float:
    """Calculate position size using global calculator"""
    return position_calculator.calculate_position_size(balance, **kwargs)
