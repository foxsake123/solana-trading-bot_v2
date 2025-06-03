#!/usr/bin/env python3
"""
Fix to ensure trading bot uses percentage-based position sizing
Add this to your trading_bot.py or replace the calculate_position_size method
"""

import json
import logging

logger = logging.getLogger(__name__)

class PositionSizingFix:
    """
    This class shows the corrected position sizing logic
    that should be used in your trading_bot.py
    """
    
    @staticmethod
    def load_trading_params():
        """Load trading parameters from config file"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trading params: {e}")
            # Default fallback values
            return {
                'min_position_size_pct': 3.0,
                'default_position_size_pct': 4.0,
                'max_position_size_pct': 5.0,
                'absolute_min_sol': 0.1,
                'absolute_max_sol': 2.0
            }
    
    @staticmethod
    def calculate_position_size(balance: float, ml_confidence: float = None) -> float:
        """
        Calculate position size as percentage of balance
        
        This method should REPLACE any existing position size calculation
        in your trading_bot.py
        """
        # Load latest config
        params = PositionSizingFix.load_trading_params()
        
        # Get percentage settings
        min_pct = params.get('min_position_size_pct', 3.0)
        default_pct = params.get('default_position_size_pct', 4.0)
        max_pct = params.get('max_position_size_pct', 5.0)
        
        # Start with default percentage
        position_pct = default_pct
        
        # Adjust based on ML confidence if provided
        if ml_confidence is not None and ml_confidence > 0:
            # Scale between min and max based on confidence
            # confidence of 0.65 = min, confidence of 0.85 = max
            if ml_confidence >= 0.85:
                position_pct = max_pct
            elif ml_confidence <= 0.65:
                position_pct = min_pct
            else:
                # Linear interpolation
                confidence_range = 0.85 - 0.65
                confidence_normalized = (ml_confidence - 0.65) / confidence_range
                position_pct = min_pct + (max_pct - min_pct) * confidence_normalized
        
        # Calculate actual position size
        position_size = balance * (position_pct / 100.0)
        
        # Apply absolute limits
        abs_min = params.get('absolute_min_sol', 0.1)
        abs_max = params.get('absolute_max_sol', 2.0)
        
        position_size = max(abs_min, position_size)
        position_size = min(abs_max, position_size)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"({position_pct:.1f}% of {balance:.4f} SOL balance)")
        
        return round(position_size, 4)
    
    @staticmethod
    def patch_trading_bot():
        """
        Instructions for patching your trading_bot.py
        """
        patch_code = '''
# In your trading_bot.py, find the calculate_position_size method
# and replace it with this:

def calculate_position_size(self, token_data: Dict[str, Any]) -> float:
    """Calculate position size based on percentage of balance"""
    try:
        # Load trading parameters
        with open('config/trading_params.json', 'r') as f:
            params = json.load(f)
        
        # Get current balance
        balance = self.get_current_balance()
        
        # Get ML confidence if available
        ml_confidence = token_data.get('ml_confidence', None)
        
        # Get percentage settings
        min_pct = params.get('min_position_size_pct', 3.0)
        default_pct = params.get('default_position_size_pct', 4.0)
        max_pct = params.get('max_position_size_pct', 5.0)
        
        # Calculate position percentage
        position_pct = default_pct
        
        if ml_confidence is not None and ml_confidence > 0:
            if ml_confidence >= 0.85:
                position_pct = max_pct
            elif ml_confidence <= 0.65:
                position_pct = min_pct
            else:
                # Linear interpolation
                confidence_range = 0.85 - 0.65
                confidence_normalized = (ml_confidence - 0.65) / confidence_range
                position_pct = min_pct + (max_pct - min_pct) * confidence_normalized
        
        # Calculate actual position size
        position_size = balance * (position_pct / 100.0)
        
        # Apply absolute limits
        abs_min = params.get('absolute_min_sol', 0.1)
        abs_max = params.get('absolute_max_sol', 2.0)
        
        position_size = max(abs_min, position_size)
        position_size = min(abs_max, position_size)
        
        self.logger.info(f"Position size: {position_size:.4f} SOL "
                        f"({position_pct:.1f}% of {balance:.4f} SOL)")
        
        return round(position_size, 4)
        
    except Exception as e:
        self.logger.error(f"Error calculating position size: {e}")
        # Fallback to safe default
        return 0.1

# Also, make sure your execute_buy method uses this:
# position_size = self.calculate_position_size(token_data)
# NOT any hardcoded values or bot_control.json values
'''
        return patch_code


# Quick test function
def test_position_sizing():
    """Test the position sizing with different balances"""
    print("Testing Position Sizing Logic")
    print("="*50)
    
    test_balances = [10, 50, 100]
    test_confidences = [0.65, 0.75, 0.85]
    
    for balance in test_balances:
        print(f"\nBalance: {balance} SOL")
        for confidence in test_confidences:
            size = PositionSizingFix.calculate_position_size(balance, confidence)
            pct = (size / balance) * 100
            print(f"  ML Confidence {confidence:.2f}: {size:.4f} SOL ({pct:.1f}%)")

if __name__ == "__main__":
    # Show the patch instructions
    print("POSITION SIZING FIX")
    print("="*80)
    print("\nThe issue: Your bot is using hardcoded values from bot_control.json")
    print("instead of the percentage-based system from trading_params.json")
    print("\nHere's the fix:")
    print("="*80)
    
    fixer = PositionSizingFix()
    print(fixer.patch_trading_bot())
    
    print("\n" + "="*80)
    print("Testing the correct logic:")
    print("="*80)
    test_position_sizing()
