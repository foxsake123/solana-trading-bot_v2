#!/usr/bin/env python3
"""
Force the bot to use larger position sizes by patching the trading logic
"""
import os
import re

def find_position_size_logic():
    """Find where position sizes are calculated in the code"""
    print("🔍 Searching for position size logic...")
    
    files_to_check = [
        "core/trading/trading_bot.py",
        "core/trading/position_manager.py",
        "trading_bot.py",
        "core/trading/risk_manager.py"
    ]
    
    found_files = []
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for position size calculations
            if any(pattern in content for pattern in [
                "position_size", "amount =", "investment", "0.1", "0.01", 
                "max_investment_per_token", "calculate_position"
            ]):
                found_files.append(filepath)
                print(f"✅ Found position logic in: {filepath}")
                
                # Show relevant lines
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'amount' in line and '=' in line and any(x in line for x in ['0.0', '0.1', 'min(']):
                        print(f"   Line {i+1}: {line.strip()}")
    
    return found_files

def patch_trading_bot():
    """Patch the trading bot to use larger positions"""
    
    trading_bot_path = None
    
    # Find the actual trading bot file
    possible_paths = [
        "core/trading/trading_bot.py",
        "trading_bot.py",
        "core/trading/real_trading_bot.py"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            trading_bot_path = path
            break
    
    if not trading_bot_path:
        print("❌ Could not find trading_bot.py")
        return False
    
    print(f"\n📝 Patching {trading_bot_path}...")
    
    with open(trading_bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_path = f"{trading_bot_path}.backup_positions"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backed up to {backup_path}")
    
    # Common patterns to replace
    replacements = [
        # Replace hardcoded small amounts
        (r'amount = 0\.1\b', 'amount = 0.4'),
        (r'amount = 0\.01\b', 'amount = 0.4'),
        (r'amount = 0\.05\b', 'amount = 0.4'),
        
        # Replace min calculations that might limit size
        (r'min\(0\.1,', 'min(0.5,'),
        (r'min\(max_investment, self\.balance \* 0\.1\)', 'min(max_investment, self.balance * 0.4)'),
        
        # Replace percentage calculations
        (r'self\.balance \* 0\.01', 'self.balance * 0.04'),
        (r'self\.balance \* 0\.1', 'self.balance * 0.4'),
        
        # Look for specific amount calculations
        (r'amount = min\(max_investment, self\.balance \* [0-9.]+\)', 
         'amount = min(max_investment, max(0.3, self.balance * 0.04))'),
    ]
    
    modified = False
    for pattern, replacement in replacements:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"✅ Replaced: {pattern} -> {replacement}")
    
    # Add a minimum position size enforcer
    if 'buy_token' in content and 'amount' in content:
        # Find the buy_token method and add minimum enforcement
        enforcer_code = '''
        # FORCE MINIMUM POSITION SIZE
        if amount < 0.3:
            logger.info(f"Increasing position size from {amount} to 0.3 SOL (minimum)")
            amount = 0.3
        '''
        
        # Try to insert after amount calculation
        if 'async def buy_token' in content:
            # Find where amount is used in buy_token
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'await self.trader.buy_token' in line and i > 0:
                    # Insert before the actual buy
                    indent = len(line) - len(line.lstrip())
                    enforcer_lines = enforcer_code.strip().split('\n')
                    enforcer_indented = '\n'.join(' ' * indent + line for line in enforcer_lines)
                    lines.insert(i, enforcer_indented)
                    content = '\n'.join(lines)
                    modified = True
                    print("✅ Added minimum position size enforcer")
                    break
    
    if modified:
        with open(trading_bot_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Patched {trading_bot_path}")
        return True
    else:
        print("⚠️  No direct position size calculations found to patch")
        return False

def create_position_override():
    """Create a position size override module"""
    override_code = '''#!/usr/bin/env python3
"""
Position size override - ensures minimum position sizes
"""
import logging

logger = logging.getLogger(__name__)

class PositionSizer:
    """Force larger position sizes"""
    
    MIN_POSITION = 0.3  # Minimum 0.3 SOL
    MAX_POSITION = 0.5  # Maximum 0.5 SOL
    DEFAULT_POSITION = 0.4  # Default 0.4 SOL
    
    @classmethod
    def calculate_position_size(cls, balance: float, config: dict = None) -> float:
        """Calculate position size with enforced minimums"""
        
        # Get configured max from config
        if config:
            max_investment = config.get('max_investment_per_token', cls.MAX_POSITION)
        else:
            max_investment = cls.MAX_POSITION
        
        # Calculate 4% of balance
        percentage_size = balance * 0.04
        
        # Use the larger of percentage or minimum
        position_size = max(cls.MIN_POSITION, percentage_size)
        
        # Cap at maximum
        position_size = min(position_size, max_investment, cls.MAX_POSITION)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"(balance: {balance:.4f}, min: {cls.MIN_POSITION}, max: {max_investment})")
        
        return position_size
    
    @classmethod
    def enforce_minimum(cls, amount: float) -> float:
        """Enforce minimum position size"""
        if amount < cls.MIN_POSITION:
            logger.warning(f"Position size {amount:.4f} below minimum, increasing to {cls.MIN_POSITION}")
            return cls.MIN_POSITION
        return amount

# Monkey patch for any imports
def patch_position_calculations():
    """Patch position calculations in the bot"""
    try:
        import sys
        
        # Try to patch various modules
        modules_to_patch = [
            'trading_bot',
            'core.trading.trading_bot',
            'core.trading.position_manager'
        ]
        
        for module_name in modules_to_patch:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                
                # Patch any calculate_position methods
                if hasattr(module, 'calculate_position_size'):
                    module.calculate_position_size = PositionSizer.calculate_position_size
                    logger.info(f"Patched {module_name}.calculate_position_size")
                
                # Patch TradingBot class if it exists
                if hasattr(module, 'TradingBot'):
                    trading_bot_class = getattr(module, 'TradingBot')
                    
                    # Wrap the buy method
                    if hasattr(trading_bot_class, 'buy_token'):
                        original_buy = trading_bot_class.buy_token
                        
                        async def patched_buy(self, address, amount):
                            amount = PositionSizer.enforce_minimum(amount)
                            return await original_buy(self, address, amount)
                        
                        trading_bot_class.buy_token = patched_buy
                        logger.info(f"Patched {module_name}.TradingBot.buy_token")
    
    except Exception as e:
        logger.error(f"Error patching position calculations: {e}")

# Auto-patch on import
patch_position_calculations()
'''
    
    with open("position_override.py", 'w', encoding='utf-8') as f:
        f.write(override_code)
    
    print("\n✅ Created position_override.py")
    print("   Add 'import position_override' to start_bot.py to force larger positions")

def main():
    print("🔧 FORCING LARGER POSITION SIZES")
    print("="*60)
    
    # Find where position sizes are calculated
    print("\n1. Finding position size logic...")
    found_files = find_position_size_logic()
    
    if found_files:
        print(f"\nFound position logic in {len(found_files)} files")
        
        # Try to patch the main trading bot
        print("\n2. Patching trading bot...")
        if patch_trading_bot():
            print("✅ Successfully patched trading bot")
        else:
            print("⚠️  Could not automatically patch - manual edit may be needed")
    
    # Create override module
    print("\n3. Creating position override module...")
    create_position_override()
    
    print("\n" + "="*60)
    print("📋 To force larger positions:")
    print("\n1. Add this line to the top of start_bot.py:")
    print("   import position_override")
    print("\n2. Or manually edit the trading bot to use:")
    print("   amount = max(0.3, <current calculation>)")
    print("\n3. Restart the bot and monitor positions")
    
    print("\n⚠️  If positions are still small, the issue might be:")
    print("   - Balance calculation is wrong")
    print("   - Safety checks limiting position size")
    print("   - Hardcoded values in the execution path")

if __name__ == "__main__":
    main()
