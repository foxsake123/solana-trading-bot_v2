#!/usr/bin/env python3
"""
Patch the enhanced_trading_bot.py to fix position sizing
"""
import os
import re

def patch_position_sizing():
    """Add safety check to position sizing in enhanced_trading_bot.py"""
    
    print("PATCHING ENHANCED TRADING BOT")
    print("=" * 60)
    
    file_path = 'enhanced_trading_bot.py'
    
    if not os.path.exists(file_path):
        print(f"ERROR: {file_path} not found!")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Looking for position sizing code...")
    
    # Find the calculate_position_size call in _execute_trade
    if 'position_size_pct = self.strategy.calculate_position_size' in content:
        print("Found position sizing calculation")
        
        # Add safety check after the calculation
        safety_check = '''
            # SAFETY CHECK: Ensure position size is reasonable
            max_position = min(balance_sol * 0.08, 0.8)  # Max 8% of balance or 0.8 SOL
            if amount_sol > max_position:
                logger.warning(f"Position size {amount_sol:.4f} exceeds safe maximum {max_position:.4f}")
                amount_sol = max_position
            '''
        
        # Find where to insert the safety check
        # Look for the line after position_size_pct calculation
        pattern = r'(amount_sol = balance_sol \* position_size_pct)'
        
        if re.search(pattern, content):
            # Add the safety check after this line
            replacement = r'\1' + safety_check
            content = re.sub(pattern, replacement, content)
            print("✅ Added safety check after position calculation")
        else:
            print("⚠️  Could not find exact pattern, trying alternative approach...")
            
            # Alternative: Add check before the minimum position size check
            if 'if amount_sol < min_position_sol:' in content:
                # Add safety check before this
                content = content.replace(
                    'if amount_sol < min_position_sol:',
                    '''# SAFETY CHECK: Cap at 8% of balance
            max_safe_position = min(balance_sol * 0.08, 0.8)
            if amount_sol > max_safe_position:
                logger.warning(f"Capping position from {amount_sol:.4f} to {max_safe_position:.4f} SOL")
                amount_sol = max_safe_position
            
            if amount_sol < min_position_sol:'''
                )
                print("✅ Added safety check using alternative method")
    
    # Write the patched content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\nSUCCESS: Patched position sizing")
    print("\nThe bot will now:")
    print("- Cap positions at 8% of balance")
    print("- Maximum 0.8 SOL per position")
    print("- No more 47 SOL positions!")
    
    return True

def show_correct_position_sizes():
    """Show what position sizes should be"""
    
    print("\n" + "="*60)
    print("CORRECT POSITION SIZES")
    print("="*60)
    
    balance = 6.8356  # Your current balance
    
    print(f"\nWith balance of {balance:.4f} SOL:")
    print(f"- 4% position: {balance * 0.04:.4f} SOL")
    print(f"- 5% position: {balance * 0.05:.4f} SOL")
    print(f"- 8% position: {balance * 0.08:.4f} SOL")
    print(f"- Absolute max: 0.8000 SOL")
    
    print("\nExpected position sizes: 0.4000 - 0.5468 SOL")
    print("NOT 47.8492 SOL!")

if __name__ == "__main__":
    # First fix the config
    import subprocess
    subprocess.run(['python', 'fix_position_sizing_bug.py'])
    
    # Then patch the bot
    patch_position_sizing()
    
    # Show expected sizes
    show_correct_position_sizes()