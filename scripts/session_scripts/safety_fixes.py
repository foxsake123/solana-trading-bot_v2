#!/usr/bin/env python3
"""
Safety Measures and Alerts Implementation for Trading Bot
Run this script to add safety features to your trading bot
"""

import json
import os
import shutil
from datetime import datetime

def update_bot_control_real():
    """Update bot_control_real.json with proper real trading settings"""
    
    config = {
        "max_open_positions": 5,  # Reduced for real trading
        "take_profit_target": 1.3,
        "stop_loss_percentage": 0.05,
        "trailing_stop_enabled": True,
        "trailing_stop_percentage": 0.1,
        "MIN_SAFETY_SCORE": 0.0,
        "MIN_VOLUME": 10000.0,  # Increased for real trading
        "MIN_LIQUIDITY": 10000.0,  # Increased for real trading
        "MIN_MCAP": 50000.0,  # Increased for real trading
        "MIN_HOLDERS": 50,  # Increased for real trading
        "MAX_PRICE_CHANGE_24H": 1000.0,  # Reduced from 10000
        "MIN_PRICE_CHANGE_24H": -30.0,  # Tightened from -50
        "MIN_PRICE_CHANGE_1H": -20.0,  # Tightened from -50
        "MIN_PRICE_CHANGE_6H": -30.0,  # Tightened from -50
        "use_machine_learning": True,
        "ml_confidence_threshold": 0.75,  # Increased for safety
        "slippage_tolerance": 0.05,  # Reduced for real trading
        "slippage_tolerance_display": 5.0,
        "simulation_mode": False,  # REAL TRADING MODE
        "starting_balance": 2.0,  # Your real wallet balance
        "running": True,
        "filter_fake_tokens": True,  # Enable for safety
        "use_birdeye_api": True,
        "position_sizing_config": "See config/trading_params.json",
        "use_percentage_sizing": True,
        "max_daily_loss_percentage": 0.05,  # 5% daily loss limit
        "max_position_size_sol": 0.1,  # Maximum 0.1 SOL per trade initially
        "alert_webhook_url": "",  # Add your Discord/Telegram webhook
        "require_high_confidence": True,
        "pause_on_daily_loss": True,
        "real_wallet_address": "YOUR_WALLET_ADDRESS_HERE"  # Update this
    }
    
    # Backup existing config
    if os.path.exists('config/bot_control_real.json'):
        backup_name = f'config/bot_control_real_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        shutil.copy('config/bot_control_real.json', backup_name)
        print(f"✅ Backed up existing config to {backup_name}")
    
    # Save new config
    with open('config/bot_control_real.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    print("✅ Updated bot_control_real.json for real trading")
    print("⚠️  Remember to update 'real_wallet_address' with your actual wallet!")
    
def create_safety_module():
    """Create safety_manager.py module"""
    
    # Create the directory first
    os.makedirs('core/safety', exist_ok=True)
    
    safety_code = '''#!/usr/bin/env python3
"""
Safety Manager for Real Trading
Implements daily loss limits, position size limits, and emergency stops
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SafetyManager:
    """Manages trading safety features and risk limits"""
    
    def __init__(self, config: Dict, db):
        self.config = config
        self.db = db
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now(timezone.utc).date()
        self.is_paused = False
        self.pause_reason = ""
        
    def check_daily_reset(self):
        """Reset daily counters if new day"""
        current_date = datetime.now(timezone.utc).date()
        if current_date > self.last_reset:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.last_reset = current_date
            logger.info(f"🔄 Daily counters reset for {current_date}")
    
    def can_trade(self, balance: float) -> tuple[bool, str]:
        """Check if trading is allowed based on safety rules"""
        self.check_daily_reset()
        
        # Check if manually paused
        if self.is_paused:
            return False, f"Trading paused: {self.pause_reason}"
        
        # Check daily loss limit
        max_daily_loss_pct = self.config.get('max_daily_loss_percentage', 0.05)
        max_daily_loss = balance * max_daily_loss_pct
        
        if abs(self.daily_loss) >= max_daily_loss:
            if self.config.get('pause_on_daily_loss', True):
                self.is_paused = True
                self.pause_reason = f"Daily loss limit reached: {self.daily_loss:.4f} SOL"
            return False, f"Daily loss limit reached: {self.daily_loss:.4f} SOL (limit: {max_daily_loss:.4f} SOL)"
        
        # Check minimum balance
        min_balance = self.config.get('min_trading_balance', 0.5)
        if balance < min_balance:
            return False, f"Balance too low: {balance:.4f} SOL (minimum: {min_balance} SOL)"
        
        # Check max daily trades
        max_daily_trades = self.config.get('max_daily_trades', 100)
        if self.daily_trades >= max_daily_trades:
            return False, f"Max daily trades reached: {self.daily_trades}"
        
        return True, "OK"
    
    def validate_position_size(self, amount: float, balance: float, ml_confidence: float = None) -> float:
        """Validate and adjust position size based on safety rules"""
        # Maximum position size in SOL
        max_position_sol = self.config.get('max_position_size_sol', 0.1)
        
        # Maximum percentage of balance
        if self.config.get('simulation_mode', True):
            max_position_pct = 0.05  # 5% in simulation
        else:
            # Real trading: start very conservative
            if balance < 5:
                max_position_pct = 0.02  # 2% for small balances
            elif balance < 10:
                max_position_pct = 0.015  # 1.5% for medium balances
            else:
                max_position_pct = 0.01  # 1% for larger balances
        
        max_by_pct = balance * max_position_pct
        
        # Apply ML confidence adjustment if required
        if self.config.get('require_high_confidence', True) and ml_confidence:
            if ml_confidence < 0.75:
                amount *= 0.5  # Halve position for lower confidence
        
        # Take minimum of all limits
        safe_amount = min(amount, max_position_sol, max_by_pct)
        
        if safe_amount < amount:
            logger.warning(f"Position size reduced from {amount:.4f} to {safe_amount:.4f} SOL for safety")
        
        return safe_amount
    
    def record_trade_result(self, pnl: float):
        """Record trade result for daily tracking"""
        self.daily_loss += pnl
        self.daily_trades += 1
        
        logger.info(f"📊 Daily P&L: {self.daily_loss:+.4f} SOL ({self.daily_trades} trades)")
        
        # Check if we should pause
        if pnl < 0 and abs(self.daily_loss) > 0.5:  # Large daily loss
            logger.warning(f"⚠️  Significant daily loss: {self.daily_loss:.4f} SOL")
    
    def emergency_stop(self, reason: str):
        """Emergency stop trading"""
        self.is_paused = True
        self.pause_reason = f"EMERGENCY STOP: {reason}"
        logger.critical(f"🚨 {self.pause_reason}")
        
        # Save state
        self.save_state()
    
    def resume_trading(self):
        """Resume trading after pause"""
        self.is_paused = False
        self.pause_reason = ""
        logger.info("✅ Trading resumed")
    
    def get_status(self) -> Dict:
        """Get current safety status"""
        return {
            'is_paused': self.is_paused,
            'pause_reason': self.pause_reason,
            'daily_loss': self.daily_loss,
            'daily_trades': self.daily_trades,
            'last_reset': self.last_reset.isoformat()
        }
    
    def save_state(self):
        """Save safety state to file"""
        state = self.get_status()
        with open('data/safety_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load safety state from file"""
        try:
            with open('data/safety_state.json', 'r') as f:
                state = json.load(f)
                self.is_paused = state.get('is_paused', False)
                self.pause_reason = state.get('pause_reason', '')
                self.daily_loss = state.get('daily_loss', 0.0)
                self.daily_trades = state.get('daily_trades', 0)
                self.last_reset = datetime.fromisoformat(state.get('last_reset', datetime.now(timezone.utc).date().isoformat())).date()
        except FileNotFoundError:
            logger.info("No saved safety state found, starting fresh")
'''
    
    with open('core/safety/safety_manager.py', 'w', encoding='utf-8') as f:
        f.write(safety_code)
    
    # Create __init__.py
    os.makedirs('core/safety', exist_ok=True)
    with open('core/safety/__init__.py', 'w', encoding='utf-8') as f:
        f.write('from .safety_manager import SafetyManager\n')
    
    print("✅ Created core/safety/safety_manager.py")

def create_alert_module():
    """Create alert_manager.py module"""
    
    alert_code = '''#!/usr/bin/env python3
"""
Alert Manager for Trading Bot
Sends notifications for important events via Discord, Telegram, or console
"""

import json
import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.webhook_url = config.get('alert_webhook_url', '')
        self.enabled = config.get('alerts_enabled', True)
        self.min_alert_interval = 60  # Minimum seconds between similar alerts
        self.last_alerts = {}
        
    def send_alert(self, message: str, level: AlertLevel = AlertLevel.INFO, data: Dict = None):
        """Send alert through configured channels"""
        if not self.enabled:
            return
        
        # Rate limiting
        alert_key = f"{level.value}:{message[:50]}"
        if not self._should_send_alert(alert_key):
            return
        
        # Format message with emoji
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.SUCCESS: "✅",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨"
        }
        
        formatted_message = f"{emoji_map[level]} **{level.value.upper()}**: {message}"
        
        # Add timestamp
        formatted_message = f"[{datetime.now().strftime('%H:%M:%S')}] {formatted_message}"
        
        # Add data if provided
        if data:
            formatted_message += f"\\n```json\\n{json.dumps(data, indent=2)}\\n```"
        
        # Console output (always)
        self._console_alert(message, level, data)
        
        # Discord webhook
        if self.webhook_url and self.webhook_url.startswith('https://discord.com/api/webhooks/'):
            self._send_discord_alert(formatted_message, level)
        
        # Telegram (if configured)
        telegram_token = self.config.get('telegram_bot_token', '')
        telegram_chat_id = self.config.get('telegram_chat_id', '')
        if telegram_token and telegram_chat_id:
            self._send_telegram_alert(message, level, telegram_token, telegram_chat_id)
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (rate limiting)"""
        now = datetime.now()
        if alert_key in self.last_alerts:
            last_sent = self.last_alerts[alert_key]
            if (now - last_sent).total_seconds() < self.min_alert_interval:
                return False
        
        self.last_alerts[alert_key] = now
        return True
    
    def _console_alert(self, message: str, level: AlertLevel, data: Dict = None):
        """Print alert to console with color"""
        from colorama import Fore, Style
        
        color_map = {
            AlertLevel.INFO: Fore.CYAN,
            AlertLevel.SUCCESS: Fore.GREEN,
            AlertLevel.WARNING: Fore.YELLOW,
            AlertLevel.CRITICAL: Fore.RED
        }
        
        color = color_map[level]
        print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {level.value.upper()}: {message}{Style.RESET_ALL}")
        
        if data:
            print(f"{color}Data: {json.dumps(data, indent=2)}{Style.RESET_ALL}")
    
    def _send_discord_alert(self, message: str, level: AlertLevel):
        """Send alert to Discord webhook"""
        try:
            color_map = {
                AlertLevel.INFO: 3447003,      # Blue
                AlertLevel.SUCCESS: 3066993,   # Green
                AlertLevel.WARNING: 15844367,  # Yellow
                AlertLevel.CRITICAL: 15158332  # Red
            }
            
            payload = {
                "embeds": [{
                    "description": message,
                    "color": color_map[level],
                    "footer": {
                        "text": "Solana Trading Bot"
                    }
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    def _send_telegram_alert(self, message: str, level: AlertLevel, token: str, chat_id: str):
        """Send alert to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    # Convenience methods for different alert types
    def trade_alert(self, action: str, token: str, amount: float, price: float, tx_hash: str = None):
        """Alert for trade execution"""
        message = f"{action} {amount:.4f} SOL of {token[:8]}... at ${price:.6f}"
        data = {
            "action": action,
            "token": token,
            "amount": amount,
            "price": price,
            "tx_hash": tx_hash
        }
        
        level = AlertLevel.SUCCESS if action == "SELL" else AlertLevel.INFO
        self.send_alert(message, level, data)
    
    def profit_alert(self, token: str, pnl: float, percentage: float):
        """Alert for profitable trade"""
        message = f"Profit on {token[:8]}...: {pnl:+.4f} SOL ({percentage:+.1f}%)"
        data = {
            "token": token,
            "pnl": pnl,
            "percentage": percentage
        }
        
        level = AlertLevel.SUCCESS if pnl > 0 else AlertLevel.WARNING
        self.send_alert(message, level, data)
    
    def balance_alert(self, balance: float, daily_pnl: float):
        """Alert for balance updates"""
        message = f"Balance: {balance:.4f} SOL | Daily P&L: {daily_pnl:+.4f} SOL"
        data = {
            "balance": balance,
            "daily_pnl": daily_pnl
        }
        
        level = AlertLevel.WARNING if balance < 1.0 else AlertLevel.INFO
        self.send_alert(message, level, data)
    
    def error_alert(self, error: str, context: str = None):
        """Alert for errors"""
        message = f"Error in {context}: {error}" if context else f"Error: {error}"
        self.send_alert(message, AlertLevel.CRITICAL)
    
    def startup_alert(self, mode: str, balance: float):
        """Alert for bot startup"""
        message = f"Bot started in {mode} mode with {balance:.4f} SOL"
        self.send_alert(message, AlertLevel.INFO)
    
    def shutdown_alert(self, reason: str = "User requested"):
        """Alert for bot shutdown"""
        message = f"Bot shutting down: {reason}"
        self.send_alert(message, AlertLevel.WARNING)

# Singleton instance
_alert_manager = None

def get_alert_manager(config: Dict = None) -> AlertManager:
    """Get or create alert manager singleton"""
    global _alert_manager
    if _alert_manager is None and config is not None:
        _alert_manager = AlertManager(config)
    return _alert_manager
'''
    
    os.makedirs('core/alerts', exist_ok=True)
    with open('core/alerts/alert_manager.py', 'w', encoding='utf-8') as f:
        f.write(alert_code)
    
    # Create __init__.py
    with open('core/alerts/__init__.py', 'w', encoding='utf-8') as f:
        f.write('from .alert_manager import AlertManager, AlertLevel, get_alert_manager\n')
    
    print("✅ Created core/alerts/alert_manager.py")

def update_trading_bot_with_safety():
    """Create an updated trading_bot.py with safety features"""
    
    updated_bot = '''# trading_bot.py - WITH SAFETY FEATURES
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
'''
    
    # Save the updated bot
    with open('core/trading/trading_bot_safe.py', 'w', encoding='utf-8') as f:
        f.write(updated_bot)
    
    print("✅ Created core/trading/trading_bot_safe.py with safety features")
    print("   To use: Replace trading_bot.py with trading_bot_safe.py after review")

def main():
    """Run all safety fixes"""
    print("="*60)
    print("IMPLEMENTING SAFETY MEASURES AND ALERTS")
    print("="*60)
    
    # Update bot_control_real.json
    update_bot_control_real()
    print()
    
    # Create safety manager
    create_safety_module()
    print()
    
    # Create alert manager
    create_alert_module()
    print()
    
    # Create updated trading bot
    update_trading_bot_with_safety()
    print()
    
    print("="*60)
    print("✅ SAFETY IMPLEMENTATION COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Update 'real_wallet_address' in config/bot_control_real.json")
    print("2. Add Discord webhook URL or Telegram credentials for alerts")
    print("3. Review core/trading/trading_bot_safe.py")
    print("4. Replace trading_bot.py with trading_bot_safe.py when ready")
    print("\nTo start real trading with safety:")
    print("   python start_bot.py real --config config/bot_control_real.json")

if __name__ == "__main__":
    main()
