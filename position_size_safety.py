"""
Position size safety check to prevent oversized positions
"""
import logging

logger = logging.getLogger(__name__)

def safe_position_size(calculated_size: float, balance: float, config: dict) -> float:
    """
    Ensure position size is reasonable
    
    :param calculated_size: The calculated position size
    :param balance: Current balance
    :param config: Configuration dict
    :return: Safe position size
    """
    # Get limits from config
    min_pct = config.get('min_position_size_pct', 4.0) / 100
    max_pct = config.get('max_position_size_pct', 8.0) / 100
    abs_min = config.get('absolute_min_sol', 0.4)
    abs_max = config.get('absolute_max_sol', 0.8)
    
    # Calculate percentage of balance
    if balance > 0:
        pct_of_balance = calculated_size / balance
        
        # Log if position is unreasonable
        if pct_of_balance > 0.5:  # More than 50% of balance
            logger.warning(f"Position size {calculated_size:.2f} is {pct_of_balance*100:.1f}% of balance!")
            logger.warning(f"Capping at {max_pct*100}% = {balance * max_pct:.2f} SOL")
            calculated_size = balance * max_pct
    
    # Apply percentage limits
    min_size = max(abs_min, balance * min_pct)
    max_size = min(abs_max, balance * max_pct)
    
    # Ensure within bounds
    safe_size = max(min_size, min(max_size, calculated_size))
    
    if safe_size != calculated_size:
        logger.info(f"Adjusted position size from {calculated_size:.4f} to {safe_size:.4f} SOL")
    
    return safe_size
