# enhanced_trading_bot_v2.py
"""
Enhanced Trading Bot with Citadel-Barra, Partial Exits, and Twitter Sentiment
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from core.trading.trading_bot import TradingBot
from citadel_barra_strategy import CitadelBarraStrategy
from core.strategies.partial_exits import PartialExitManager
from core.analysis.twitter_sentiment import TwitterSentimentAnalyzer

logger = logging.getLogger(__name__)

class EnhancedTradingBotV2(TradingBot):
    """Enhanced bot with all features integrated"""
    
    def __init__(self, config, db, token_scanner, solana_trader):
        super().__init__(config, db, token_scanner, solana_trader)
        
        # Initialize strategies
        self.citadel_strategy = CitadelBarraStrategy(config, db)
        self.partial_exit_manager = PartialExitManager(config)
        self.sentiment_analyzer = TwitterSentimentAnalyzer(config)
        
        # Override min score to ensure trades execute
        self.trading_params['min_token_score'] = 0.5
        self.trading_params['min_ml_confidence'] = 0.5
        
        # Performance tracking
        self.feature_performance = {
            'citadel_signals': {'trades': 0, 'profitable': 0},
            'partial_exits': {'triggered': 0, 'total_profit': 0},
            'sentiment_boosts': {'used': 0, 'successful': 0}
        }
        
        logger.info("🚀 Enhanced Trading Bot V2 initialized with all features")
    
    async def analyze_and_trade_token(self, token: Dict):
        """Enhanced token analysis with all signals"""
        try:
            address = token.get('contract_address', token.get('address', ''))
            ticker = token.get('ticker', token.get('symbol', 'UNKNOWN'))
            
            # Skip if we already have a position
            if address in self.positions:
                return
            
            # 1. Citadel-Barra Analysis
            citadel_analysis = await self.citadel_strategy.analyze_token(token)
            combined_alpha = citadel_analysis.get('combined_alpha', 0)
            
            # 2. Twitter Sentiment Analysis
            sentiment_data = await self.sentiment_analyzer.analyze_token_sentiment(ticker, address)
            sentiment_boost = self.sentiment_analyzer.get_sentiment_boost(sentiment_data)
            
            # 3. Combine signals
            final_score = combined_alpha + sentiment_boost
            
            logger.info(f"📊 Analysis for {ticker}:")
            logger.info(f"   Citadel Alpha: {combined_alpha:.3f}")
            logger.info(f"   Sentiment: {sentiment_data.get('signal')} ({sentiment_boost:+.3f})")
            logger.info(f"   Final Score: {final_score:.3f}")
            
            # Make trading decision (lower threshold for execution)
            if final_score > 0.15:  # Lower threshold
                logger.info(f"✅ BUY SIGNAL for {ticker} (score: {final_score:.3f})")
                
                # Calculate position size
                position_size = self._calculate_enhanced_position_size(
                    final_score, 
                    citadel_analysis.get('factors', {}),
                    sentiment_data
                )
                
                # Check balance
                if self.balance >= position_size:
                    result = await self.buy_token(address, position_size)
                    
                    if result and result.get('success'):
                        # Store analysis data for exit decisions
                        self.positions[address]['citadel_data'] = citadel_analysis
                        self.positions[address]['entry_sentiment'] = sentiment_data
                        
                        if sentiment_boost > 0:
                            self.feature_performance['sentiment_boosts']['used'] += 1
                else:
                    logger.warning(f"Insufficient balance for {position_size:.4f} SOL position")
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
    
    def _calculate_enhanced_position_size(self, score: float, factors: Dict, sentiment: Dict) -> float:
        """Calculate position size with all factors considered"""
        
        # Base size (4-7% of balance)
        base_pct = 0.04 + (0.03 * min(score, 1.0))  # 4-7% based on score
        base_size = self.balance * base_pct
        
        # Apply Citadel risk adjustment
        volatility = factors.get('volatility', 1.0)
        risk_adj = 1.0 / (1.0 + volatility)  # Lower size for higher volatility
        
        # Sentiment adjustment
        sentiment_adj = 1.0
        if sentiment.get('signal') == 'BULLISH' and sentiment.get('volume_spike'):
            sentiment_adj = 1.2  # 20% boost for strong sentiment
        elif sentiment.get('signal') == 'BEARISH':
            sentiment_adj = 0.8  # 20% reduction for negative sentiment
        
        # Final size
        position_size = base_size * risk_adj * sentiment_adj
        
        # Apply limits
        min_size = max(0.4, self.balance * 0.04)  # At least 0.4 SOL or 4%
        max_size = self.balance * 0.07  # Max 7%
        
        position_size = max(min_size, min(position_size, max_size))
        
        logger.info(f"Position sizing: base={base_size:.3f}, risk_adj={risk_adj:.2f}, "
                   f"sentiment_adj={sentiment_adj:.2f}, final={position_size:.3f}")
        
        return position_size
    
    async def monitor_positions(self):
        """Enhanced position monitoring with partial exits"""
        for address, position in list(self.positions.items()):
            try:
                # Get current token data
                current_data = await self.token_scanner.get_token_data(address)
                if not current_data:
                    continue
                
                current_price = current_data.get('price_usd', 0)
                if current_price <= 0:
                    continue
                
                # Calculate P&L
                entry_price = position['entry_price']
                profit_pct = (current_price - entry_price) / entry_price
                
                # 1. Check partial exits
                exit_result = await self.partial_exit_manager.check_exits(position, current_price)
                
                if exit_result:
                    exit_amount, reason = exit_result
                    
                    # Execute partial sell
                    remaining_amount = position['amount'] - exit_amount
                    
                    if remaining_amount > 0:
                        # Partial exit
                        result = await self.sell_token(address, exit_amount, partial=True)
                        if result and result.get('success'):
                            position['amount'] = remaining_amount
                            self.feature_performance['partial_exits']['triggered'] += 1
                            self.feature_performance['partial_exits']['total_profit'] += exit_amount * profit_pct
                    else:
                        # Full exit
                        await self.sell_token(address, position['amount'])
                        self.partial_exit_manager.reset_position(address)
                    
                    continue
                
                # 2. Check Citadel exit conditions
                citadel_data = position.get('citadel_data', {})
                entry_factors = citadel_data.get('factors', {})
                
                should_exit, exit_reason = self.citadel_strategy.should_exit_position(
                    position, current_data, entry_factors
                )
                
                if should_exit:
                    logger.info(f"🚪 Citadel exit signal: {exit_reason}")
                    await self.sell_token(address, position['amount'])
                    self.partial_exit_manager.reset_position(address)
                    continue
                
                # 3. Regular stop loss/take profit
                if profit_pct <= -0.05:  # 5% stop loss
                    logger.info(f"🛑 Stop loss triggered for {position['ticker']}")
                    await self.sell_token(address, position['amount'])
                    self.partial_exit_manager.reset_position(address)
                
            except Exception as e:
                logger.error(f"Error monitoring position {address}: {e}")
    
    async def display_performance_summary(self):
        """Display enhanced performance metrics"""
        logger.info("\n" + "="*50)
        logger.info("📊 ENHANCED BOT PERFORMANCE SUMMARY")
        logger.info("="*50)
        
        # Basic metrics
        total_trades = len(self.completed_trades)
        profitable_trades = sum(1 for t in self.completed_trades if t.get('profit', 0) > 0)
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Win Rate: {win_rate:.1f}%")
        logger.info(f"Current Balance: {self.balance:.4f} SOL")
        
        # Feature performance
        logger.info("\n📈 FEATURE PERFORMANCE:")
        
        # Citadel
        citadel_trades = self.feature_performance['citadel_signals']['trades']
        if citadel_trades > 0:
            citadel_win_rate = self.feature_performance['citadel_signals']['profitable'] / citadel_trades * 100
            logger.info(f"Citadel Strategy: {citadel_trades} trades, {citadel_win_rate:.1f}% win rate")
        
        # Partial Exits
        partial_exits = self.feature_performance['partial_exits']['triggered']
        if partial_exits > 0:
            avg_exit_profit = self.feature_performance['partial_exits']['total_profit'] / partial_exits
            logger.info(f"Partial Exits: {partial_exits} triggered, {avg_exit_profit:.2%} avg profit")
        
        # Sentiment
        sentiment_uses = self.feature_performance['sentiment_boosts']['used']
        if sentiment_uses > 0:
            sentiment_success = self.feature_performance['sentiment_boosts']['successful'] / sentiment_uses * 100
            logger.info(f"Sentiment Boosts: {sentiment_uses} used, {sentiment_success:.1f}% successful")
        
        # Exit statistics
        exit_stats = self.partial_exit_manager.get_stats()
        logger.info(f"\n🎯 EXIT LEVELS REACHED:")
        logger.info(f"20% profit: {exit_stats['positions_at_20%']} positions")
        logger.info(f"50% profit: {exit_stats['positions_at_50%']} positions")
        logger.info(f"100% profit: {exit_stats['positions_at_100%']} positions")
        logger.info(f"200% profit: {exit_stats['positions_at_200%']} positions")
        logger.info(f"Active moonbags: {exit_stats['active_moonbags']}")
        
        logger.info("="*50)