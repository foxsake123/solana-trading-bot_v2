#!/usr/bin/env python3
"""
Simple startup script for Solana Trading Bot v2
"""
import asyncio
import logging
import sys
import json
from datetime import datetime

# Add imports
from config.bot_config import BotConfiguration
from core.trading.trading_bot import TradingBot
from core.trading.position_manager import PositionManager
from core.data.token_scanner import TokenScanner
from core.data.market_data import BirdeyeAPI
from core.analysis.token_analyzer import TokenAnalyzer
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    # Determine mode from command line
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info(f"{'='*60}")
    logger.info(f"Solana Trading Bot v2 Starting - {mode.upper()} MODE")
    logger.info(f"{'='*60}")
    
    try:
        # Load bot control configuration
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
        
        # Override simulation mode from command line
        if mode == 'real':
            config['simulation_mode'] = False
        else:
            config['simulation_mode'] = True
        
        # Initialize database
        db = Database('data/db/sol_bot.db')
        
        # Initialize components
        solana_trader = SolanaTrader(db=db, simulation_mode=config['simulation_mode'])
        await solana_trader.connect()
        
        # Initialize token analyzer first
        token_analyzer = TokenAnalyzer(config, db)
        
        # Initialize token scanner with correct parameters
        token_scanner = TokenScanner(db, solana_trader, token_analyzer)
        
        # Set up BirdeyeAPI
        birdeye_api = BirdeyeAPI()
        token_scanner.birdeye_api = birdeye_api
        
        # Initialize trading bot
        trading_bot = TradingBot(config, db, token_scanner, solana_trader)
        
        logger.info(f"Bot initialized successfully in {mode} mode")
        logger.info(f"Simulation mode: {config['simulation_mode']}")
        logger.info(f"Starting balance: {config.get('starting_simulation_balance', 10.0)} SOL")
        
        # Start the bot
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if 'solana_trader' in locals():
            await solana_trader.close()

if __name__ == "__main__":
    asyncio.run(main())
