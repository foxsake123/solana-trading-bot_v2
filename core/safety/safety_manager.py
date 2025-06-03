#!/usr/bin/env python3
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
