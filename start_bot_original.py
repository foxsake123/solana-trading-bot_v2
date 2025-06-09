#!/usr/bin/env python3
"""
Enhanced startup script for Solana Trading Bot v2 with Citadel-Barra Strategy
"""
import asyncio
import logging
import sys
import json
from datetime import datetime
import position_override  # Force larger position sizes

# Add imports
from config.bot_config import BotConfiguration
from core.trading.position_manager import PositionManager
from core.data.token_scanner import TokenScanner
from core.data.market_data import BirdeyeAPI
from core.analysis.token_analyzer import TokenAnalyzer
from core.blockchain.solana_client import SolanaTrader
from core.storage.database import Database

# Import the appropriate trading bot based on configuration
def get_trading_bot(config):
    """
    Return the appropriate trading bot based on configuration
    """
    use_citadel = config.get('use_citadel_strategy', False)
    
    if use_citadel:
        try:
            from enhanced_trading_bot import EnhancedTradingBot
            logger.info("Using Citadel-Barra Enhanced Trading Bot")
            return EnhancedTradingBot
        except ImportError:
            logger.warning("Enhanced Trading Bot not found, falling back to standard bot")
            from core.trading.trading_bot import TradingBot
            return TradingBot
    else:
        from core.trading.trading_bot import TradingBot
        logger.info("Using Standard Trading Bot")
        return TradingBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point with Citadel-Barra strategy support"""
    # Determine mode from command line
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info(f"{'='*60}")
    logger.info(f"Solana Trading Bot v2 Starting - {mode.upper()} MODE")
    logger.info(f"{'='*60}")
    
    try:
        # Load bot control configuration
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
        
        # Load trading parameters
        with open('config/trading_params.json', 'r') as f:
            trading_params = json.load(f)
        
        # Merge configurations
        config.update(trading_params)
        
        # Override simulation mode from command line
        if mode == 'real':
            config['simulation_mode'] = False
        else:
            config['simulation_mode'] = True
        
        # Check if Citadel-Barra strategy is enabled
        if config.get('use_citadel_strategy', False):
            logger.info("🏛️  Citadel-Barra Strategy ENABLED")
            logger.info(f"   Alpha Decay Half-life: {config.get('alpha_decay_halflife_hours', 24)} hours")
            logger.info(f"   Max Factor Exposure: {config.get('max_factor_exposure', 2.0)}")
            logger.info(f"   Target Idiosyncratic Ratio: {config.get('target_idiosyncratic_ratio', 0.6)}")
        
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
        
        # Get the appropriate trading bot class
        TradingBotClass = get_trading_bot(config)
        
        # Initialize trading bot
        trading_bot = TradingBotClass(config, db, token_scanner, solana_trader)
        
        logger.info(f"Bot initialized successfully in {mode} mode")
        logger.info(f"Simulation mode: {config['simulation_mode']}")
        logger.info(f"Starting balance: {config.get('starting_simulation_balance', 10.0)} SOL")
        
        # Display position sizing configuration
        logger.info(f"Position Sizing Configuration:")
        logger.info(f"   Min: {config.get('min_position_size_pct', 3.0)}% ({config.get('absolute_min_sol', 0.3)} SOL)")
        logger.info(f"   Default: {config.get('default_position_size_pct', 4.0)}%")
        logger.info(f"   Max: {config.get('max_position_size_pct', 5.0)}% ({config.get('absolute_max_sol', 0.5)} SOL)")
        
        # Start monitoring if Citadel strategy is enabled
        if config.get('use_citadel_strategy', False):
            logger.info("Starting Citadel-Barra performance monitoring...")
            # Could start a background monitoring task here
        
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