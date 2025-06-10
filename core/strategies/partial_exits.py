# core/strategies/partial_exits.py
"""
Partial Exit Strategy Manager for Solana Trading Bot
Implements multi-level profit taking with moonbag retention
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class PartialExitManager:
    """Manages partial exits at multiple profit levels"""
    
    def __init__(self, config: Dict, db, solana_trader):
        self.config = config['partial_exits']
        self.db = db
        self.solana_trader = solana_trader
        
        # Exit levels from config
        self.exit_levels = self.config['levels']
        self.trailing_stop = self.config['trailing_stop']
        
        # Track executed exits per position
        self.executed_exits = {}  # {position_id: [executed_levels]}
        self.trailing_stops = {}  # {position_id: {'activated': bool, 'highest_price': float}}
        
        # Performance tracking
        self.exit_performance = {
            'partial_exits_executed': 0,
            'total_profit_captured': 0,
            'moonbags_active': 0
        }
        
    async def check_and_execute_exits(self, position: Dict, current_price: float) -> Dict:
        """
        Check if position qualifies for partial exits
        Returns dict with exit details
        """
        
        position_id = f"{position['contract_address']}_{position['buy_timestamp']}"
        
        # Initialize tracking if needed
        if position_id not in self.executed_exits:
            self.executed_exits[position_id] = []
            self.trailing_stops[position_id] = {
                'activated': False,
                'highest_price': current_price,
                'stop_price': 0
            }
        
        # Calculate current profit percentage
        entry_price = position['price']
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        logger.debug(f"Position {position['symbol']} at {profit_pct:.1f}% profit")
        
        # Check each exit level
        exits_executed = []
        
        for i, level in enumerate(self.exit_levels):
            level_id = f"level_{i}_{level['profit_pct']}"
            
            # Skip if already executed
            if level_id in self.executed_exits[position_id]:
                continue
            
            # Check if profit target hit
            if profit_pct >= level['profit_pct'] * 100:
                logger.info(f"🎯 Profit target {level['profit_pct']*100}% hit for {position['symbol']}")
                
                # Calculate exit amount
                remaining_amount = await self._get_remaining_position(position)
                exit_amount = remaining_amount * level['exit_pct']
                
                # Execute partial exit
                exit_result = await self._execute_partial_sell(
                    position,
                    exit_amount,
                    current_price,
                    f"Partial exit at {level['profit_pct']*100}% profit"
                )
                
                if exit_result['success']:
                    self.executed_exits[position_id].append(level_id)
                    exits_executed.append({
                        'level': level['profit_pct'],
                        'amount': exit_amount,
                        'price': current_price,
                        'profit_sol': exit_result['profit_sol']
                    })
                    
                    # Update performance metrics
                    self.exit_performance['partial_exits_executed'] += 1
                    self.exit_performance['total_profit_captured'] += exit_result['profit_sol']
        
        # Check trailing stop activation
        if self.trailing_stop['enabled']:
            await self._manage_trailing_stop(position, position_id, current_price, profit_pct)
        
        # Check if position is now a moonbag
        remaining_pct = await self._calculate_remaining_percentage(position)
        is_moonbag = remaining_pct <= 0.3  # 30% or less remaining
        
        return {
            'exits_executed': exits_executed,
            'remaining_percentage': remaining_pct,
            'is_moonbag': is_moonbag,
            'profit_pct': profit_pct,
            'trailing_stop_active': self.trailing_stops[position_id]['activated']
        }
    
    async def _execute_partial_sell(self, position: Dict, amount: float, 
                                   current_price: float, reason: str) -> Dict:
        """Execute a partial sell order"""
        
        try:
            logger.info(f"Executing partial sell: {amount:.4f} {position['symbol']} at ${current_price:.6f}")
            
            # Execute sell through Solana trader
            result = await self.solana_trader.sell_token(
                contract_address=position['contract_address'],
                amount=amount,
                min_sol_output=amount * current_price * 0.95  # 5% slippage tolerance
            )
            
            if result['success']:
                # Calculate profit
                entry_value = amount * position['price']
                exit_value = result['sol_received']
                profit_sol = exit_value - entry_value
                
                # Record partial exit in database
                await self._record_partial_exit(
                    position, amount, current_price, 
                    profit_sol, reason
                )
                
                logger.info(f"✅ Partial exit successful: {profit_sol:.4f} SOL profit")
                
                return {
                    'success': True,
                    'amount_sold': amount,
                    'sol_received': exit_value,
                    'profit_sol': profit_sol,
                    'tx_signature': result['signature']
                }
            else:
                logger.error(f"Partial sell failed: {result.get('error', 'Unknown error')}")
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"Error executing partial sell: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _manage_trailing_stop(self, position: Dict, position_id: str, 
                                   current_price: float, profit_pct: float):
        """Manage trailing stop for moonbag positions"""
        
        trailing_data = self.trailing_stops[position_id]
        
        # Check if trailing stop should be activated
        if not trailing_data['activated'] and profit_pct >= self.trailing_stop['activation'] * 100:
            trailing_data['activated'] = True
            trailing_data['highest_price'] = current_price
            trailing_data['stop_price'] = current_price * (1 - self.trailing_stop['distance'])
            
            logger.info(f"🔒 Trailing stop activated for {position['symbol']} at {profit_pct:.1f}% profit")
            logger.info(f"   Stop price: ${trailing_data['stop_price']:.6f}")
        
        # Update trailing stop if active
        elif trailing_data['activated']:
            # Update highest price and stop if price increased
            if current_price > trailing_data['highest_price']:
                trailing_data['highest_price'] = current_price
                trailing_data['stop_price'] = current_price * (1 - self.trailing_stop['distance'])
                
                logger.debug(f"Trailing stop updated for {position['symbol']}: ${trailing_data['stop_price']:.6f}")
            
            # Check if stop hit
            elif current_price <= trailing_data['stop_price']:
                logger.warning(f"⚠️ Trailing stop hit for {position['symbol']} at ${current_price:.6f}")
                
                # Execute remaining position sell
                remaining_amount = await self._get_remaining_position(position)
                
                exit_result = await self._execute_partial_sell(
                    position,
                    remaining_amount,
                    current_price,
                    f"Trailing stop hit at {profit_pct:.1f}% profit"
                )
                
                if exit_result['success']:
                    # Mark position as fully exited
                    self.executed_exits[position_id].append('trailing_stop')
    
    async def _get_remaining_position(self, position: Dict) -> float:
        """Get remaining position amount after partial exits"""
        
        # Query database for partial exits
        query = """
        SELECT SUM(amount) as sold_amount
        FROM partial_exits
        WHERE contract_address = ? AND buy_timestamp = ?
        """
        
        result = self.db.execute_query(
            query, 
            (position['contract_address'], position['buy_timestamp'])
        )
        
        sold_amount = result[0]['sold_amount'] or 0
        remaining = position['amount'] - sold_amount
        
        return max(remaining, 0)
    
    async def _calculate_remaining_percentage(self, position: Dict) -> float:
        """Calculate percentage of position remaining"""
        
        remaining = await self._get_remaining_position(position)
        return (remaining / position['amount']) * 100
    
    async def _record_partial_exit(self, position: Dict, amount: float, 
                                  price: float, profit_sol: float, reason: str):
        """Record partial exit in database"""
        
        query = """
        INSERT INTO partial_exits (
            contract_address, symbol, buy_timestamp, 
            amount, price, profit_sol, reason, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute_query(query, (
            position['contract_address'],
            position['symbol'],
            position['buy_timestamp'],
            amount,
            price,
            profit_sol,
            reason,
            datetime.now()
        ))
    
    def get_exit_statistics(self) -> Dict:
        """Get partial exit performance statistics"""
        
        # Query database for comprehensive stats
        stats_query = """
        SELECT 
            COUNT(*) as total_exits,
            SUM(profit_sol) as total_profit,
            AVG(profit_sol) as avg_profit,
            COUNT(DISTINCT contract_address) as unique_tokens
        FROM partial_exits
        WHERE timestamp > datetime('now', '-7 days')
        """
        
        stats = self.db.execute_query(stats_query)[0]
        
        return {
            'weekly_stats': {
                'total_exits': stats['total_exits'] or 0,
                'total_profit': stats['total_profit'] or 0,
                'avg_profit_per_exit': stats['avg_profit'] or 0,
                'unique_tokens': stats['unique_tokens'] or 0
            },
            'session_stats': self.exit_performance,
            'active_moonbags': len([
                p for p in self.trailing_stops.values() 
                if p['activated']
            ])
        }
    
    async def optimize_exit_levels(self) -> Dict:
        """Analyze and optimize exit levels based on historical performance"""
        
        # Query historical exit performance
        analysis_query = """
        SELECT 
            reason,
            AVG(profit_sol) as avg_profit,
            COUNT(*) as exit_count,
            SUM(profit_sol) as total_profit
        FROM partial_exits
        WHERE timestamp > datetime('now', '-30 days')
        GROUP BY reason
        ORDER BY avg_profit DESC
        """
        
        results = self.db.execute_query(analysis_query)
        
        # Analyze which exit levels perform best
        recommendations = []
        
        for result in results:
            if '50%' in result['reason'] and result['avg_profit'] > 0.1:
                recommendations.append("Consider lowering first exit to 40% for faster profit capture")
            elif '200%' in result['reason'] and result['exit_count'] < 10:
                recommendations.append("200% exit rarely hit - consider 150% level")
        
        return {
            'performance_by_level': results,
            'recommendations': recommendations,
            'optimal_levels': self._calculate_optimal_levels(results)
        }
    
    def _calculate_optimal_levels(self, historical_data: List[Dict]) -> List[Dict]:
        """Calculate optimal exit levels based on historical data"""
        
        # This is a simplified optimization
        # In production, use more sophisticated analysis
        
        return [
            {'profit_pct': 0.4, 'exit_pct': 0.3},   # 40% profit: exit 30%
            {'profit_pct': 0.8, 'exit_pct': 0.3},   # 80% profit: exit 30%
            {'profit_pct': 1.5, 'exit_pct': 0.3},   # 150% profit: exit 30%
            # Keep 10% as permanent moonbag
        ]
