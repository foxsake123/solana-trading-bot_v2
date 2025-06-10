# enhanced_trading_bot.py
"""
Enhanced Trading Bot with Citadel-Barra Strategy
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

# Import base components
from core.trading.trading_bot import TradingBot
from citadel_barra_strategy import CitadelBarraStrategy

logger = logging.getLogger(__name__)

class EnhancedTradingBot(TradingBot):
    """Enhanced bot with Citadel-Barra strategy"""
    
    def __init__(self, config, db, token_scanner, solana_trader):
        super().__init__(config, db, token_scanner, solana_trader)

        # Initialize Birdeye API properly
        if hasattr(token_scanner, 'birdeye_api') and not token_scanner.birdeye_api:
            from core.data.market_data import BirdeyeAPI
            token_scanner.birdeye_api = BirdeyeAPI(config.get('BIRDEYE_API_KEY'))
            logger.info(f"Birdeye API initialized: {scanner.birdeye_api.is_available}")
        
        # Initialize Citadel-Barra strategy
        self.citadel_strategy = CitadelBarraStrategy(config, db)
        
        # Performance tracking
        self.feature_performance = {
            'citadel_signals': {'trades': 0, 'profitable': 0}
        }
        
        logger.info("🚀 Enhanced Trading Bot initialized with Citadel-Barra strategy")
    
    async def analyze_token(self, token_data: Dict) -> Dict:
        """Enhanced token analysis with Citadel strategy"""
        
        # Use Citadel-Barra analysis
        citadel_analysis = await self.citadel_strategy.analyze_token(token_data)
        
        # Make trading decision
        recommendation = citadel_analysis['recommendation']
        
        return {
            'recommendation': recommendation,
            'score': citadel_analysis.get('combined_alpha', 0),
            'citadel_signals': citadel_analysis,
            'reasons': citadel_analysis.get('reasons', [])
        }
    
    async def execute_buy(self, token_data: Dict, analysis: Dict) -> Dict:
        """Execute buy with Citadel position sizing"""
        
        # Get current balance
        balance = await self.solana_trader.get_sol_balance()
        
        # Calculate position size using Citadel strategy
        position_size = self.citadel_strategy.calculate_position_size(
            token_data, 
            analysis['citadel_signals']['factors'],
            analysis['citadel_signals']['alpha_signals'],
            balance
        )
        
        logger.info(f"📊 Citadel position size: {position_size:.4f} SOL")
        
        # Execute buy
        result = await self.solana_trader.buy_token(
            token_data['contract_address'],
            position_size
        )
        
        if result.get('success'):
            self.feature_performance['citadel_signals']['trades'] += 1
        
        return result
    
    async def check_exit_conditions(self, position: Dict, current_data: Dict) -> bool:
        """Check Citadel exit conditions"""
        
        # Get entry factors (simplified - would be stored in real implementation)
        entry_factors = self.citadel_strategy.calculate_barra_factors(position)
        
        # Check if should exit
        should_exit, reason = self.citadel_strategy.should_exit_position(
            position, current_data, entry_factors
        )
        
        if should_exit:
            logger.info(f"🚪 Citadel exit signal: {reason}")
        
        return should_exit
