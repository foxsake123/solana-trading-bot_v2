#!/usr/bin/env python3
"""
Enhanced startup script for Solana Trading Bot v2 with all new features
"""
import asyncio
import logging
import sys
import json
from datetime import datetime

# Core imports
from config.bot_config import BotConfiguration
from core.data.token_scanner import TokenScanner
from core.data.market_data import BirdeyeAPI
from core.analysis.token_analyzer import TokenAnalyzer
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database
from dotenv import load_dotenv
load_dotenv()

# Import enhanced bot
from enhanced_trading_bot import EnhancedTradingBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Enhanced main entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info(f"{'='*60}")
    logger.info(f"Solana Trading Bot v2 ENHANCED - {mode.upper()} MODE")
    logger.info(f"{'='*60}")
    
    try:
        # Load configurations
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
        
        with open('config/trading_params.json', 'r') as f:
            trading_params = json.load(f)
        
        config.update(trading_params)
        config['BIRDEYE_API_KEY'] = BotConfiguration.API_KEYS['BIRDEYE_API_KEY']

        # Override simulation mode
        config['simulation_mode'] = (mode != 'real')
        
        # Show active features
        logger.info("🚀 ENHANCED FEATURES:")
        logger.info(f"   ✅ Citadel-Barra Strategy: {config.get('use_citadel_strategy', False)}")
        logger.info(f"   ✅ Twitter Sentiment: {bool(config.get('twitter', {}).get('bearer_token'))}")
        logger.info(f"   ✅ Partial Exits: {config.get('use_partial_exits', True)}")
        logger.info(f"   ✅ Whale Tracking: {bool(BotConfiguration.API_KEYS['BIRDEYE_API_KEY'],)}")
        logger.info(f"   ✅ Jupiter Routing: {config.get('use_jupiter', True)}")
        logger.info(f"   ✅ ML Auto-Retrain: {config.get('ml_auto_retrain', True)}")
        
        # Initialize database
        db = Database('data/db/sol_bot.db')
        
        # Initialize components
        solana_trader = SolanaTrader(db=db, simulation_mode=config['simulation_mode'])
        await solana_trader.connect()
        
        token_analyzer = TokenAnalyzer(config, db)
        token_scanner = TokenScanner(
            config,
            token_analyzer,
            BotConfiguration.API_KEYS['BIRDEYE_API_KEY'],
        )
        
        # Initialize ENHANCED trading bot
        trading_bot = EnhancedTradingBot(config, db, token_scanner, solana_trader)
        
        # Start Twitter trending discovery
        if config.get('twitter', {}).get('bearer_token'):
            asyncio.create_task(discover_trending_loop(trading_bot))
        
        # Start trading
        logger.info("🚀 Starting enhanced trading bot...")
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        if 'trading_bot' in locals():
            await trading_bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

async def discover_trending_loop(bot):
    """Discover trending tokens from Twitter"""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            await bot.discover_trending_tokens()
        except Exception as e:
            logger.error(f"Trending discovery error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
