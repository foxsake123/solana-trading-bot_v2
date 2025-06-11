# core/strategies/partial_exits.py
"""
Partial Exit Strategy Manager
Implements 20%, 50%, 100%, 200% exit levels
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExitLevel:
    """Exit level configuration"""
    profit_pct: float  # Profit percentage (0.2 = 20%)
    exit_pct: float    # Percentage of position to exit
    description: str

class PartialExitManager:
    """Manages partial exits at multiple profit levels"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Define exit levels
        self.exit_levels = [
            ExitLevel(0.2, 0.25, "20% profit - Exit 25%"),
            ExitLevel(0.5, 0.25, "50% profit - Exit 25%"),
            ExitLevel(1.0, 0.25, "100% profit - Exit 25%"),
            ExitLevel(2.0, 0.25, "200% profit - Keep 25% moonbag"),
        ]
        
        # Track executed exits per position
        self.executed_exits: Dict[str, List[float]] = {}
        
        # Trailing stop configuration
        self.trailing_stop_config = {
            'enabled': True,
            'activation': 3.0,  # Activate at 300% profit
            'distance': 0.2     # 20% trailing distance
        }
        
        # Track highest prices for trailing stops
        self.highest_prices: Dict[str, float] = {}
        
    async def check_exits(self, position: Dict, current_price: float) -> Optional[Tuple[float, str]]:
        """
        Check if any partial exit should be executed
        
        Returns:
            Tuple of (exit_amount, reason) if exit should happen, None otherwise
        """
        token_address = position['contract_address']
        entry_price = position['entry_price']
        current_amount = position['amount']
        
        # Calculate profit percentage
        profit_pct = (current_price - entry_price) / entry_price
        
        # Initialize tracking if needed
        if token_address not in self.executed_exits:
            self.executed_exits[token_address] = []
        
        # Check each exit level
        for level in self.exit_levels:
            if profit_pct >= level.profit_pct and level.profit_pct not in self.executed_exits[token_address]:
                # Calculate exit amount
                exit_amount = current_amount * level.exit_pct
                
                # Mark level as executed
                self.executed_exits[token_address].append(level.profit_pct)
                
                logger.info(f"✅ Partial exit triggered: {level.description}")
                logger.info(f"   Token: {token_address[:8]}...")
                logger.info(f"   Profit: {profit_pct*100:.1f}%")
                logger.info(f"   Exit amount: {exit_amount:.4f} ({level.exit_pct*100:.0f}% of position)")
                
                return (exit_amount, level.description)
        
        # Check trailing stop for moonbag
        if profit_pct >= self.trailing_stop_config['activation']:
            return self._check_trailing_stop(position, current_price, profit_pct)
        
        return None
    
    def _check_trailing_stop(self, position: Dict, current_price: float, profit_pct: float) -> Optional[Tuple[float, str]]:
        """Check trailing stop for high profit positions"""
        token_address = position['contract_address']
        
        # Update highest price
        if token_address not in self.highest_prices:
            self.highest_prices[token_address] = current_price
        else:
            self.highest_prices[token_address] = max(self.highest_prices[token_address], current_price)
        
        # Calculate drawdown from highest
        highest_price = self.highest_prices[token_address]
        drawdown = (highest_price - current_price) / highest_price
        
        # Check if trailing stop hit
        if drawdown >= self.trailing_stop_config['distance']:
            # Exit entire remaining position
            exit_amount = position['amount']
            reason = f"Trailing stop hit at {profit_pct*100:.1f}% profit (drawdown: {drawdown*100:.1f}%)"
            
            logger.info(f"🛑 Trailing stop triggered!")
            logger.info(f"   Token: {token_address[:8]}...")
            logger.info(f"   Highest profit: {((highest_price - position['entry_price']) / position['entry_price'] * 100):.1f}%")
            logger.info(f"   Current profit: {profit_pct*100:.1f}%")
            logger.info(f"   Drawdown: {drawdown*100:.1f}%")
            
            return (exit_amount, reason)
        
        return None
    
    def get_exit_summary(self, token_address: str) -> Dict:
        """Get summary of exits for a position"""
        executed = self.executed_exits.get(token_address, [])
        
        return {
            'executed_levels': executed,
            'remaining_levels': [level.profit_pct for level in self.exit_levels if level.profit_pct not in executed],
            'total_exits': len(executed),
            'moonbag_active': 2.0 in executed  # 200% level executed
        }
    
    def reset_position(self, token_address: str):
        """Reset tracking for a closed position"""
        if token_address in self.executed_exits:
            del self.executed_exits[token_address]
        if token_address in self.highest_prices:
            del self.highest_prices[token_address]
    
    def get_stats(self) -> Dict:
        """Get overall partial exit statistics"""
        total_positions = len(self.executed_exits)
        
        # Count positions at each level
        level_counts = {level.profit_pct: 0 for level in self.exit_levels}
        for exits in self.executed_exits.values():
            for level in exits:
                if level in level_counts:
                    level_counts[level] += 1
        
        return {
            'total_positions_tracked': total_positions,
            'positions_at_20%': level_counts.get(0.2, 0),
            'positions_at_50%': level_counts.get(0.5, 0),
            'positions_at_100%': level_counts.get(1.0, 0),
            'positions_at_200%': level_counts.get(2.0, 0),
            'active_moonbags': sum(1 for exits in self.executed_exits.values() if 2.0 in exits)
        }