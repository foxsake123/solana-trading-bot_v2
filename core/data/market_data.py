# core/data/market_data.py (Refactored)

import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MarketDataManager:
    """
    Manages all interactions with external market data providers (e.g., Birdeye).
    """
    def __init__(self, config):
        """
        Initializes the MarketDataManager with the unified configuration object.

        Args:
            config: The unified bot configuration object.
        """
        self.config = config
        self.api_key = self.config.birdeye_api_key
        self.base_url = self.config.get('birdeye_base_url', "https://public-api.birdeye.so")
        
        if not self.api_key:
            logger.error("Birdeye API key is not configured. Market data fetching will fail.")
            # In a real application, you might want to raise an exception to stop the bot
            # raise ValueError("Birdeye API key is missing.")

        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }
        # Use a context-managed client for better resource handling
        self.client = httpx.AsyncClient(headers=self.headers, timeout=10.0)
        logger.info("MarketDataManager initialized.")

    # core/data/market_data.py

    async def get_new_token_pairs(self) -> List[Dict[str, Any]]:
        """
        Fetches a list of tokens filtered by a minimum liquidity threshold.
        This is a more robust method than relying on sorting.
        """
        # Get the minimum liquidity from our config to use in the API filter
        min_liquidity_filter = self.config.get('min_liquidity_usd', 50000)
        
        # New endpoint: We remove the failing 'sort_by' and add a 'liquidity_gte' filter
        # We also add a limit to get a manageable number of tokens.
        endpoint = f"/defi/v3/token/list?liquidity_gte={min_liquidity_filter}&limit=100"
        
        logger.info(f"Fetching token list from Birdeye with min liquidity >= ${min_liquidity_filter}...")
        try:
            response = await self.client.get(f"{self.base_url}{endpoint}")
            response.raise_for_status() 
            data = response.json()
            if data.get('success'):
                token_list = data.get('data', {}).get('tokens', [])
                logger.info(f"Successfully fetched {len(token_list)} tokens from Birdeye.")
                return token_list
            else:
                logger.warning(f"Birdeye API call was not successful: {data}")
                return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching token list: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching token list: {e}", exc_info=True)
        return []

    async def get_full_token_data(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetches comprehensive data for a single token using Birdeye's overview endpoint.
        """
        endpoint = f"/public/defi/v2/token_overview?address={contract_address}"
        logger.debug(f"Fetching full data for token: {contract_address}")
        try:
            response = await self.client.get(f"{self.base_url}{endpoint}")
            response.raise_for_status() # Will raise an exception for 4xx/5xx responses
            data = response.json()
            if data.get('success'):
                return data.get('data', {})
            else:
                logger.warning(f"Birdeye API did not return successful overview data for {contract_address}: {data}")
                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching token data for {contract_address}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"An error occurred fetching token data for {contract_address}: {e}", exc_info=True)
        return None