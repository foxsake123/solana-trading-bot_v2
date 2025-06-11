# debug_trading_execution.py
import asyncio
import json
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_trading_flow():
    """Debug why trades aren't executing"""
    
    # 1. Check trading parameters
    with open('config/trading_params.json', 'r') as f:
        params = json.load(f)
    
    logger.info("=== TRADING PARAMETERS ===")
    logger.info(f"Min token score: {params.get('min_token_score', 0.7)}")
    logger.info(f"Min ML confidence: {params.get('min_ml_confidence', 0.7)}")
    logger.info(f"Position size: {params.get('position_size_min', 0.03)} - {params.get('position_size_max', 0.05)}")
    logger.info(f"Simulation mode: {params.get('simulation_mode', True)}")
    
    # 2. Test token analyzer
    from core.analysis.token_analyzer import TokenAnalyzer
    from core.data.market_data import BirdeyeAPI
    
    analyzer = TokenAnalyzer({})
    birdeye = BirdeyeAPI(params.get('BIRDEYE_API_KEY'))
    
    # Get a real token to test
    logger.info("\n=== TESTING TOKEN ANALYSIS ===")
    trending = await birdeye.get_trending_tokens(limit=5)
    
    if trending:
        test_token = trending[0]
        logger.info(f"Testing token: {test_token.get('symbol')} ({test_token.get('address')})")
        
        # Analyze token
        analysis = await analyzer.analyze(test_token)
        logger.info(f"Analysis score: {analysis.get('score', 0)}")
        logger.info(f"Recommendation: {analysis.get('recommendation', 'SKIP')}")
        
        # Check if score meets threshold
        if analysis.get('score', 0) < params.get('min_token_score', 0.7):
            logger.warning(f"Score {analysis.get('score')} below threshold {params.get('min_token_score')}")
            logger.info("SOLUTION: Lower min_token_score in trading_params.json")
        
        # Check citadel strategy
        logger.info("\n=== TESTING CITADEL STRATEGY ===")
        from citadel_barra_strategy import CitadelBarraStrategy
        
        citadel = CitadelBarraStrategy(params, None)
        citadel_analysis = await citadel.analyze_token(test_token)
        
        logger.info(f"Combined alpha: {citadel_analysis.get('combined_alpha', 0)}")
        logger.info(f"Recommendation: {citadel_analysis.get('recommendation', 'SKIP')}")
        logger.info(f"Factors: {citadel_analysis.get('factors', {})}")
    
    # 3. Check balance tracking
    logger.info("\n=== CHECKING BALANCE ===")
    from core.blockchain.solana_trader import SolanaTrader
    
    trader = SolanaTrader(params)
    balance = trader.balance  # In simulation mode
    logger.info(f"Current balance: {balance} SOL")
    
    if balance < params.get('position_size_min', 0.03):
        logger.error("Balance too low for minimum position size!")
        logger.info("SOLUTION: Check solana_client.py wallet_balance initialization")
    
    # Close aiohttp session properly
    await birdeye.close()

if __name__ == "__main__":
    asyncio.run(debug_trading_flow())