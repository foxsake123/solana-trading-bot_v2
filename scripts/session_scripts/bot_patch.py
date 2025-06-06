#!/usr/bin/env python3
"""
Patch to add missing methods to trading_bot.py
"""

def add_missing_methods():
    """Add the missing methods to trading_bot.py"""
    
    missing_methods = '''
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
'''
    
    # Read current trading_bot.py
    with open('core/trading/trading_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find where to insert the methods (before the stop method)
    insert_point = content.find('    async def stop(self):')
    
    if insert_point == -1:
        print("❌ Could not find insertion point")
        return False
    
    # Insert the missing methods
    new_content = content[:insert_point] + missing_methods + '\n' + content[insert_point:]
    
    # Write back
    with open('core/trading/trading_bot.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Added missing methods to trading_bot.py")
    return True

if __name__ == "__main__":
    print("TRADING BOT METHOD PATCH")
    print("=" * 50)
    
    if add_missing_methods():
        print("\n✅ Patch applied successfully!")
        print("\nNow run: python start_bot.py simulation")
    else:
        print("\n❌ Patch failed!")
