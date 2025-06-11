# core/data/token_scanner.py (Final Version)

import asyncio
import logging
from typing import List, Dict, Any

from core.data.market_data import MarketDataManager
from core.analysis.token_analyzer import TokenAnalyzer
from core.storage.database import Database

logger = logging.getLogger(__name__)

class TokenScanner:
    """
    Scans for new tokens, filters them, and adds potential candidates to the database.
    """
    def __init__(self, db: Database, market_data: MarketDataManager, 
                 token_analyzer: TokenAnalyzer, config):
        self.db = db
        self.market_data = market_data
        self.token_analyzer = token_analyzer
        self.config = config

        self.scan_interval = self.config.get('scan_interval_seconds', 300)
        self.min_liquidity = self.config.get('min_liquidity_usd', 50000)
        
        self._running = False
        logger.info("TokenScanner initialized.")

    async def start(self):
        """Starts the continuous scanning process."""
        self._running = True
        logger.info(f"TokenScanner started. Will scan for new tokens every {self.scan_interval} seconds.")
        # Run the first scan immediately on startup
        await self.scan_for_new_tokens()
        
        while self._running:
            await asyncio.sleep(self.scan_interval)
            try:
                await self.scan_for_new_tokens()
            except Exception as e:
                logger.error(f"Error during token scan loop: {e}", exc_info=True)

    def stop(self):
        """Stops the scanning process."""
        self._running = False
        logger.info("TokenScanner stopping...")

    async def scan_for_new_tokens(self):
        """
        Fetches new tokens, filters them, and adds viable candidates to the database.
        """
        logger.info("Scanning for new tokens...")
        try:
            new_tokens = await self.market_data.get_new_token_pairs()
            if not new_tokens:
                logger.info("Token scanner did not receive any tokens from market data source.")
                return

            logger.info(f"Received {len(new_tokens)} tokens from Birdeye. Filtering and adding to DB...")
            
            added_count = 0
            for token in new_tokens:
                if await self.is_token_viable(token):
                    # If token is viable, add it to the database for the analyzer to pick up.
                    await self.db.add_token(
                        contract_address=token.get('address'),
                        symbol=token.get('symbol', 'N/A'),
                        name=token.get('name', 'N/A'),
                        initial_score=50 # Assign a neutral base score
                    )
                    added_count += 1
            
            if added_count > 0:
                logger.info(f"Added {added_count} new viable tokens to the database for analysis.")
            else:
                logger.info("No new viable tokens found in this scan.")

        except Exception as e:
            logger.error(f"Failed to complete token scan: {e}", exc_info=True)

    async def is_token_viable(self, token: Dict[str, Any]) -> bool:
        """
        Applies basic filters to determine if a token is worth adding to our database.
        """
        # Ensure token has an address and symbol
        address = token.get('address')
        symbol = token.get('symbol')
        if not address or not symbol:
            return False

        # Filter out tokens with very low liquidity
        liquidity = token.get('liquidity', {}).get('usd', 0)
        if liquidity < self.min_liquidity:
            return False

        # Check if we already have this token in our database
        exists = await self.db.get_token(address)
        if exists:
            return False

        return True