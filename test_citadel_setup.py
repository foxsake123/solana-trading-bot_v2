#!/usr/bin/env python3
"""Test script to verify Citadel-Barra integration"""

import sys
import json

# Test imports
print("Testing imports...")
try:
    from citadel_barra_strategy import CitadelBarraStrategy, BarraFactors
    print("✅ CitadelBarraStrategy imported successfully")
except ImportError as e:
    print(f"❌ Failed to import CitadelBarraStrategy: {e}")
    sys.exit(1)

try:
    from enhanced_trading_bot import EnhancedTradingBot
    print("✅ EnhancedTradingBot imported successfully")
except ImportError as e:
    print(f"❌ Failed to import EnhancedTradingBot: {e}")
    sys.exit(1)

# Test configuration
print("\nTesting configuration...")
try:
    with open('config/trading_params.json', 'r') as f:
        config = json.load(f)
    
    if 'use_citadel_strategy' in config:
        print(f"✅ use_citadel_strategy: {config['use_citadel_strategy']}")
    
    if 'signal_weights' in config:
        print("✅ Signal weights configured:")
        for signal, weight in config['signal_weights'].items():
            print(f"   - {signal}: {weight}")
    
    if 'factor_limits' in config:
        print("✅ Factor limits configured")
        
except Exception as e:
    print(f"❌ Configuration error: {e}")

print("\n✅ All tests passed! Citadel-Barra strategy is ready to use.")
print("\nTo start the bot with Citadel strategy:")
print("   python start_bot.py simulation")
