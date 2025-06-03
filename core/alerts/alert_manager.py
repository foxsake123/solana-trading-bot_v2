#!/usr/bin/env python3
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
            formatted_message += f"\n```json\n{json.dumps(data, indent=2)}\n```"
        
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
