# core/trading/position_manager.py (Refactored)

import logging
from typing import Dict, Any, Optional

from core.storage.database import Database
from core.trading.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class PositionManager:
    """
    Manages the bot's open positions, including opening, closing, and tracking them.
    """
    def __init__(self, db: Database, risk_manager: RiskManager, config):
        """
        Initializes the PositionManager.

        Args:
            db: The database instance for persistence.
            risk_manager: The RiskManager instance for risk checks.
            config: The unified bot configuration object.
        """
        self.db = db
        self.risk_manager = risk_manager
        self.config = config
        self.active_positions = {}  # In-memory cache for speed
        logger.info("PositionManager initialized.")

    async def load_open_positions(self):
        """Loads all open positions from the database into the in-memory cache."""
        logger.info("Loading open positions from database...")
        open_positions_from_db = await self.db.get_open_positions()
        for pos in open_positions_from_db:
            self.active_positions[pos['contract_address']] = pos
        logger.info(f"Loaded {len(self.active_positions)} open positions.")

    async def open_position(self, trade_details: Dict[str, Any]) -> bool:
        """
        Opens a new position after checking risk viability.

        Args:
            trade_details: A dictionary containing all necessary trade info.
                           (e.g., contract_address, symbol, entry_price, etc.)

        Returns:
            True if the position was opened successfully, False otherwise.
        """
        contract_address = trade_details['contract_address']
        
        # Risk Check 1: Maximum number of active positions
        if not self.risk_manager.check_trade_viability(len(self.active_positions)):
            return False
            
        # Risk Check 2: Check if a position for this token is already open
        if contract_address in self.active_positions:
            logger.warning(f"Attempted to open a position for {trade_details['symbol']} but one already exists.")
            return False

        # All checks passed, proceed to open position
        logger.info(f"Opening new position for {trade_details['symbol']} at entry price ${trade_details['entry_price']:.6f}")
        
        # Add position to database
        position_id = await self.db.add_position(trade_details)
        if position_id:
            # Add to in-memory cache
            self.active_positions[contract_address] = await self.db.get_position(position_id)
            logger.info(f"Successfully opened and cached position for {trade_details['symbol']}. Position ID: {position_id}")
            return True
        
        logger.error(f"Failed to open position for {trade_details['symbol']} in the database.")
        return False

    async def close_position(self, contract_address: str, exit_price: float, reason: str) -> bool:
        """
        Closes an open position.

        Args:
            contract_address: The contract address of the token.
            exit_price: The price at which the position is being closed.
            reason: The reason for closing (e.g., 'take_profit', 'stop_loss').

        Returns:
            True if the position was closed successfully, False otherwise.
        """
        if contract_address not in self.active_positions:
            logger.warning(f"Attempted to close a position for {contract_address} but none was found.")
            return False

        position = self.active_positions[contract_address]
        
        profit_loss_pct = (exit_price / position['entry_price']) - 1
        logger.info(
            f"Closing position for {position['symbol']} due to {reason}. "
            f"Entry: ${position['entry_price']:.6f}, Exit: ${exit_price:.6f}, P/L: {profit_loss_pct:.2%}"
        )

        # Update position in the database
        success = await self.db.update_position(position['id'], exit_price, profit_loss_pct)

        if success:
            # Remove from in-memory cache
            del self.active_positions[contract_address]
            logger.info(f"Position for {position['symbol']} closed and removed from cache.")
            return True
        
        logger.error(f"Failed to close position for {position['symbol']} in the database.")
        return False

    def get_position(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Retrieves an active position from the cache."""
        return self.active_positions.get(contract_address)

    def get_all_active_positions(self) -> Dict[str, Any]:
        """Returns all active positions from the cache."""
        return self.active_positions