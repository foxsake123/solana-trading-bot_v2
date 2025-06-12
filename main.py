# main.py (Final Version for Startup)

import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configs.unified_config import Config
from core.trading.enhanced_trading_bot import EnhancedTradingBot
from core.blockchain.solana_client import SolanaTrader
from core.data.token_scanner import TokenScanner
from core.data.market_data import MarketDataAggregator
from core.analysis.token_analyzer import TokenAnalyzer
from core.storage.database import Database
from core.trading.position_manager import PositionManager
from core.trading.risk_manager import RiskManager
from utils.logger import setup_logging

async def main(mode: str):
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create the one and only CONFIG instance for this session
    CONFIG = Config(mode=mode)

    logger.info(f"{'='*60}")
    logger.info(f"Solana Trading Bot v2 Starting - {mode.upper()} MODE")
    logger.info(f"{'='*60}")
    
    # Initialize all components to None for clean shutdown on startup failure
    trading_bot = None
    solana_client = None
    db = None

    try:
        # Check if essential env vars are loaded
        if not CONFIG.wallet_private_key or not CONFIG.solana_rpc_url:
            raise ValueError("Wallet private key or Solana RPC URL not found in .env file. Halting.")

        db = Database(CONFIG.get('database_path', 'data/sol_bot.db'))
        await db.initialize()   # <--- ADD THIS LINE
        
        solana_client = SolanaTrader(
            rpc_url=CONFIG.solana_rpc_url,
            private_key=CONFIG.wallet_private_key,
            simulation_mode=CONFIG.get('simulation_mode', True)
        )
        await solana_client.connect()
        
        balance_sol, balance_usd = await solana_client.get_wallet_balance()
        logger.info(f"Initial balance: {balance_sol:.4f} SOL (${balance_usd:.2f})")
        
        market_data = MarketDataAggregator(CONFIG.birdeye_api_key)
        risk_manager = RiskManager(CONFIG, balance_sol)
        position_manager = PositionManager(db, risk_manager, CONFIG)
        token_analyzer = TokenAnalyzer(db, market_data, CONFIG)
        token_scanner = TokenScanner(db, market_data, token_analyzer, CONFIG)
        
        trading_bot = EnhancedTradingBot(
            config=CONFIG,
            solana_client=solana_client,
            token_scanner=token_scanner,
            token_analyzer=token_analyzer,
            position_manager=position_manager,
            risk_manager=risk_manager,
            ml_predictor=None, # Simplified for now
            performance_tracker=None, # Simplified for now
            db=db # <--- ADD THIS LINE
        )
        
        logger.info("Starting trading bot...")
        await trading_bot.start()
        
        await asyncio.Event().wait() # Keep running indefinitely
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    except Exception as e:
        logger.error(f"A fatal error occurred in the main loop: {e}", exc_info=True)
    finally:
        logger.info("Closing connections...")
        if trading_bot:
            await trading_bot.stop()
        if solana_client:
            await solana_client.close()
        if db:
            await db.close()
        logger.info("Bot has been shut down.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Solana Trading Bot v2')
    parser.add_argument(
        '--mode', choices=['simulation', 'real'], default='simulation',
        help='Set the trading mode (default: simulation)'
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.mode))
    except KeyboardInterrupt:
        print("\nBot stopped by user.")