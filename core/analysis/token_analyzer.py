# core/analysis/token_analyzer.py (Refactored)

import logging
from typing import Dict, Any

from core.storage.database import Database
from core.data.market_data import MarketDataManager

logger = logging.getLogger(__name__)

class TokenAnalyzer:
    """
    Analyzes token data to generate a score and make trading decisions.
    """
    def __init__(self, db: Database, market_data: MarketDataManager, config):
        """
        Initializes the TokenAnalyzer.

        Args:
            db: The database instance.
            market_data: The MarketDataManager for fetching on-chain data.
            config: The unified bot configuration object.
        """
        self.db = db
        self.market_data = market_data
        self.config = config
        
        # Load factor weights from the unified config
        self.factor_weights = self.config.get('factor_weights', {})
        if not self.factor_weights:
            logger.warning("Factor weights not found in config. Analysis will be limited.")
        
        logger.info("TokenAnalyzer initialized.")

    async def analyze_token(self, contract_address: str) -> Dict[str, Any]:
        """
        Performs a full analysis of a token based on various factors.

        Args:
            contract_address: The contract address of the token to analyze.

        Returns:
            A dictionary containing the analysis results, including the final score.
        """
        logger.debug(f"Analyzing token: {contract_address}")
        
        # 1. Fetch all required data for analysis
        token_data = await self.market_data.get_full_token_data(contract_address)
        if not token_data:
            logger.warning(f"Could not retrieve market data for {contract_address}.")
            return {}

        # 2. Calculate individual factor scores
        factors = {
            "liquidity": self._score_liquidity(token_data),
            "volume": self._score_volume(token_data),
            "age": self._score_age(token_data),
            "market_cap": self._score_market_cap(token_data)
            # Future factors can be added here (e.g., holder distribution, social sentiment)
        }

        # 3. Calculate the final weighted score
        final_score = self._calculate_final_score(factors)

        analysis_result = {
            "contract_address": contract_address,
            "symbol": token_data.get('symbol', 'N/A'),
            "final_score": final_score,
            "factors": factors
        }
        
        # 4. Persist the analysis result to the database
        await self.db.add_analysis_record(analysis_result)
        
        logger.info(f"Analysis complete for {analysis_result['symbol']}. Final Score: {final_score:.2f}")
        return analysis_result

    def _calculate_final_score(self, factors: Dict[str, float]) -> float:
        """Calculates the weighted average score from individual factors."""
        total_score = 0
        total_weight = 0
        
        for factor_name, score in factors.items():
            weight = self.factor_weights.get(factor_name, 0)
            total_score += score * weight
            total_weight += weight
            
        if total_weight == 0:
            logger.warning("Total weight of factors is zero. Cannot calculate final score.")
            return 0
            
        return (total_score / total_weight) * 100 # Normalize to a 0-100 scale

    # --- Scoring Functions for each factor ---

    def _score_liquidity(self, token_data: Dict[str, Any]) -> float:
        """Scores token based on its liquidity. Returns a score between 0.0 and 1.0."""
        liquidity_usd = token_data.get('liquidity', {}).get('usd', 0)
        min_liq = self.config.get('min_liquidity_usd', 10000)
        max_liq = self.config.get('max_liquidity_usd', 1000000)
        
        if liquidity_usd < min_liq: return 0.0
        if liquidity_usd > max_liq: return 1.0
        
        return (liquidity_usd - min_liq) / (max_liq - min_liq)

    def _score_volume(self, token_data: Dict[str, Any]) -> float:
        """Scores token based on its 24h trading volume. Returns a score between 0.0 and 1.0."""
        volume_usd = token_data.get('volume', {}).get('h24', 0)
        min_vol = self.config.get('min_24h_volume_usd', 50000)
        
        return 1.0 if volume_usd > min_vol else 0.0

    def _score_age(self, token_data: Dict[str, Any]) -> float:
        """Scores token based on its age. Returns a score between 0.0 and 1.0."""
        # This is a simplified example. A real implementation would parse creation time.
        # For now, we'll assume newer tokens are riskier.
        # This logic needs to be enhanced with real on-chain creation time data.
        return 0.5 # Neutral score for now

    def _score_market_cap(self, token_data: Dict[str, Any]) -> float:
        """Scores token based on its market cap. Returns a score between 0.0 and 1.0."""
        # Market cap can be a proxy for stability.
        # This is a simplified example.
        mc = token_data.get('market_cap', 0)
        if mc > 1000000: return 1.0 # > $1M MC is good
        if mc > 250000: return 0.7
        if mc > 50000: return 0.4
        return 0.1