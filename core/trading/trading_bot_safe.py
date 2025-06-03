# trading_bot.py - WITH SAFETY FEATURES
import asyncio
import logging
import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import safety and alert managers
from core.safety import SafetyManager
from core.alerts import AlertManager, AlertLevel

logger = logging.getLogger('trading_bot')

class TradingBot:
    """Trading bot with safety features and alerts"""
    
    def __init__(self, config: Dict, db: Any, token_scanner: Any, trader: Any):
        self.config = config
        self.db = db
        self.token_scanner = token_scanner
        self.trader = trader
        self.balance = config.get('starting_simulation_balance', 10.0) if config.get('simulation_mode', True) else config.get('starting_balance', 2.0)
        self.simulation_mode = config.get('simulation_mode', True)
        self.positions = {}
        self.running = False
        
        # Initialize safety and alerts
        self.safety_manager = SafetyManager(config, db)
        self.alert_manager = AlertManager(config)
        
        # Load trading parameters
        self.trading_params = self.load_trading_params()
        
        # Send startup alert
        mode = 'SIMULATION' if self.simulation_mode else 'REAL'
        self.alert_manager.startup_alert(mode, self.balance)
        
        logger.info(f"Trading bot initialized in {mode} mode")
        logger.info(f"Starting balance: {self.balance} SOL")
        logger.info(f"Safety features: {'ENABLED' if not self.simulation_mode else 'SIMULATION MODE'}")
    
    def load_trading_params(self) -> Dict:
        """Load trading parameters from config file"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trading params: {e}")
            return {
                'min_position_size_pct': 3.0,
                'default_position_size_pct': 4.0,
                'max_position_size_pct': 5.0,
                'absolute_min_sol': 0.1,
                'absolute_max_sol': 2.0,
                'max_open_positions': 10
            }
    
    def calculate_position_size(self, ml_confidence: float = None) -> float:
        """Calculate position size with safety checks"""
        # Reload params to get latest values
        self.trading_params = self.load_trading_params()
        
        # Get percentage settings
        min_pct = self.trading_params.get('min_position_size_pct', 3.0)
        default_pct = self.trading_params.get('default_position_size_pct', 4.0)
        max_pct = self.trading_params.get('max_position_size_pct', 5.0)
        
        # Start with default percentage
        position_pct = default_pct
        
        # Adjust based on ML confidence if provided
        if ml_confidence is not None and ml_confidence > 0:
            if ml_confidence >= 0.85:
                position_pct = max_pct
            elif ml_confidence <= 0.65:
                position_pct = min_pct
            else:
                confidence_range = 0.85 - 0.65
                confidence_normalized = (ml_confidence - 0.65) / confidence_range
                position_pct = min_pct + (max_pct - min_pct) * confidence_normalized
        
        # Calculate actual position size
        position_size = self.balance * (position_pct / 100.0)
        
        # Apply absolute limits
        abs_min = self.trading_params.get('absolute_min_sol', 0.1)
        abs_max = self.trading_params.get('absolute_max_sol', 2.0)
        
        position_size = max(abs_min, position_size)
        position_size = min(abs_max, position_size)
        
        # Apply safety manager validation
        position_size = self.safety_manager.validate_position_size(position_size, self.balance, ml_confidence)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"({position_pct:.1f}% of {self.balance:.4f} SOL balance)")
        
        return round(position_size, 4)
    
    async def start(self):
        """Start the trading bot with safety checks"""
        logger.info("="*50)
        logger.info("   Trading Bot Starting with Safety Features")
        logger.info("="*50)
        
        self.running = True
        
        # Load safety state
        self.safety_manager.load_state()
        
        # Start token scanner in background
        asyncio.create_task(self.token_scanner.start_scanning())
        
        # Start main trading loop
        await self.trading_loop()
    
    async def trading_loop(self):
        """Main trading loop with safety checks"""
        logger.info("Starting trading loop")
        
        scan_interval = self.config.get('scan_interval', 60)
        
        while self.running:
            try:
                # Check if we can trade
                can_trade, reason = self.safety_manager.can_trade(self.balance)
                if not can_trade:
                    logger.warning(f"Trading blocked: {reason}")
                    self.alert_manager.send_alert(f"Trading blocked: {reason}", AlertLevel.WARNING)
                    await asyncio.sleep(scan_interval)
                    continue
                
                # Update balance
                if self.simulation_mode:
                    logger.info(f"Current balance: {self.balance:.4f} SOL (simulation)")
                else:
                    balance_sol, balance_usd = await self.trader.get_wallet_balance()
                    self.balance = balance_sol
                    logger.info(f"Current balance: {self.balance:.4f} SOL (${balance_usd:.2f})")
                    
                    # Send balance update every hour
                    if datetime.now().minute == 0:
                        self.alert_manager.balance_alert(self.balance, self.safety_manager.daily_loss)
                
                # Check if we can open more positions
                max_positions = self.trading_params.get('max_open_positions', 10)
                if len(self.positions) >= max_positions:
                    logger.info(f"Max positions reached ({max_positions}), monitoring only")
                else:
                    # Find and trade tokens
                    await self.find_and_trade_tokens()
                
                # Monitor existing positions
                await self.monitor_positions()
                
                # Save safety state
                self.safety_manager.save_state()
                
                # Wait before next iteration
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                self.alert_manager.error_alert(str(e), "trading loop")
                
                # Emergency stop on critical errors
                if not self.simulation_mode and "insufficient funds" in str(e).lower():
                    self.safety_manager.emergency_stop("Insufficient funds error")
                
                await asyncio.sleep(30)
    
    async def buy_token(self, address: str, amount: float):
        """Buy a token with alerts"""
        try:
            # Get current price for position tracking
            current_price = 0.0001
            if self.token_scanner.birdeye_api:
                token_info = await self.token_scanner.birdeye_api.get_token_info(address)
                if token_info:
                    current_price = token_info.get('price_usd', 0.0001)
            
            # Execute trade
            tx_hash = await self.trader.buy_token(address, amount)
            
            if tx_hash:
                # Update balance
                self.balance -= amount
                
                # Track position
                self.positions[address] = {
                    'amount': amount,
                    'entry_time': datetime.now(timezone.utc),
                    'entry_price': current_price,
                    'highest_price': current_price
                }
                
                logger.info(f"✅ Successfully bought {amount:.4f} SOL of {address[:8]}...")
                logger.info(f"   TX: {tx_hash}")
                logger.info(f"   Entry price: ${current_price:.6f}")
                
                # Send trade alert
                self.alert_manager.trade_alert("BUY", address, amount, current_price, tx_hash)
                
        except Exception as e:
            logger.error(f"Error buying token: {e}")
            self.alert_manager.error_alert(str(e), f"buying {address[:8]}...")
    
    async def sell_token(self, address: str, amount: float, current_price: float = None):
        """Sell a token with alerts"""
        try:
            tx_hash = await self.trader.sell_token(address, amount)
            
            if tx_hash:
                # Calculate actual return
                position = self.positions.get(address, {})
                entry_price = position.get('entry_price', 0.0001)
                
                if current_price and entry_price > 0:
                    # Calculate actual SOL return
                    price_multiple = current_price / entry_price
                    sol_return = amount * price_multiple
                    profit_sol = sol_return - amount
                    profit_pct = (price_multiple - 1) * 100
                    
                    self.balance += sol_return
                    
                    # Record trade result
                    self.safety_manager.record_trade_result(profit_sol)
                    
                    logger.info(f"✅ Successfully sold {amount:.4f} SOL of {address[:8]}...")
                    logger.info(f"   Return: {sol_return:.4f} SOL (Profit: {profit_sol:+.4f} SOL)")
                    
                    # Send alerts
                    self.alert_manager.trade_alert("SELL", address, amount, current_price, tx_hash)
                    self.alert_manager.profit_alert(address, profit_sol, profit_pct)
                    
                else:
                    # Fallback if no price data
                    self.balance += amount
                
                # Remove position
                if address in self.positions:
                    del self.positions[address]
                
        except Exception as e:
            logger.error(f"Error selling token: {e}")
            self.alert_manager.error_alert(str(e), f"selling {address[:8]}...")
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False
        
        # Send shutdown alert
        self.alert_manager.shutdown_alert("Manual stop requested")
        
        # Save final state
        self.safety_manager.save_state()
    
    # ... (rest of the existing methods remain the same) ...
