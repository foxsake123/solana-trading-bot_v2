#!/usr/bin/env python3
"""
Position size override - ensures minimum position sizes
"""
import logging

logger = logging.getLogger(__name__)

class PositionSizer:
    """Force larger position sizes"""
    
    MIN_POSITION = 0.3  # Minimum 0.3 SOL
    MAX_POSITION = 0.5  # Maximum 0.5 SOL
    DEFAULT_POSITION = 0.4  # Default 0.4 SOL
    
    @classmethod
    def calculate_position_size(cls, balance: float, config: dict = None) -> float:
        """Calculate position size with enforced minimums"""
        
        # Get configured max from config
        if config:
            max_investment = config.get('max_investment_per_token', cls.MAX_POSITION)
        else:
            max_investment = cls.MAX_POSITION
        
        # Calculate 4% of balance
        percentage_size = balance * 0.04
        
        # Use the larger of percentage or minimum
        position_size = max(cls.MIN_POSITION, percentage_size)
        
        # Cap at maximum
        position_size = min(position_size, max_investment, cls.MAX_POSITION)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"(balance: {balance:.4f}, min: {cls.MIN_POSITION}, max: {max_investment})")
        
        return position_size
    
    @classmethod
    def enforce_minimum(cls, amount: float) -> float:
        """Enforce minimum position size"""
        if amount < cls.MIN_POSITION:
            logger.warning(f"Position size {amount:.4f} below minimum, increasing to {cls.MIN_POSITION}")
            return cls.MIN_POSITION
        return amount

# Monkey patch for any imports
def patch_position_calculations():
    """Patch position calculations in the bot"""
    try:
        import sys
        
        # Try to patch various modules
        modules_to_patch = [
            'trading_bot',
            'core.trading.trading_bot',
            'core.trading.position_manager'
        ]
        
        for module_name in modules_to_patch:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                
                # Patch any calculate_position methods
                if hasattr(module, 'calculate_position_size'):
                    module.calculate_position_size = PositionSizer.calculate_position_size
                    logger.info(f"Patched {module_name}.calculate_position_size")
                
                # Patch TradingBot class if it exists
                if hasattr(module, 'TradingBot'):
                    trading_bot_class = getattr(module, 'TradingBot')
                    
                    # Wrap the buy method
                    if hasattr(trading_bot_class, 'buy_token'):
                        original_buy = trading_bot_class.buy_token
                        
                        async def patched_buy(self, address, amount):
                            amount = PositionSizer.enforce_minimum(amount)
                            return await original_buy(self, address, amount)
                        
                        trading_bot_class.buy_token = patched_buy
                        logger.info(f"Patched {module_name}.TradingBot.buy_token")
    
    except Exception as e:
        logger.error(f"Error patching position calculations: {e}")

# Auto-patch on import
patch_position_calculations()
