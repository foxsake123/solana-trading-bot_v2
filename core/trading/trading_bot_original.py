# trading_bot.py - FIXED VERSION
import asyncio
import logging
import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger('trading_bot')

class TradingBot:
    """Trading bot that trades real Solana tokens with percentage-based position sizing"""
    
    def __init__(self, config: Dict, db: Any, token_scanner: Any, trader: Any):
        self.config = config
        self.db = db
        self.token_scanner = token_scanner
        self.trader = trader
        self.balance = config.get('starting_simulation_balance', 10.0)
        self.simulation_mode = config.get('simulation_mode', True)
        self.positions = {}
        self.running = False
        
        # Load trading parameters
        self.trading_params = self.load_trading_params()
        
        logger.info(f"Trading bot initialized in {'SIMULATION' if self.simulation_mode else 'REAL'} mode")
        logger.info(f"Starting balance: {self.balance} SOL")
        logger.info(f"Position sizing: {self.trading_params.get('min_position_size_pct', 3)}-{self.trading_params.get('default_position_size_pct', 4)}-{self.trading_params.get('max_position_size_pct', 5)}% of balance")
    
    def load_trading_params(self) -> Dict:
        """Load trading parameters from config file"""
        try:
            with open('config/trading_params.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trading params: {e}")
            # Return defaults
            return {
                'min_position_size_pct': 3.0,
                'default_position_size_pct': 4.0,
                'max_position_size_pct': 5.0,
                'absolute_min_sol': 0.1,
                'absolute_max_sol': 2.0,
                'max_open_positions': 10
            }
    
    def calculate_position_size(self, ml_confidence: float = None) -> float:
        """
        Calculate position size as percentage of balance
        
        Args:
            ml_confidence: ML model confidence score (0-1)
            
        Returns:
            Position size in SOL
        """
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
                # Linear interpolation between min and max
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
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"({position_pct:.1f}% of {self.balance:.4f} SOL balance)")
        
        return round(position_size, 4)
    
    async def start(self):
        """Start the trading bot"""
        logger.info("="*50)
        logger.info("   Real Token Trading Bot Starting")
        logger.info("="*50)
        
        self.running = True
        
        # Start token scanner in background
        asyncio.create_task(self.token_scanner.start_scanning())
        
        # Start main trading loop
        await self.trading_loop()
    
    async def trading_loop(self):
        """Main trading loop"""
        logger.info("Starting trading loop - looking for real tokens only")
        
        scan_interval = self.config.get('scan_interval', 60)
        
        while self.running:
            try:
                # Update balance
                if self.simulation_mode:
                    # In simulation mode, DON'T override balance from trader
                    # It returns wrong value (0.05 SOL)
                    logger.info(f"Current balance: {self.balance:.4f} SOL (simulation)")
                else:
                    # Real mode - get from wallet
                    balance_sol, balance_usd = await self.trader.get_wallet_balance()
                    self.balance = balance_sol
                    logger.info(f"Current balance: {self.balance:.4f} SOL")
                                
                # Check if we can open more positions
                max_positions = self.trading_params.get('max_open_positions', 10)
                if len(self.positions) >= max_positions:
                    logger.info(f"Max positions reached ({max_positions}), monitoring only")
                else:
                    # Get real tokens to analyze
                    await self.find_and_trade_tokens()
                
                # Monitor existing positions
                await self.monitor_positions()
                
                # Wait before next iteration
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)
    
    async def find_and_trade_tokens(self):
        """Find and trade real tokens"""
        try:
            # Get top gainers and trending tokens
            top_gainers = await self.token_scanner.get_top_gainers()
            trending = await self.token_scanner.get_trending_tokens()
            
            # Combine and deduplicate
            all_tokens = []
            seen = set()
            
            for token in top_gainers + trending:
                address = token.get('contract_address', token.get('address', ''))
                
                # Skip if already seen or if it's a simulation token
                if address in seen or address.startswith('Sim'):
                    continue
                    
                seen.add(address)
                all_tokens.append(token)
            
            logger.info(f"Found {len(all_tokens)} unique real tokens to analyze")
            
            # Analyze each token
            for token in all_tokens:
                await self.analyze_and_trade_token(token)
                
        except Exception as e:
            logger.error(f"Error finding tokens: {e}")
    
    async def analyze_and_trade_token(self, token: Dict):
        """Analyze a token and decide whether to trade"""
        try:
            address = token.get('contract_address', token.get('address', ''))
            ticker = token.get('ticker', token.get('symbol', 'UNKNOWN'))
            
            # Skip if we already have a position
            if address in self.positions:
                return
            
            # Get ML confidence if available
            ml_confidence = None
            
            # Analyze token
            if self.token_scanner.token_analyzer:
                analysis = await self.token_scanner.token_analyzer.analyze_token(address)
                
                if analysis.get('buy_recommendation', False):
                    logger.info(f"✅ Buy signal for {ticker} ({address[:8]}...)")
                    logger.info(f"   Reasons: {', '.join(analysis.get('reasons', []))}")
                    
                    # Get ML confidence from analysis
                    ml_confidence = analysis.get('ml_confidence', None)
                    
                    # Calculate position size using percentage-based system
                    amount = self.calculate_position_size(ml_confidence)
                    
                    # Check if we have enough balance
                    if self.balance >= amount:
                        await self.buy_token(address, amount)
                    else:
                        logger.warning(f"Insufficient balance for {amount:.4f} SOL position")
                else:
                    logger.debug(f"❌ No buy signal for {ticker}")
            else:
                # If no analyzer, use simple criteria
                price_change_24h = token.get('price_change_24h', 0)
                volume_24h = token.get('volume_24h', 0)
                
                # Check against trading params
                min_volume = self.trading_params.get('min_volume_24h', 30000)
                
                if price_change_24h > 5 and volume_24h > min_volume:
                    logger.info(f"✅ Simple buy signal for {ticker} (24h: +{price_change_24h:.1f}%)")
                    
                    # Calculate position size
                    amount = self.calculate_position_size()
                    
                    if self.balance >= amount:
                        await self.buy_token(address, amount)
                    
        except Exception as e:
            logger.error(f"Error analyzing token: {e}")
    
    async def buy_token(self, address: str, amount: float):
        """Buy a token"""
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
                
        except Exception as e:
            logger.error(f"Error buying token: {e}")
    
    async def monitor_positions(self):
        """Monitor existing positions for exit signals"""
        try:
            if not self.positions:
                return
            
            for address, position in list(self.positions.items()):
                # Get current token data
                if self.token_scanner.birdeye_api:
                    token_info = await self.token_scanner.birdeye_api.get_token_info(address)
                    
                    if token_info:
                        current_price = token_info.get('price_usd', 0)
                        entry_price = position.get('entry_price', 0.0001)
                        
                        if entry_price > 0 and current_price > 0:
                            pnl_pct = ((current_price / entry_price) - 1) * 100
                            
                            # Update highest price for trailing stop
                            if current_price > position.get('highest_price', 0):
                                position['highest_price'] = current_price
                            
                            # Get exit parameters from trading_params.json
                            take_profit_pct = self.trading_params.get('take_profit_pct', 0.5) * 100  # Convert to percentage
                            stop_loss_pct = self.trading_params.get('stop_loss_pct', 0.05) * 100
                            
                            # Check trailing stop if enabled
                            if self.trading_params.get('trailing_stop_enabled', True):
                                activation_pct = self.trading_params.get('trailing_stop_activation_pct', 0.3) * 100
                                distance_pct = self.trading_params.get('trailing_stop_distance_pct', 0.15) * 100
                                
                                if pnl_pct >= activation_pct:
                                    # Trailing stop activated
                                    highest_price = position['highest_price']
                                    trailing_stop_price = highest_price * (1 - distance_pct / 100)
                                    
                                    if current_price <= trailing_stop_price:
                                        logger.info(f"📉 Trailing stop hit for {address[:8]}... "
                                                   f"(Peak: +{((highest_price/entry_price)-1)*100:.1f}%, "
                                                   f"Exit: +{pnl_pct:.1f}%)")
                                        await self.sell_token(address, position['amount'], current_price)
                                        continue
                            
                            # Check regular take profit and stop loss
                            if pnl_pct >= take_profit_pct:
                                logger.info(f"🎯 Take profit hit for {address[:8]}... (+{pnl_pct:.1f}%)")
                                await self.sell_token(address, position['amount'], current_price)
                            elif pnl_pct <= -stop_loss_pct:
                                logger.info(f"🛑 Stop loss hit for {address[:8]}... ({pnl_pct:.1f}%)")
                                await self.sell_token(address, position['amount'], current_price)
                                
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    async def sell_token(self, address: str, amount: float, current_price: float = None):
        """Sell a token"""
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
                    
                    self.balance += sol_return
                    
                    logger.info(f"✅ Successfully sold {amount:.4f} SOL of {address[:8]}...")
                    logger.info(f"   Return: {sol_return:.4f} SOL (Profit: {profit_sol:+.4f} SOL)")
                else:
                    # Fallback if no price data
                    self.balance += amount
                
                # Remove position
                if address in self.positions:
                    del self.positions[address]
                
        except Exception as e:
            logger.error(f"Error selling token: {e}")
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping trading bot...")
        self.running = False