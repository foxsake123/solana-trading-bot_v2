#!/usr/bin/env python3
"""
Enhanced Bot Startup Script
Includes all necessary fixes and safety checks
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot components
from config.bot_config import BotConfiguration
from core.trading.trading_bot import TradingBot
from core.data.token_scanner import TokenScanner
from core.analysis.token_analyzer import TokenAnalyzer
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info("="*60)
    logger.info(f"Starting Solana Trading Bot - {mode.upper()} MODE")
    logger.info("="*60)
    
    try:
        # Load configuration
        config = BotConfiguration.load_config(mode)
        
        # Initialize database
        db = Database('data/db/sol_bot.db')
        
        # Initialize components
        token_analyzer = TokenAnalyzer(config, db, BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY'))
        solana_trader = SolanaTrader(
            rpc_url=BotConfiguration.RPC_URL,
            private_key=BotConfiguration.PRIVATE_KEY if mode == 'real' else None,
            simulation_mode=(mode != 'real')
        )
        
        # Initialize token scanner
        token_scanner = TokenScanner(db, solana_trader, token_analyzer)
        
        # Initialize trading bot
        trading_bot = TradingBot(config, db, token_scanner, solana_trader)
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(start_monitoring())
        
        # Start the bot
        logger.info("[LAUNCH] Starting trading bot...")
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if 'trading_bot' in locals():
            trading_bot.running = False
        logger.info("Bot stopped")

async def start_monitoring():
    """Start performance monitoring in background"""
    await asyncio.sleep(60)  # Wait 1 minute before starting monitor
    try:
        from monitoring.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        await monitor.start()
    except Exception as e:
        logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
