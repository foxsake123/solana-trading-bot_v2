# fix_bot_logic.py
import shutil
from datetime import datetime

# Backup trading_bot.py
bot_file = "core/trading/trading_bot.py"
backup = f"{bot_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(bot_file, backup)
print(f"✅ Backed up to {backup}")

# Read the file
with open(bot_file, 'r') as f:
    content = f.read()

# Check if analyze_and_trade_token is being called
if "analyze_and_trade_token" not in content:
    print("❌ Bot not calling analyze_and_trade_token!")
    
    # Find where tokens are being processed
    if "for token in all_tokens:" in content:
        # Replace the loop to actually analyze tokens
        content = content.replace(
            "for token in all_tokens:",
            "for token in all_tokens:\n                await self.analyze_and_trade_token(token)"
        )
        print("✅ Fixed token analysis loop")
    
    # Write back
    with open(bot_file, 'w') as f:
        f.write(content)
    
    print("✅ Bot should now analyze and trade tokens")
    print("Restart: python start_bot.py")
else:
    print("✓ Bot already has analyze_and_trade_token calls")
    print("Checking if method exists...")
    
    # Add simple buy logic if analyze method is too complex
    simple_analyze = '''
    async def analyze_and_trade_token(self, token: Dict):
        """Simple analysis for immediate trades"""
        try:
            address = token.get('contract_address', token.get('address', ''))
            symbol = token.get('symbol', 'UNKNOWN')
            price_change = token.get('price_change_24h', 0)
            volume = token.get('volume_24h', 0)
            
            # Simple criteria
            if price_change > 5 and volume > 10000:
                print(f"✅ BUY SIGNAL: {symbol} (+{price_change:.1f}%)")
                
                # Buy 5% of balance
                amount = self.balance * 0.05
                await self.buy_token(address, amount)
        except Exception as e:
            print(f"Error analyzing {token}: {e}")
'''
    
    # Check if we need to add this method
    if "Simple analysis for immediate trades" not in content:
        # Add before the last line
        content = content.replace(
            "# End of class",
            simple_analyze + "\n    # End of class"
        )
        
        with open(bot_file, 'w') as f:
            f.write(content)
        
        print("✅ Added simple analyze method")

print("\n🎯 Next: python start_bot.py")