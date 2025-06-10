# core/data/jupiter_aggregator.py
"""
Jupiter Aggregator for optimal swap routing
"""

import aiohttp
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class JupiterAggregator:
    def __init__(self):
        self.quote_api = "https://quote-api.jup.ag/v6/quote"
        self.swap_api = "https://quote-api.jup.ag/v6/swap"
        
    async def get_best_route(self, input_mint: str, output_mint: str, amount: int) -> Optional[Dict]:
        """Get best swap route from Jupiter"""
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 300,  # 3% slippage
            "onlyDirectRoutes": False,
            "asLegacyTransaction": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.quote_api, params=params) as resp:
                    if resp.status == 200:
                        quote = await resp.json()
                        
                        if quote.get('data'):
                            best_route = quote['data'][0]
                            
                            return {
                                "route": best_route,
                                "output_amount": int(best_route['outAmount']),
                                "price_impact": float(best_route['priceImpactPct']),
                                "route_plan": best_route.get('routePlan', [])
                            }
        except Exception as e:
            logger.error(f"Jupiter quote error: {e}")
            
        return None
    
    async def execute_swap(self, route: Dict, wallet_keypair) -> Dict:
        """Execute swap through Jupiter"""
        # Note: Actual implementation requires transaction signing
        logger.info("Jupiter swap execution - implement with wallet signing")
        return {"success": False, "error": "Not implemented"}
