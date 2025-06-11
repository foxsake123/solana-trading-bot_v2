# core/trading/enhanced_trading_bot.py (Refactored for Strategy Integration)

import asyncio
import logging
from typing import Dict, Any

from configs.unified_config import Config
from core.blockchain.solana_client import SolanaTrader
from core.data.token_scanner import TokenScanner
from core.analysis.token_analyzer import TokenAnalyzer
from core.trading.position_manager import PositionManager
from core.trading.risk_manager import RiskManager
from ml.models.ml_predictor import MLPredictor
from monitoring.performance_tracker import PerformanceTracker
from core.storage.database import Database

logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    def __init__(self, config: Config, solana_client: SolanaTrader, token_scanner: TokenScanner,
                 token_analyzer: TokenAnalyzer, position_manager: PositionManager,
                 risk_manager: RiskManager, db: Database, ml_predictor = None,
                 performance_tracker = None): # <-- ADD "db: Database" HERE
        
        self.config = config
        self.solana_client = solana_client
        self.token_scanner = token_scanner
        self.token_analyzer = token_analyzer
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.db = db # <--- ADD THIS LINE
        self.ml_predictor = ml_predictor
        self.performance_tracker = performance_tracker
        
        self._running = False
        self.main_task = None
        
        self.trade_interval = self.config.get('trade_interval_seconds', 60)
        self.min_trade_score = self.config.get('min_trade_score', 75)

    async def start(self):
        """Starts the main trading bot loop."""
        if self._running:
            logger.warning("Bot is already running.")
            return

        self._running = True
        logger.info("Enhanced Trading Bot starting its main loop...")
        
        # Load any existing open positions from the last session
        await self.position_manager.load_open_positions()

        # Start the token scanner in the background
        asyncio.create_task(self.token_scanner.start())

        # Start the main trading loop
        self.main_task = asyncio.create_task(self._trading_loop())
        logger.info("Bot is now running.")

    async def stop(self):
        """Stops the main trading bot loop."""
        if not self._running:
            logger.warning("Bot is not running.")
            return
            
        self._running = False
        self.token_scanner.stop()
        if self.main_task:
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                logger.info("Main trading loop successfully cancelled.")
        
        logger.info("Enhanced Trading Bot stopped.")

    async def _trading_loop(self):
        """The core loop where decisions are made and trades are executed."""
        while self._running:
            try:
                logger.info("--- Starting new trading cycle ---")
                
                # 1. Evaluate existing open positions for selling opportunities
                await self._evaluate_open_positions()

                # 2. Find and evaluate new tokens for buying opportunities
                await self._evaluate_new_buy_opportunities()

                logger.info(f"--- Trading cycle complete. Waiting for {self.trade_interval} seconds. ---")
                await asyncio.sleep(self.trade_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"An error occurred in the trading loop: {e}", exc_info=True)
                # Avoid rapid-fire loops on persistent errors
                await asyncio.sleep(self.trade_interval)

    async def _evaluate_open_positions(self):
        """Checks all active positions to see if any should be closed."""
        open_positions = self.position_manager.get_all_active_positions().copy()
        if not open_positions:
            logger.info("No open positions to evaluate.")
            return
        
        logger.info(f"Evaluating {len(open_positions)} open position(s)...")
        for address, position in open_positions.items():
            # Get current price, stop loss, take profit
            market_data = await self.token_analyzer.market_data.get_full_token_data(address)
            if not market_data or not market_data.get('price'):
                logger.warning(f"Could not get market data for open position: {position['symbol']}. Skipping.")
                continue

            current_price = market_data['price']
            stop_loss_price = self.risk_manager.get_stop_loss_price(position['entry_price'])
            take_profit_price = self.risk_manager.get_take_profit_price(position['entry_price'])
            
            # Check for sell conditions
            sell_reason = None
            if current_price <= stop_loss_price:
                sell_reason = "stop_loss"
            elif current_price >= take_profit_price:
                sell_reason = "take_profit"
            
            if sell_reason:
                logger.info(f"Sell condition met for {position['symbol']}: {sell_reason}")
                # Execute sell trade
                # In a real scenario, you would call self.solana_client.execute_trade(...)
                # For simulation, we just close the position
                await self.position_manager.close_position(address, current_price, sell_reason)

    async def _evaluate_new_buy_opportunities(self):
        """Scans and analyzes new tokens to find buying opportunities."""
        # Get a list of potential tokens from the database (added by TokenScanner)
        potential_tokens = await self.db.get_all_tokens()
        logger.info(f"Found {len(potential_tokens)} potential tokens in DB to evaluate.")

        for token in potential_tokens:
            address = token['contract_address']
            # Skip if we already have a position
            if self.position_manager.get_position(address):
                continue
            
            # 1. Analyze the token to get its latest score
            analysis_result = await self.token_analyzer.analyze_token(address)
            if not analysis_result or 'final_score' not in analysis_result:
                continue

            score = analysis_result['final_score']
            logger.info(f"Token: {analysis_result.get('symbol', address)}, Score: {score:.2f}")

            # 2. Check if the score meets our buy threshold
            if score >= self.min_trade_score:
                logger.info(f"Buy signal for {analysis_result['symbol']}! Score ({score:.2f}) >= threshold ({self.min_trade_score}).")
                
                # 3. If it's a buy, calculate position size using the Risk Manager
                current_price = analysis_result.get('price', 0) # Assumes analyzer returns price
                if not current_price:
                    market_data = await self.token_analyzer.market_data.get_full_token_data(address)
                    current_price = market_data.get('price', 0)

                if current_price > 0:
                    position_size_usd = self.risk_manager.calculate_position_size(current_price, score)
                    
                    if position_size_usd > 0:
                        # 4. Execute the trade (simulation for now)
                        logger.info(f"Executing simulated BUY for {analysis_result['symbol']} of ${position_size_usd:.2f}")
                        
                        trade_details = {
                            "contract_address": address,
                            "symbol": analysis_result.get('symbol', 'N/A'),
                            "entry_price": current_price,
                            "position_size_usd": float(position_size_usd),
                            "reason": "strategy_buy_signal"
                        }
                        await self.position_manager.open_position(trade_details)
                else:
                    logger.warning(f"Cannot calculate position size for {analysis_result['symbol']}; price is zero.")