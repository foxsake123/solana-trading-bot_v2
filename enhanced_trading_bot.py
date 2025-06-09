# enhanced_trading_bot.py
"""
Enhanced trading bot integrating Citadel-Barra strategy with existing infrastructure
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from citadel_barra_strategy import CitadelBarraStrategy, BarraFactors

logger = logging.getLogger('enhanced_trading_bot')

class EnhancedTradingBot:
    """
    Enhanced version of the trading bot with Citadel-inspired multi-factor strategy
    """
    
    def __init__(self, config: Dict, db, token_scanner, trader):
        self.config = config
        self.db = db
        self.token_scanner = token_scanner
        self.trader = trader
        
        # Initialize Citadel-Barra strategy
        self.strategy = CitadelBarraStrategy(
            db=db,
            config=config,
            birdeye_api=token_scanner.birdeye_api
        )
        
        # Enhanced position tracking
        self.positions = {}
        self.factor_exposures = {}
        self.alpha_decay_tracker = {}
        
        # Performance tracking
        self.performance_metrics = {
            'sharpe_ratio': 0,
            'information_ratio': 0,
            'max_drawdown': 0,
            'factor_attribution': {}
        }
        
        # Risk limits from config
        self.max_portfolio_risk = config.get('max_portfolio_risk_pct', 30.0) / 100
        self.max_positions = config.get('max_open_positions', 10)
        
        self.running = False
        self.simulation_mode = config.get('simulation_mode', True)
        
        logger.info(f"Enhanced Trading Bot initialized in {'SIMULATION' if self.simulation_mode else 'REAL'} mode")
    
    async def start(self):
        """Start the enhanced trading bot"""
        logger.info("="*50)
        logger.info("   Enhanced Citadel-Barra Trading Bot Starting")
        logger.info("="*50)
        
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self.token_scanner.start_scanning())
        asyncio.create_task(self._risk_monitoring_loop())
        asyncio.create_task(self._alpha_decay_loop())
        
        # Main trading loop
        await self.trading_loop()
    
    async def trading_loop(self):
        """Main trading loop with multi-factor analysis"""
        scan_interval = self.config.get('scan_interval', 60)
        
        while self.running:
            try:
                # Update portfolio metrics
                await self._update_portfolio_metrics()
                
                # Get current positions and calculate portfolio risk
                portfolio_risk = self._calculate_portfolio_risk()
                
                # Log portfolio status
                balance_sol, balance_usd = await self.trader.get_wallet_balance()
                logger.info(f"Balance: {balance_sol:.4f} SOL | Portfolio Risk: {portfolio_risk:.1%}")
                
                # Find and analyze tokens
                if portfolio_risk < self.max_portfolio_risk:
                    await self._scan_and_trade()
                else:
                    logger.warning(f"Portfolio risk limit reached: {portfolio_risk:.1%}")
                
                # Monitor existing positions
                await self._monitor_positions()
                
                # Rebalance if needed
                await self._rebalance_portfolio()
                
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)
    
    async def _scan_and_trade(self):
        """Scan for opportunities using multi-factor analysis"""
        try:
            # Get candidate tokens
            top_gainers = await self.token_scanner.get_top_gainers()
            trending = await self.token_scanner.get_trending_tokens()
            
            # Combine and deduplicate
            candidates = self._combine_token_lists(top_gainers, trending)
            
            logger.info(f"Analyzing {len(candidates)} tokens with Citadel-Barra strategy")
            
            # Score and rank opportunities
            opportunities = []
            
            for token in candidates:
                try:
                    # Skip if already have position
                    if token.get('contract_address') in self.positions:
                        continue
                    
                    # Calculate Barra factors
                    factors = await self.strategy.calculate_barra_factors(token)
                    
                    # Generate alpha signals
                    alpha_signals = self.strategy.generate_alpha_signals(token, factors)
                    
                    # Add ML prediction if available
                    if self.token_scanner.token_analyzer:
                        ml_analysis = await self.token_scanner.token_analyzer.analyze_token(
                            token['contract_address']
                        )
                        alpha_signals['ml_prediction'] = ml_analysis.get('confidence', 0.5)
                    
                    # Calculate expected alpha
                    expected_alpha = self.strategy._combine_alpha_signals(alpha_signals)
                    
                    # Risk-adjusted score
                    risk_adj_score = expected_alpha / (1 + factors.idiosyncratic_risk)
                    
                    opportunities.append({
                        'token': token,
                        'factors': factors,
                        'alpha_signals': alpha_signals,
                        'expected_alpha': expected_alpha,
                        'risk_adj_score': risk_adj_score
                    })
                    
                except Exception as e:
                    logger.error(f"Error analyzing token {token.get('symbol')}: {e}")
                    continue
            
            # Sort by risk-adjusted score
            opportunities.sort(key=lambda x: x['risk_adj_score'], reverse=True)
            
            # Execute top opportunities
            for opp in opportunities[:3]:  # Top 3 opportunities
                if len(self.positions) >= self.max_positions:
                    break
                
                await self._execute_trade(opp)
                
        except Exception as e:
            logger.error(f"Error in scan and trade: {e}")
    
    async def _execute_trade(self, opportunity: Dict):
        """Execute trade with sophisticated position sizing"""
        token = opportunity['token']
        factors = opportunity['factors']
        alpha_signals = opportunity['alpha_signals']
        
        try:
            # Calculate position size
            position_size_pct = self.strategy.calculate_position_size(
                token_data=token,
                factors=factors,
                alpha_signals=alpha_signals,
                current_portfolio=self.positions
            )
            
            # Get current balance
            balance_sol, _ = await self.trader.get_wallet_balance()
            
            # Calculate SOL amount
            amount_sol = balance_sol * position_size_pct
            # SAFETY CHECK: Ensure position size is reasonable
            max_position = min(balance_sol * 0.08, 0.8)  # Max 8% of balance or 0.8 SOL
            if amount_sol > max_position:
                logger.warning(f"Position size {amount_sol:.4f} exceeds safe maximum {max_position:.4f}")
                amount_sol = max_position
            
            
            # Apply minimum position size (important for your profits!)
            min_position_sol = self.config.get('absolute_min_sol', 0.3)
            
            # FORCE MINIMUM POSITION SIZE - CRITICAL FIX
            if amount_sol < min_position_sol:
                logger.warning(f"Position size {amount_sol:.4f} below minimum {min_position_sol:.4f}, forcing to minimum")
                amount_sol = min_position_sol
            
            # Also ensure we respect the absolute minimum from config
            amount_sol = max(amount_sol, 0.4)  # Force 0.4 SOL minimum
            
            logger.info(f"Final position size: {amount_sol:.4f} SOL (min: {min_position_sol:.4f})")
            
            # Check if we have enough balance
            if amount_sol > balance_sol * 0.95:  # Keep 5% reserve
                logger.warning(f"Insufficient balance for {token['symbol']}")
                return
            
            # Log the decision
            logger.info(f"🎯 Executing trade for {token['symbol']}:")
            logger.info(f"   Expected Alpha: {opportunity['expected_alpha']:.2f}")
            logger.info(f"   Risk-Adj Score: {opportunity['risk_adj_score']:.2f}")
            logger.info(f"   Position Size: {amount_sol:.4f} SOL ({position_size_pct*100:.1f}%)")
            logger.info(f"   Key Factors: Beta={factors.market_beta:.2f}, Vol={factors.volatility:.2f}")
            
            # Execute the trade
            tx_hash = await self.trader.buy_token(token['contract_address'], amount_sol)
            
            if tx_hash:
                # Track position with enhanced metadata
                self.positions[token['contract_address']] = {
                    'token': token,
                    'amount_sol': amount_sol,
                    'entry_time': datetime.now(timezone.utc),
                    'entry_price': token.get('price_usd', 0),
                    'factors': factors,
                    'alpha_signals': alpha_signals,
                    'expected_alpha': opportunity['expected_alpha'],
                    'tx_hash': tx_hash
                }
                
                # Track factor exposures
                self._update_factor_exposures()
                
                # Initialize alpha decay tracking
                self.alpha_decay_tracker[token['contract_address']] = {
                    'initial_alpha': opportunity['expected_alpha'],
                    'current_alpha': opportunity['expected_alpha'],
                    'entry_time': datetime.now(timezone.utc)
                }
                
                logger.info(f"✅ Position opened: {token['symbol']} - {amount_sol:.4f} SOL")
                
        except Exception as e:
            logger.error(f"Error executing trade for {token['symbol']}: {e}")
    
    async def _monitor_positions(self):
        """Monitor positions with dynamic exit strategies"""
        for address, position in list(self.positions.items()):
            try:
                # Get current token data
                current_data = await self.token_scanner.birdeye_api.get_token_info(address)
                
                if not current_data:
                    continue
                
                # Calculate current P&L
                entry_price = position['entry_price']
                current_price = current_data.get('price_usd', 0)
                
                if entry_price > 0 and current_price > 0:
                    pnl_pct = ((current_price / entry_price) - 1) * 100
                    
                    # Get current alpha (with decay)
                    current_alpha = self.alpha_decay_tracker.get(address, {}).get('current_alpha', 0)
                    
                    # Dynamic exit conditions
                    should_exit, exit_reason = self._check_exit_conditions(
                        position=position,
                        current_data=current_data,
                        pnl_pct=pnl_pct,
                        current_alpha=current_alpha
                    )
                    
                    if should_exit:
                        logger.info(f"📤 Exit signal for {position['token']['symbol']}: {exit_reason}")
                        logger.info(f"   P&L: {pnl_pct:+.1f}%")
                        
                        # Calculate exit amount (could be partial)
                        exit_amount = self._calculate_exit_amount(position, exit_reason)
                        
                        # Execute sell
                        await self.trader.sell_token(address, exit_amount)
                        
                        # Update or remove position
                        if exit_amount >= position['amount_sol'] * 0.95:
                            del self.positions[address]
                            del self.alpha_decay_tracker[address]
                        else:
                            position['amount_sol'] -= exit_amount
                
            except Exception as e:
                logger.error(f"Error monitoring position {address}: {e}")
    
    def _check_exit_conditions(self, position: Dict, current_data: Dict, 
                             pnl_pct: float, current_alpha: float) -> Tuple[bool, str]:
        """Sophisticated exit logic based on multiple factors"""
        
        # 1. Stop loss
        stop_loss = self.config.get('stop_loss_pct', 5.0)
        if pnl_pct <= -stop_loss:
            return True, f"Stop loss ({pnl_pct:.1f}%)"
        
        # 2. Take profit with alpha consideration
        base_take_profit = self.config.get('take_profit_pct', 50.0)
        
        # Adjust take profit based on remaining alpha
        alpha_adjustment = max(0.5, current_alpha + 1)  # Scale from 0.5x to 1.5x
        adjusted_take_profit = base_take_profit * alpha_adjustment
        
        if pnl_pct >= adjusted_take_profit:
            return True, f"Take profit ({pnl_pct:.1f}%)"
        
        # 3. Alpha exhaustion (signal has decayed)
        if current_alpha < -0.2:  # Negative alpha
            return True, "Alpha exhausted"
        
        # 4. Risk increase
        current_volatility = self._estimate_current_volatility(current_data)
        entry_volatility = position['factors'].volatility
        
        if current_volatility > entry_volatility * 2:
            return True, "Risk increased significantly"
        
        # 5. Better opportunity available (opportunity cost)
        if hasattr(self, 'better_opportunity_available'):
            if self.better_opportunity_available and pnl_pct > 10:
                return True, "Better opportunity available"
        
        # 6. Time-based exit for mean reversion trades
        if position['alpha_signals'].get('mean_reversion', 0) > 0.5:
            hours_held = (datetime.now(timezone.utc) - position['entry_time']).total_seconds() / 3600
            if hours_held > 24 and pnl_pct > 5:
                return True, "Mean reversion time limit"
        
        return False, ""
    
    def _calculate_exit_amount(self, position: Dict, exit_reason: str) -> float:
        """Calculate how much to sell (supports partial exits)"""
        
        # For now, exit full position
        # Could implement partial exits based on:
        # - Scaling out at different profit levels
        # - Keeping a "moon bag" for huge gainers
        # - Risk-based partial exits
        
        return position['amount_sol']
    
    async def _rebalance_portfolio(self):
        """Rebalance portfolio based on factor exposures"""
        if len(self.positions) < 3:
            return
            
        # Calculate current factor exposures
        factor_exposures = self._calculate_factor_exposures()
        
        # Check if rebalancing needed
        needs_rebalance = False
        
        for factor, exposure in factor_exposures.items():
            if abs(exposure) > self.strategy.max_factor_exposure:
                needs_rebalance = True
                logger.warning(f"Factor {factor} overexposed: {exposure:.2f}")
        
        if needs_rebalance:
            # Identify positions to trim
            # This is simplified - in production, use optimization
            logger.info("Portfolio rebalancing needed - factor limits exceeded")
    
    def _calculate_portfolio_risk(self) -> float:
        """Calculate current portfolio risk"""
        if not self.positions:
            return 0.0
            
        # Get position values
        position_list = []
        for address, pos in self.positions.items():
            position_list.append({
                'value': pos['amount_sol'],
                'factors': pos['factors'].__dict__,
                'variance': pos['factors'].idiosyncratic_risk ** 2
            })
        
        # Use strategy's risk decomposition
        risk_decomp = self.strategy.calculate_portfolio_risk_decomposition(position_list)
        
        return risk_decomp['total_risk']
    
    def _calculate_factor_exposures(self) -> Dict[str, float]:
        """Calculate portfolio-level factor exposures"""
        if not self.positions:
            return {}
            
        total_value = sum(p['amount_sol'] for p in self.positions.values())
        
        exposures = {}
        factor_names = ['market_beta', 'sol_beta', 'momentum', 'volatility']
        
        for factor in factor_names:
            weighted_exposure = sum(
                getattr(p['factors'], factor, 0) * p['amount_sol'] / total_value
                for p in self.positions.values()
            )
            exposures[factor] = weighted_exposure
            
        return exposures
    
    def _update_factor_exposures(self):
        """Update cached factor exposures"""
        self.factor_exposures = self._calculate_factor_exposures()
    
    async def _alpha_decay_loop(self):
        """Background task to decay alpha signals over time"""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                
                for address, tracker in self.alpha_decay_tracker.items():
                    # Calculate hours since entry
                    hours_elapsed = (current_time - tracker['entry_time']).total_seconds() / 3600
                    
                    # Exponential decay with half-life
                    decay_factor = 0.5 ** (hours_elapsed / self.strategy.alpha_decay_halflife)
                    
                    # Update current alpha
                    tracker['current_alpha'] = tracker['initial_alpha'] * decay_factor
                
                await asyncio.sleep(3600)  # Update hourly
                
            except Exception as e:
                logger.error(f"Error in alpha decay loop: {e}")
                await asyncio.sleep(3600)
    
    async def _risk_monitoring_loop(self):
        """Background task for continuous risk monitoring"""
        while self.running:
            try:
                # Monitor portfolio risk
                portfolio_risk = self._calculate_portfolio_risk()
                
                if portfolio_risk > self.max_portfolio_risk * 0.9:
                    logger.warning(f"⚠️  Approaching risk limit: {portfolio_risk:.1%}")
                
                # Monitor factor exposures
                exposures = self._calculate_factor_exposures()
                for factor, exposure in exposures.items():
                    if abs(exposure) > self.strategy.max_factor_exposure * 0.8:
                        logger.warning(f"⚠️  High {factor} exposure: {exposure:.2f}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _update_portfolio_metrics(self):
        """Update performance metrics"""
        try:
            # This would calculate Sharpe ratio, Information ratio, etc.
            # Simplified for now
            pass
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def _combine_token_lists(self, *lists) -> List[Dict]:
        """Combine and deduplicate token lists"""
        seen = set()
        combined = []
        
        for token_list in lists:
            for token in token_list:
                address = token.get('contract_address', token.get('address', ''))
                if address and address not in seen:
                    seen.add(address)
                    combined.append(token)
                    
        return combined
    
    def _estimate_current_volatility(self, token_data: Dict) -> float:
        """Estimate current volatility from recent price action"""
        # Simplified estimation
        return abs(token_data.get('price_change_1h', 0)) / 100 * np.sqrt(24)
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping enhanced trading bot...")
        self.running = False