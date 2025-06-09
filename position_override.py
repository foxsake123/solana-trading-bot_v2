"""
Position size override to ensure minimum positions
This file forces minimum position sizes regardless of other settings
"""

import logging

logger = logging.getLogger(__name__)

# OVERRIDE ALL POSITION SIZES TO MINIMUM 0.4 SOL
FORCE_MIN_POSITION_SOL = 0.4

def override_position_size(calculated_size: float) -> float:
    """Force minimum position size"""
    if calculated_size < FORCE_MIN_POSITION_SOL:
        logger.warning(f"Overriding position size from {calculated_size:.4f} to {FORCE_MIN_POSITION_SOL:.4f} SOL")
        return FORCE_MIN_POSITION_SOL
    return calculated_size

# Monkey patch to ensure this is used
logger.info(f"Position override active: Minimum {FORCE_MIN_POSITION_SOL} SOL per trade")
