#!/usr/bin/env python3
"""
Simple Bot Starter - Minimal script to start the bot
"""
import asyncio
import logging
import sys
import json
import os

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot_starter')

async def start_bot():
    """Start the trading bot with minimal setup"""
    
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    logger.info("="*60)
    logger.info(f"STARTING SOLANA TRADING BOT - {mode.upper()} MODE")
    logger.info("="*60)
    
    try:
        # Import required modules
        from config.bot_config import BotConfiguration
        from core.trading.trading_bot import TradingBot
        from core.data.token_scanner import TokenScanner
        from core.analysis.token_analyzer import TokenAnalyzer
        from core.blockchain.solana_client import SolanaTrader
        from core.storage.database import Database
        from core.data.market_data import BirdeyeAPI
        
        # Load configuration
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
        
        # Override simulation mode
        config['simulation_mode'] = (mode != 'real')
        
        logger.info(f"Simulation Mode: {config['simulation_mode']}")
        logger.info(f"Starting Balance: {config.get('starting_simulation_balance', 10)} SOL")
        
        # Initialize database
        db_path = 'data/db/sol_bot.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db = Database(db_path)
        logger.info("[OK] Database initialized")
        
        # Initialize Solana client
        solana_trader = SolanaTrader(
            rpc_url=BotConfiguration.RPC_URL,
            private_key=BotConfiguration.PRIVATE_KEY if mode == 'real' else None,
            simulation_mode=config['simulation_mode'],
            db=db
        )
        await solana_trader.connect()
        logger.info("[OK] Solana client connected")
        
        # Initialize token analyzer
        birdeye_api_key = BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY')
        token_analyzer = TokenAnalyzer(config, db)
        
        # Set up BirdeyeAPI if key is available
        if birdeye_api_key:
            birdeye_api = BirdeyeAPI(birdeye_api_key)
            token_analyzer.birdeye_api = birdeye_api
            logger.info("[OK] BirdeyeAPI configured")
        else:
            logger.warning("[!] No Birdeye API key found")
        
        # Initialize token scanner
        token_scanner = TokenScanner(db, solana_trader, token_analyzer)
        
        # Set up BirdeyeAPI for scanner too
        if birdeye_api_key:
            token_scanner.birdeye_api = birdeye_api
        
        logger.info("[OK] Token scanner initialized")
        
        # Initialize trading bot
        trading_bot = TradingBot(config, db, token_scanner, solana_trader)
        logger.info("[OK] Trading bot initialized")
        
        # Quick config check
        logger.info("\\nConfiguration:")
        logger.info(f"- Min Position: {config.get('min_position_size_pct', 3)}%")
        logger.info(f"- Max Position: {config.get('max_position_size_pct', 5)}%")
        logger.info(f"- Win Rate Target: {config.get('target_win_rate', 85)}%")
        logger.info(f"- Citadel Strategy: {config.get('use_citadel_strategy', True)}")
        
        # Start the bot
        logger.info("\\n[LAUNCH] Starting trading loop...")
        logger.info("Press Ctrl+C to stop\\n")
        
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("\\nShutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped")

def check_requirements():
    """Check if all requirements are met"""
    issues = []
    
    # Check directories
    required_dirs = ['core', 'config', 'data', 'logs']
    for dir in required_dirs:
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)
    
    # Check files
    if not os.path.exists('data/safety_state.json'):
        # Create it
        safety_state = {
            'is_paused': False,
            'pause_reason': '',
            'daily_loss': 0.0,
            'daily_trades': 0,
            'last_reset': datetime.now().date().isoformat()
        }
        os.makedirs('data', exist_ok=True)
        with open('data/safety_state.json', 'w') as f:
            json.dump(safety_state, f, indent=2)
        logger.info("[FIX] Created safety_state.json")
    
    # Check config files
    if not os.path.exists('config/bot_control.json'):
        issues.append("Missing config/bot_control.json")
    
    if not os.path.exists('config/trading_params.json'):
        issues.append("Missing config/trading_params.json")
    
    return issues

def main():
    """Main entry point"""
    from datetime import datetime
    
    print("\\nSOLANA TRADING BOT STARTER")
    print("="*40)
    
    # Check requirements
    issues = check_requirements()
    if issues:
        print("\\n[ERROR] Missing requirements:")
        for issue in issues:
            print(f"  - {issue}")
        print("\\nPlease run setup script first")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
