#!/usr/bin/env python3
"""
Working Bot Starter - Uses correct SolanaTrader parameters
"""
import asyncio
import logging
import sys
import json
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot_starter')

async def start_bot():
    """Start the trading bot with correct parameters"""
    
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
        
        # Get API keys
        birdeye_api_key = BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY')
        
        logger.info(f"Simulation Mode: {config['simulation_mode']}")
        logger.info(f"Starting Balance: {config.get('starting_simulation_balance', 10)} SOL")
        logger.info(f"Birdeye API: {'Configured' if birdeye_api_key else 'Not configured'}")
        
        # Initialize database
        db_path = 'data/db/sol_bot.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db = Database(db_path)
        logger.info("[OK] Database initialized")
        
        # Initialize Solana client - CORRECTED PARAMETERS
        solana_trader = SolanaTrader(
            db=db,
            simulation_mode=config['simulation_mode']
        )
        await solana_trader.connect()
        logger.info("[OK] Solana client connected")
        
        # Get initial balance
        balance_sol, balance_usd = await solana_trader.get_wallet_balance()
        logger.info(f"Wallet Balance: {balance_sol:.4f} SOL (${balance_usd:.2f})")
        
        # Initialize token analyzer
        token_analyzer = TokenAnalyzer(config, db)
        
        # Set up BirdeyeAPI if key is available
        if birdeye_api_key:
            birdeye_api = BirdeyeAPI(birdeye_api_key)
            token_analyzer.birdeye_api = birdeye_api
            logger.info("[OK] BirdeyeAPI configured")
            
            # Test Birdeye connection
            try:
                test_tokens = await birdeye_api.get_token_list(limit=3)
                if test_tokens:
                    logger.info(f"[OK] Birdeye API working - found {len(test_tokens)} tokens")
                    for token in test_tokens[:2]:
                        logger.info(f"  - {token.get('symbol', 'Unknown')}: ${token.get('price', 0):.6f}")
            except Exception as e:
                logger.warning(f"[!] Birdeye API test failed: {e}")
        else:
            logger.warning("[!] No Birdeye API key found - limited functionality")
        
        # Initialize token scanner
        token_scanner = TokenScanner(db, solana_trader, token_analyzer)
        
        # Set up BirdeyeAPI for scanner too
        if birdeye_api_key:
            token_scanner.birdeye_api = birdeye_api
        
        logger.info("[OK] Token scanner initialized")
        
        # Initialize trading bot
        trading_bot = TradingBot(config, db, token_scanner, solana_trader)
        logger.info("[OK] Trading bot initialized")
        
        # Display configuration
        logger.info("\\nConfiguration Summary:")
        logger.info(f"- Position Size: {config.get('min_position_size_pct', 3)}-{config.get('max_position_size_pct', 5)}%")
        logger.info(f"- Min Position: {config.get('absolute_min_sol', 0.1)} SOL")
        logger.info(f"- Max Positions: {config.get('max_open_positions', 10)}")
        
        # Load and display trading parameters
        try:
            with open('config/trading_params.json', 'r') as f:
                trading_params = json.load(f)
                logger.info(f"- Stop Loss: {trading_params.get('stop_loss', 5)}%")
                logger.info(f"- Take Profit: {trading_params.get('take_profit', 50)}%")
                logger.info(f"- Citadel Strategy: {trading_params.get('use_citadel_strategy', True)}")
        except:
            pass
        
        # Check token analyzer has analyze method
        if hasattr(token_analyzer, 'analyze'):
            logger.info("[OK] TokenAnalyzer has analyze() method")
        else:
            logger.warning("[!] TokenAnalyzer missing analyze() method")
        
        # Final checks
        logger.info("\\n[CHECKS] Pre-flight verification:")
        logger.info(f"- Database: {'Connected' if db else 'Error'}")
        logger.info(f"- Solana Client: {'Connected' if solana_trader else 'Error'}")
        logger.info(f"- Token Scanner: {'Ready' if token_scanner else 'Error'}")
        logger.info(f"- Trading Bot: {'Ready' if trading_bot else 'Error'}")
        
        # Start the bot
        logger.info("\\n[LAUNCH] Starting trading loop...")
        logger.info("Press Ctrl+C to stop\\n")
        
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("\\nShutting down...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if 'solana_trader' in locals():
            await solana_trader.close()
        logger.info("Bot stopped")

def check_environment():
    """Quick environment check"""
    issues = []
    
    # Check directories
    for dir in ['core', 'config', 'data', 'logs']:
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)
    
    # Check safety state
    if not os.path.exists('data/safety_state.json'):
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
    
    # Check configs
    required_files = [
        'config/bot_control.json',
        'config/bot_config.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            issues.append(f"Missing: {file}")
    
    return issues

def main():
    """Main entry point"""
    print("\\nSOLANA TRADING BOT STARTER")
    print("="*40)
    
    # Check environment
    issues = check_environment()
    if issues:
        print("\\n[ERROR] Missing files:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()
