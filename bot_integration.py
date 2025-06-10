#!/usr/bin/env python3
"""
Complete Bot Integration Script
Brings together all components and starts the bot
"""
import asyncio
import json
import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot_integration')

class BotIntegration:
    """Handles complete bot integration and startup"""
    
    def __init__(self):
        self.mode = 'simulation'
        self.config = {}
        
    def check_environment(self):
        """Check if all required components are present"""
        logger.info("Checking environment...")
        
        required_dirs = ['core', 'config', 'data', 'logs', 'models']
        required_files = [
            'config/bot_control.json',
            'config/trading_params.json',
            'core/analysis/token_analyzer.py',
            'core/data/market_data.py'
        ]
        
        missing = []
        
        for dir in required_dirs:
            if not os.path.exists(dir):
                missing.append(f"Directory: {dir}")
                
        for file in required_files:
            if not os.path.exists(file):
                missing.append(f"File: {file}")
                
        if missing:
            logger.error("Missing components:")
            for item in missing:
                logger.error(f"  - {item}")
            return False
            
        logger.info("✅ All required components present")
        return True
    
    def apply_runtime_fixes(self):
        """Apply necessary runtime fixes"""
        logger.info("Applying runtime fixes...")
        
        # Fix 1: Ensure safety_state.json exists
        if not os.path.exists('data/safety_state.json'):
            safety_state = {
                'is_paused': False,
                'pause_reason': '',
                'daily_loss': 0.0,
                'daily_trades': 0,
                'last_reset': datetime.now().date().isoformat()
            }
            
            with open('data/safety_state.json', 'w') as f:
                json.dump(safety_state, f, indent=2)
            logger.info("✅ Created safety_state.json")
        
        # Fix 2: Update bot_control.json with optimized settings
        try:
            with open('config/bot_control.json', 'r') as f:
                bot_control = json.load(f)
            
            # Apply optimized settings
            bot_control.update({
                'min_position_size_pct': 4.0,
                'default_position_size_pct': 5.0,
                'max_position_size_pct': 7.0,
                'use_partial_exits': True,
                'use_citadel_strategy': True
            })
            
            with open('config/bot_control.json', 'w') as f:
                json.dump(bot_control, f, indent=2)
            logger.info("✅ Updated bot_control.json with optimized settings")
            
        except Exception as e:
            logger.warning(f"Could not update bot_control.json: {e}")
    
    async def test_birdeye_connection(self):
        """Test Birdeye API connection"""
        logger.info("Testing Birdeye API connection...")
        
        try:
            from core.data.market_data import BirdeyeAPI
            from config.bot_config import BotConfiguration
            
            api = BirdeyeAPI(BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY'))
            
            # Try to get token list
            tokens = await api.get_token_list(limit=5)
            
            if tokens:
                logger.info(f"✅ Birdeye API working - found {len(tokens)} tokens")
                for token in tokens[:3]:
                    logger.info(f"  - {token.get('symbol', 'Unknown')}: ${token.get('price', 0):.6f}")
                return True
            else:
                logger.warning("⚠️  Birdeye API returned no tokens")
                return False
                
        except Exception as e:
            logger.error(f"❌ Birdeye API error: {e}")
            return False
    
    async def start_bot_with_monitoring(self):
        """Start the bot with integrated monitoring"""
        logger.info("Starting bot with monitoring...")
        
        try:
            # Import after fixes are applied
            from enhanced_trading_bot import EnhancedTradingBot
            from core.data.token_scanner import TokenScanner
            from core.analysis.token_analyzer import TokenAnalyzer
            from core.blockchain.solana_client import SolanaTrader
            from core.storage.database import Database
            from config.bot_config import BotConfiguration
            
            # Load configuration
            config = BotConfiguration.load_config(self.mode)
            
            # Initialize database
            db = Database('data/db/sol_bot.db')
            
            # Initialize components
            logger.info("Initializing components...")
            
            # Token Analyzer with Birdeye
            token_analyzer = TokenAnalyzer(
                config=config,
                db=db,
                birdeye_api=BotConfiguration.API_KEYS.get('BIRDEYE_API_KEY')
            )
            
            # Solana Trader
            solana_trader = SolanaTrader(
                rpc_url=BotConfiguration.RPC_URL,
                private_key=BotConfiguration.PRIVATE_KEY if self.mode == 'real' else None,
                simulation_mode=(self.mode != 'real'),
                db=db
            )
            await solana_trader.connect()
            
            # Token Scanner
            token_scanner = TokenScanner(db, solana_trader, token_analyzer)
            
            # Initialize Enhanced Trading Bot
            trading_bot = EnhancedTradingBot(config, db, token_scanner, solana_trader)
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self.run_monitor_loop())
            
            # Start the bot
            logger.info("="*60)
            logger.info("🚀 STARTING ENHANCED SOLANA TRADING BOT")
            logger.info(f"Mode: {self.mode.upper()}")
            logger.info(f"Strategy: Citadel-Barra with Partial Exits")
            logger.info(f"Initial Balance: {config.get('starting_simulation_balance', 10)} SOL")
            logger.info("="*60)
            
            await trading_bot.start()
            
        except KeyboardInterrupt:
            logger.info("\\nShutdown requested by user...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            logger.info("Bot stopped")
    
    async def run_monitor_loop(self):
        """Run monitoring in background"""
        await asyncio.sleep(30)  # Wait 30 seconds before starting
        
        while True:
            try:
                # Simple performance check
                from simple_monitor import SimpleMonitor
                monitor = SimpleMonitor()
                stats = monitor.get_stats()
                
                if stats:
                    logger.info(f"Performance Update - Trades: {stats['total_trades']}, Profit: {stats['total_profit']:.4f} SOL")
                    
            except Exception as e:
                logger.debug(f"Monitor error: {e}")
                
            await asyncio.sleep(300)  # Update every 5 minutes
    
    async def run(self, mode='simulation'):
        """Run the complete integration"""
        self.mode = mode
        
        print("="*60)
        print("SOLANA TRADING BOT v2 - COMPLETE INTEGRATION")
        print("="*60)
        
        # Step 1: Check environment
        if not self.check_environment():
            print("\\n❌ Environment check failed. Please run setup script first.")
            return
        
        # Step 2: Apply fixes
        self.apply_runtime_fixes()
        
        # Step 3: Test Birdeye
        birdeye_ok = await self.test_birdeye_connection()
        if not birdeye_ok:
            print("\\n⚠️  Warning: Birdeye API not working properly")
            print("Bot will continue but may have limited functionality")
        
        # Step 4: Start bot
        await self.start_bot_with_monitoring()

async def main():
    """Main entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    if mode not in ['simulation', 'real']:
        print("Usage: python bot_integration.py [simulation|real]")
        sys.exit(1)
    
    if mode == 'real':
        print("\\n⚠️  WARNING: REAL TRADING MODE")
        print("This will use real SOL. Are you sure? (yes/no): ", end='')
        confirm = input().strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    integration = BotIntegration()
    await integration.run(mode)

if __name__ == "__main__":
    # Handle missing enhanced_trading_bot.py
    if not os.path.exists('enhanced_trading_bot.py'):
        print("Creating enhanced_trading_bot.py...")
        
        enhanced_bot_code = '''from core.trading.trading_bot import TradingBot
from core.safety.safety_manager import SafetyManager
from core.alerts.alert_manager import AlertManager, AlertLevel
import logging

logger = logging.getLogger('enhanced_trading_bot')

class EnhancedTradingBot(TradingBot):
    """Enhanced trading bot with Citadel-Barra strategy and partial exits"""
    
    def __init__(self, config, db, token_scanner, trader):
        super().__init__(config, db, token_scanner, trader)
        
        # Enhanced features
        self.use_partial_exits = config.get('use_partial_exits', True)
        self.use_citadel_strategy = config.get('use_citadel_strategy', True)
        
        logger.info("Enhanced Trading Bot initialized")
        logger.info(f"Partial Exits: {'ENABLED' if self.use_partial_exits else 'DISABLED'}")
        logger.info(f"Citadel Strategy: {'ENABLED' if self.use_citadel_strategy else 'DISABLED'}")
    
    async def calculate_position_size(self, token_data, signal_strength):
        """Enhanced position sizing with Citadel-Barra approach"""
        base_size = await super().calculate_position_size(token_data, signal_strength)
        
        if self.use_citadel_strategy:
            # Apply factor-based adjustments
            volatility_factor = 1.0 - (token_data.get('volatility', 0.5) * 0.3)
            liquidity_factor = min(token_data.get('liquidity_usd', 0) / 100000, 1.5)
            
            adjusted_size = base_size * volatility_factor * liquidity_factor
            
            # Ensure minimum position size
            adjusted_size = max(adjusted_size, 0.4)  # Minimum 0.4 SOL
            
            return round(adjusted_size, 4)
        
        return base_size
    
    async def monitor_position_for_exit(self, position):
        """Enhanced exit monitoring with partial exits"""
        if self.use_partial_exits:
            current_price = await self.get_current_price(position['token_address'])
            profit_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
            
            # Partial exit levels
            exit_levels = [
                (20, 0.25),   # 25% at 20% profit
                (50, 0.25),   # 25% at 50% profit
                (100, 0.25),  # 25% at 100% profit
                (200, 0.25)   # Final 25% at 200% profit
            ]
            
            for target_pct, exit_portion in exit_levels:
                if profit_pct >= target_pct and not position.get(f'exit_{target_pct}'):
                    # Execute partial exit
                    await self.execute_partial_exit(position, exit_portion, target_pct)
                    position[f'exit_{target_pct}'] = True
                    break
        
        # Standard exit monitoring
        return await super().monitor_position_for_exit(position)
'''
        
        with open('enhanced_trading_bot.py', 'w') as f:
            f.write(enhanced_bot_code)
        print("✅ Created enhanced_trading_bot.py")
    
    # Run the main function
    asyncio.run(main())
