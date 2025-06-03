#!/usr/bin/env python3
"""
Partial Profit Taking Strategy Implementation
Allows the bot to take partial profits at multiple levels while letting winners run
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PartialProfitStrategy:
    """
    Implements a sophisticated partial profit-taking strategy
    Takes profits in tranches while maintaining exposure to big winners
    """
    
    def __init__(self, config_path="config/partial_profit_config.json"):
        self.config = self.load_config(config_path)
        self.active_positions = {}  # Track partial exits per position
        
    def load_config(self, config_path):
        """Load partial profit configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "enabled": True,
                "profit_levels": [
                    {"target_pct": 30, "sell_pct": 25},   # At 30% profit, sell 25% of position
                    {"target_pct": 70, "sell_pct": 25},   # At 70% profit, sell another 25%
                    {"target_pct": 150, "sell_pct": 25},  # At 150% profit, sell another 25%
                    {"target_pct": 300, "sell_pct": 15},  # At 300% profit, sell 15%
                    # Keep 10% for moonshot potential
                ],
                "min_position_for_partial": 0.2,  # Minimum position size (SOL) to use partial exits
                "trailing_stop_after_partial": {
                    "enabled": True,
                    "activation_pct": 20,  # Activate trailing stop 20% from last exit
                    "distance_pct": 15     # Trail by 15%
                }
            }
    
    def save_config(self):
        """Save configuration to file"""
        with open("config/partial_profit_config.json", 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def should_take_partial_profit(self, position: Dict) -> Optional[Tuple[float, float]]:
        """
        Determine if partial profit should be taken for a position
        
        Args:
            position: Dict containing position info (amount, entry_price, current_price, contract_address)
            
        Returns:
            Tuple of (sell_percentage, reason) if partial profit should be taken, None otherwise
        """
        if not self.config.get("enabled", True):
            return None
        
        # Check if position is large enough for partial exits
        if position['amount'] < self.config.get("min_position_for_partial", 0.2):
            return None
        
        # Calculate current profit percentage
        entry_price = position['entry_price']
        current_price = position['current_price']
        profit_pct = ((current_price / entry_price) - 1) * 100
        
        # Get or create position tracking
        address = position['contract_address']
        if address not in self.active_positions:
            self.active_positions[address] = {
                'exits_taken': [],
                'remaining_pct': 100.0,
                'highest_price': current_price,
                'last_exit_price': entry_price
            }
        
        pos_info = self.active_positions[address]
        
        # Update highest price
        if current_price > pos_info['highest_price']:
            pos_info['highest_price'] = current_price
        
        # Check profit levels
        for level in self.config['profit_levels']:
            target_pct = level['target_pct']
            sell_pct = level['sell_pct']
            
            # Check if we've already taken this level
            if target_pct in pos_info['exits_taken']:
                continue
            
            # Check if current profit exceeds target
            if profit_pct >= target_pct:
                # Calculate actual amount to sell based on remaining position
                actual_sell_pct = (sell_pct / 100) * pos_info['remaining_pct']
                
                # Record the exit
                pos_info['exits_taken'].append(target_pct)
                pos_info['remaining_pct'] -= sell_pct
                pos_info['last_exit_price'] = current_price
                
                reason = f"Partial profit at {target_pct}% gain (selling {sell_pct}% of original position)"
                logger.info(f"📊 {reason} for {address[:8]}...")
                
                return (actual_sell_pct / 100, reason)
        
        # Check trailing stop after partial exits
        if (len(pos_info['exits_taken']) > 0 and 
            self.config.get('trailing_stop_after_partial', {}).get('enabled', True)):
            
            trailing_config = self.config['trailing_stop_after_partial']
            activation_pct = trailing_config['activation_pct']
            distance_pct = trailing_config['distance_pct']
            
            # Calculate profit from last exit
            profit_from_last_exit = ((current_price / pos_info['last_exit_price']) - 1) * 100
            
            # Check if we should activate trailing stop
            if profit_from_last_exit >= activation_pct:
                # Check if price has dropped from highest
                drop_from_highest = ((pos_info['highest_price'] - current_price) / pos_info['highest_price']) * 100
                
                if drop_from_highest >= distance_pct:
                    # Sell remaining position
                    sell_pct = pos_info['remaining_pct']
                    reason = f"Trailing stop hit after partial profits (dropped {drop_from_highest:.1f}% from peak)"
                    
                    # Clear position tracking
                    del self.active_positions[address]
                    
                    return (sell_pct / 100, reason)
        
        return None
    
    def calculate_position_size_for_partial(self, balance: float, ml_confidence: float = None) -> float:
        """
        Calculate position size considering partial profit strategy
        Larger positions are better suited for partial exits
        """
        # Base position size (can integrate with existing position calculator)
        base_pct = 4.0  # Default 4% of balance
        
        # Adjust for ML confidence if provided
        if ml_confidence is not None and ml_confidence > 0.7:
            # Higher confidence = larger position for partial profit potential
            base_pct = 5.0 + (ml_confidence - 0.7) * 10  # Up to 8% for very high confidence
        
        position_size = balance * (base_pct / 100)
        
        # Ensure minimum size for partial exits
        min_for_partial = self.config.get("min_position_for_partial", 0.2)
        if position_size < min_for_partial and balance > min_for_partial * 10:
            position_size = min_for_partial
        
        return round(position_size, 4)
    
    def get_position_status(self, address: str) -> Dict:
        """Get current status of a position's partial exits"""
        if address not in self.active_positions:
            return {
                'has_partial_exits': False,
                'remaining_pct': 100.0,
                'exits_taken': []
            }
        
        pos_info = self.active_positions[address]
        return {
            'has_partial_exits': len(pos_info['exits_taken']) > 0,
            'remaining_pct': pos_info['remaining_pct'],
            'exits_taken': pos_info['exits_taken'],
            'highest_price': pos_info.get('highest_price', 0),
            'last_exit_price': pos_info.get('last_exit_price', 0)
        }
    
    def optimize_profit_levels(self, historical_data: List[Dict]) -> Dict:
        """
        Analyze historical data to optimize profit levels
        
        Args:
            historical_data: List of trade dictionaries with 'max_profit_pct' field
            
        Returns:
            Optimized profit levels configuration
        """
        if not historical_data:
            return self.config
        
        # Extract maximum profit percentages
        max_profits = [trade['max_profit_pct'] for trade in historical_data 
                      if 'max_profit_pct' in trade and trade['max_profit_pct'] > 0]
        
        if not max_profits:
            return self.config
        
        # Calculate percentiles for profit levels
        import numpy as np
        
        p25 = np.percentile(max_profits, 25)
        p50 = np.percentile(max_profits, 50)
        p75 = np.percentile(max_profits, 75)
        p90 = np.percentile(max_profits, 90)
        p95 = np.percentile(max_profits, 95)
        
        # Generate optimized levels
        optimized_levels = []
        
        # First exit at 25th percentile (catch early profits)
        if p25 > 20:
            optimized_levels.append({
                "target_pct": int(p25),
                "sell_pct": 25
            })
        
        # Second exit at median
        if p50 > p25 + 20:
            optimized_levels.append({
                "target_pct": int(p50),
                "sell_pct": 25
            })
        
        # Third exit at 75th percentile
        if p75 > p50 + 30:
            optimized_levels.append({
                "target_pct": int(p75),
                "sell_pct": 25
            })
        
        # Fourth exit at 90th percentile
        if p90 > p75 + 50:
            optimized_levels.append({
                "target_pct": int(p90),
                "sell_pct": 20
            })
        
        # Keep some for extreme gains (95th percentile+)
        # Remaining 5-10% rides to the moon
        
        print(f"📊 Optimized Profit Levels based on {len(max_profits)} trades:")
        print(f"   P25: {p25:.0f}%, P50: {p50:.0f}%, P75: {p75:.0f}%, P90: {p90:.0f}%, P95: {p95:.0f}%")
        print(f"   Recommended levels: {optimized_levels}")
        
        return {
            **self.config,
            "profit_levels": optimized_levels
        }
    
    def simulate_strategy(self, historical_trades: List[Dict]) -> Dict:
        """
        Simulate partial profit strategy on historical trades
        Compare with current full-exit strategy
        """
        results = {
            'current_strategy_pnl': 0,
            'partial_strategy_pnl': 0,
            'trades_analyzed': 0,
            'improved_trades': 0,
            'capture_rate': []  # How much of max profit was captured
        }
        
        for trade in historical_trades:
            if 'entry_price' not in trade or 'exit_price' not in trade:
                continue
            
            results['trades_analyzed'] += 1
            
            # Current strategy P&L
            current_pnl = (trade['exit_price'] / trade['entry_price'] - 1) * trade['amount']
            results['current_strategy_pnl'] += current_pnl
            
            # Simulate partial exits
            if 'price_path' in trade:  # Would need intraday price data
                partial_pnl = self._simulate_partial_exits(trade)
                results['partial_strategy_pnl'] += partial_pnl
                
                if partial_pnl > current_pnl:
                    results['improved_trades'] += 1
            else:
                # Simple simulation without price path
                max_profit = trade.get('max_profit_pct', trade.get('percentage_change', 0))
                
                # Assume we could capture 70% of max profit with partial exits
                estimated_capture = 0.7 if max_profit > 100 else 0.85
                partial_pnl = current_pnl * estimated_capture * (max_profit / trade.get('percentage_change', 1))
                results['partial_strategy_pnl'] += partial_pnl
        
        # Calculate improvement
        if results['current_strategy_pnl'] > 0:
            improvement = ((results['partial_strategy_pnl'] / results['current_strategy_pnl']) - 1) * 100
            
            print(f"\n📊 Partial Profit Strategy Simulation Results:")
            print(f"   Trades analyzed: {results['trades_analyzed']}")
            print(f"   Current strategy P&L: {results['current_strategy_pnl']:.4f} SOL")
            print(f"   Partial strategy P&L: {results['partial_strategy_pnl']:.4f} SOL")
            print(f"   Improvement: {improvement:+.1f}%")
            
            if improvement > 10:
                print(f"   ✅ Partial profit strategy shows significant improvement!")
            else:
                print(f"   ℹ️  Partial profit strategy shows marginal improvement")
        
        return results


# Integration with main trading bot
def create_partial_profit_config():
    """Create default partial profit configuration file"""
    default_config = {
        "enabled": True,
        "profit_levels": [
            {"target_pct": 30, "sell_pct": 25},
            {"target_pct": 70, "sell_pct": 25},
            {"target_pct": 150, "sell_pct": 25},
            {"target_pct": 300, "sell_pct": 15}
        ],
        "min_position_for_partial": 0.2,
        "trailing_stop_after_partial": {
            "enabled": True,
            "activation_pct": 20,
            "distance_pct": 15
        }
    }
    
    with open("config/partial_profit_config.json", 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print("✅ Created config/partial_profit_config.json")
    print("📊 Default profit levels:")
    for level in default_config['profit_levels']:
        print(f"   At {level['target_pct']}% profit → Sell {level['sell_pct']}% of position")
    print("   Remaining 10% rides for maximum gains!")


def main():
    """Test partial profit strategy"""
    print("="*60)
    print("PARTIAL PROFIT TAKING STRATEGY")
    print("="*60)
    
    # Create config if it doesn't exist
    import os
    if not os.path.exists("config/partial_profit_config.json"):
        create_partial_profit_config()
    
    # Initialize strategy
    strategy = PartialProfitStrategy()
    
    # Test with example position
    test_position = {
        'contract_address': 'ABC123',
        'amount': 0.5,
        'entry_price': 0.001,
        'current_price': 0.0013  # 30% profit
    }
    
    result = strategy.should_take_partial_profit(test_position)
    if result:
        sell_pct, reason = result
        print(f"\n✅ Partial profit signal: Sell {sell_pct*100:.1f}% - {reason}")
    else:
        print("\n❌ No partial profit signal yet")
    
    print("\n📝 To integrate with your bot:")
    print("1. Import PartialProfitStrategy in trading_bot.py")
    print("2. Initialize in __init__: self.partial_profit = PartialProfitStrategy()")
    print("3. Check for partial exits in monitor_positions()")
    print("4. Implement partial sell orders in sell_token()")

if __name__ == "__main__":
    main()
