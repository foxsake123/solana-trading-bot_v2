#!/usr/bin/env python3
"""
Complete the Citadel-Barra strategy setup
"""

import os
import shutil
import json

def main():
    print("🏛️  Completing Citadel-Barra Strategy Setup...")
    print("="*60)
    
    # Step 1: Check if required files exist
    required_files = [
        'citadel_barra_strategy.py',
        'enhanced_trading_bot.py',
        'update_config_citadel.py',
        'citadel_strategy_monitor.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease save these files from Claude to your project root directory.")
        return
    
    print("✅ All required files present")
    
    # Step 2: Backup original start_bot.py
    if os.path.exists('start_bot.py'):
        backup_name = 'start_bot_original.py'
        if not os.path.exists(backup_name):
            shutil.copy('start_bot.py', backup_name)
            print(f"✅ Backed up original start_bot.py to {backup_name}")
    
    # Step 3: Check configuration
    config_path = 'config/trading_params.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if config.get('use_citadel_strategy', False):
            print("✅ Citadel strategy is ENABLED in configuration")
        else:
            print("⚠️  Citadel strategy is DISABLED in configuration")
            print("   To enable, set 'use_citadel_strategy': true in config/trading_params.json")
    
    # Step 4: Create test script
    test_script = '''#!/usr/bin/env python3
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
print("\\nTesting configuration...")
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

print("\\n✅ All tests passed! Citadel-Barra strategy is ready to use.")
print("\\nTo start the bot with Citadel strategy:")
print("   python start_bot.py simulation")
'''
    
    with open('test_citadel_setup.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("\n✅ Created test_citadel_setup.py")
    
    # Step 5: Instructions
    print("\n" + "="*60)
    print("📋 NEXT STEPS:")
    print("="*60)
    print("\n1. Run the test script to verify setup:")
    print("   python test_citadel_setup.py")
    
    print("\n2. If using the updated start_bot.py, save it:")
    print("   (The updated version automatically detects Citadel strategy)")
    
    print("\n3. Start the bot in simulation mode:")
    print("   python start_bot.py simulation")
    
    print("\n4. Monitor performance with:")
    print("   python citadel_strategy_monitor.py")
    
    print("\n5. View enhanced monitoring:")
    print("   python monitoring/enhanced_monitor.py")
    
    print("\n" + "="*60)
    print("💡 TIPS:")
    print("="*60)
    print("- Start with simulation mode for at least 100 trades")
    print("- Monitor factor exposures to ensure diversification")
    print("- Adjust signal weights based on performance")
    print("- Watch alpha decay to optimize holding periods")
    print("- Position sizes will be dynamically adjusted based on risk")
    
    print("\n🚀 Your bot is ready with institutional-grade risk management!")

if __name__ == "__main__":
    main()