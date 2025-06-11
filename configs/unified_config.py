#!/usr/bin/env python3
"""
Unified configuration manager - Single source of truth for all bot parameters
"""
import json
import os
import shutil
from datetime import datetime

class UnifiedConfig:
    """Single source of truth for all bot configuration"""
    
    # THE MASTER CONFIG - All parameters in one place
    MASTER_CONFIG = {
        # POSITION SIZING (MOST IMPORTANT!)
        "position_sizing": {
            "min_position_size_sol": 0.3,      # Minimum 0.3 SOL per trade
            "max_position_size_sol": 0.5,      # Maximum 0.5 SOL per trade
            "default_position_size_sol": 0.4,  # Default 0.4 SOL if not calculated
            "max_investment_per_token": 0.5,   # For compatibility
            "min_investment_per_token": 0.3,   # For compatibility
            "max_open_positions": 10,
            "position_size_method": "fixed",    # "fixed" or "dynamic"
        },
        
        # PROFIT MANAGEMENT
        "profit_management": {
            "take_profit_target": 1.50,        # 50% profit (1.5x)
            "take_profit_pct": 0.50,           # 50% for other configs
            "stop_loss_percentage": 0.05,      # 5% stop loss
            "stop_loss_pct": 0.05,             # For compatibility
            "trailing_stop_enabled": True,
            "trailing_stop_percentage": 0.15,  # 15% trailing
            "trailing_stop_activation_pct": 0.30,  # Activate at 30% profit
            "trailing_stop_distance_pct": 0.15,    # Trail by 15%
        },
        
        # TOKEN FILTERS
        "token_filters": {
            "min_safety_score": 0.0,           # Disabled for now
            "min_volume": 1000.0,              # Low to catch more opportunities
            "min_volume_24h": 20000.0,         # For other configs
            "min_liquidity": 5000.0,           # Low to catch more
            "min_liquidity_usd": 5000.0,       # For compatibility
            "min_mcap": 10000.0,
            "min_market_cap": 100000.0,        # For other configs
            "min_holders": 10,
            "max_price_change_24h": 10000.0,   # Allow up to 10,000% gains!
            "min_price_change_24h": -50.0,
            "min_price_change_1h": -50.0,
            "min_price_change_6h": -50.0,
        },
        
        # ML CONFIGURATION
        "ml_config": {
            "use_machine_learning": True,
            "ml_confidence_threshold": 0.65,
            "use_ml_predictions": True,
            "ml_weight_in_decision": 0.4,
        },
        
        # EXECUTION
        "execution": {
            "slippage_tolerance": 0.10,        # 10% slippage
            "slippage_tolerance_display": 10.0,
            "scan_interval": 60,               # Scan every 60 seconds
            "simulation_mode": True,
            "starting_simulation_balance": 10.0,
        },
        
        # BOT CONTROL
        "bot_control": {
            "running": True,
            "filter_fake_tokens": False,
            "use_birdeye_api": True,
            "use_technical_analysis": True,
        }
    }
    
    @staticmethod
    def get_all_config_files():
        """List all config files that need to be updated"""
        return [
            "config/bot_control.json",
            "config/trading_params.json",
            "config/data/bot_control.json"  # Sometimes duplicated here
        ]
    
    @classmethod
    def backup_configs(cls):
        """Backup existing config files"""
        backup_dir = f"config/backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        for config_file in cls.get_all_config_files():
            if os.path.exists(config_file):
                filename = os.path.basename(config_file)
                shutil.copy2(config_file, os.path.join(backup_dir, filename))
                print(f"✅ Backed up {config_file}")
        
        return backup_dir
    
    @classmethod
    def create_unified_config(cls):
        """Create the unified configuration file"""
        # Flatten the master config for bot_control.json format
        bot_control_config = {
            # Position sizing
            "min_investment_per_token": cls.MASTER_CONFIG["position_sizing"]["min_position_size_sol"],
            "max_investment_per_token": cls.MASTER_CONFIG["position_sizing"]["max_position_size_sol"],
            "min_position_size_sol": cls.MASTER_CONFIG["position_sizing"]["min_position_size_sol"],
            "max_position_size_sol": cls.MASTER_CONFIG["position_sizing"]["max_position_size_sol"],
            "default_position_size_sol": cls.MASTER_CONFIG["position_sizing"]["default_position_size_sol"],
            "max_open_positions": cls.MASTER_CONFIG["position_sizing"]["max_open_positions"],
            
            # Profit management
            "take_profit_target": cls.MASTER_CONFIG["profit_management"]["take_profit_target"],
            "stop_loss_percentage": cls.MASTER_CONFIG["profit_management"]["stop_loss_percentage"],
            "trailing_stop_enabled": cls.MASTER_CONFIG["profit_management"]["trailing_stop_enabled"],
            "trailing_stop_percentage": cls.MASTER_CONFIG["profit_management"]["trailing_stop_percentage"],
            
            # Token filters
            "MIN_SAFETY_SCORE": cls.MASTER_CONFIG["token_filters"]["min_safety_score"],
            "MIN_VOLUME": cls.MASTER_CONFIG["token_filters"]["min_volume"],
            "MIN_LIQUIDITY": cls.MASTER_CONFIG["token_filters"]["min_liquidity"],
            "MIN_MCAP": cls.MASTER_CONFIG["token_filters"]["min_mcap"],
            "MIN_HOLDERS": cls.MASTER_CONFIG["token_filters"]["min_holders"],
            "MAX_PRICE_CHANGE_24H": cls.MASTER_CONFIG["token_filters"]["max_price_change_24h"],
            "MIN_PRICE_CHANGE_24H": cls.MASTER_CONFIG["token_filters"]["min_price_change_24h"],
            "MIN_PRICE_CHANGE_1H": cls.MASTER_CONFIG["token_filters"]["min_price_change_1h"],
            "MIN_PRICE_CHANGE_6H": cls.MASTER_CONFIG["token_filters"]["min_price_change_6h"],
            
            # ML config
            "use_machine_learning": cls.MASTER_CONFIG["ml_config"]["use_machine_learning"],
            "ml_confidence_threshold": cls.MASTER_CONFIG["ml_config"]["ml_confidence_threshold"],
            
            # Execution
            "slippage_tolerance": cls.MASTER_CONFIG["execution"]["slippage_tolerance"],
            "slippage_tolerance_display": cls.MASTER_CONFIG["execution"]["slippage_tolerance_display"],
            "simulation_mode": cls.MASTER_CONFIG["execution"]["simulation_mode"],
            "starting_simulation_balance": cls.MASTER_CONFIG["execution"]["starting_simulation_balance"],
            
            # Bot control
            "running": cls.MASTER_CONFIG["bot_control"]["running"],
            "filter_fake_tokens": cls.MASTER_CONFIG["bot_control"]["filter_fake_tokens"],
            "use_birdeye_api": cls.MASTER_CONFIG["bot_control"]["use_birdeye_api"],
        }
        
        # Save to bot_control.json
        with open("config/bot_control.json", "w") as f:
            json.dump(bot_control_config, f, indent=4)
        print("✅ Updated config/bot_control.json")
        
        # Create trading_params.json with extended format
        trading_params_config = {
            # Position sizing
            "min_position_size_sol": cls.MASTER_CONFIG["position_sizing"]["min_position_size_sol"],
            "max_position_size_sol": cls.MASTER_CONFIG["position_sizing"]["max_position_size_sol"],
            "max_open_positions": cls.MASTER_CONFIG["position_sizing"]["max_open_positions"],
            
            # Profit management
            "take_profit_pct": cls.MASTER_CONFIG["profit_management"]["take_profit_pct"],
            "stop_loss_pct": cls.MASTER_CONFIG["profit_management"]["stop_loss_pct"],
            "trailing_stop_enabled": cls.MASTER_CONFIG["profit_management"]["trailing_stop_enabled"],
            "trailing_stop_activation_pct": cls.MASTER_CONFIG["profit_management"]["trailing_stop_activation_pct"],
            "trailing_stop_distance_pct": cls.MASTER_CONFIG["profit_management"]["trailing_stop_distance_pct"],
            
            # Token filters
            "min_safety_score": cls.MASTER_CONFIG["token_filters"]["min_safety_score"],
            "min_volume_24h": cls.MASTER_CONFIG["token_filters"]["min_volume_24h"],
            "min_liquidity": cls.MASTER_CONFIG["token_filters"]["min_liquidity_usd"],
            "min_holders": cls.MASTER_CONFIG["token_filters"]["min_holders"],
            "min_market_cap": cls.MASTER_CONFIG["token_filters"]["min_market_cap"],
            
            # ML
            "use_ml_predictions": cls.MASTER_CONFIG["ml_config"]["use_ml_predictions"],
            "ml_confidence_threshold": cls.MASTER_CONFIG["ml_config"]["ml_confidence_threshold"],
            "ml_weight_in_decision": cls.MASTER_CONFIG["ml_config"]["ml_weight_in_decision"],
            
            # Other params for compatibility
            "max_position_size_pct": 0.05,  # 5% of portfolio
            "max_daily_loss_pct": 0.1,
            "max_drawdown_pct": 0.2,
            "use_technical_analysis": True,
            "slippage_tolerance": cls.MASTER_CONFIG["execution"]["slippage_tolerance"],
        }
        
        with open("config/trading_params.json", "w") as f:
            json.dump(trading_params_config, f, indent=4)
        print("✅ Updated config/trading_params.json")
        
        # Also save a master config for reference
        with open("config/MASTER_CONFIG.json", "w") as f:
            json.dump(cls.MASTER_CONFIG, f, indent=4)
        print("✅ Created config/MASTER_CONFIG.json as reference")
    
    @classmethod
    def verify_position_sizes(cls):
        """Verify that position sizes are correctly set"""
        print("\n🔍 Verifying Position Sizes:")
        
        # Check bot_control.json
        with open("config/bot_control.json", "r") as f:
            bot_control = json.load(f)
        
        print(f"\nbot_control.json:")
        print(f"  min_investment_per_token: {bot_control.get('min_investment_per_token', 'NOT SET')}")
        print(f"  max_investment_per_token: {bot_control.get('max_investment_per_token', 'NOT SET')}")
        print(f"  min_position_size_sol: {bot_control.get('min_position_size_sol', 'NOT SET')}")
        print(f"  max_position_size_sol: {bot_control.get('max_position_size_sol', 'NOT SET')}")
        
        # Check trading_params.json
        with open("config/trading_params.json", "r") as f:
            trading_params = json.load(f)
        
        print(f"\ntrading_params.json:")
        print(f"  min_position_size_sol: {trading_params.get('min_position_size_sol', 'NOT SET')}")
        print(f"  max_position_size_sol: {trading_params.get('max_position_size_sol', 'NOT SET')}")
        
        # Check if values match master config
        min_size = cls.MASTER_CONFIG["position_sizing"]["min_position_size_sol"]
        max_size = cls.MASTER_CONFIG["position_sizing"]["max_position_size_sol"]
        
        all_correct = (
            bot_control.get('min_investment_per_token') == min_size and
            bot_control.get('max_investment_per_token') == max_size and
            bot_control.get('min_position_size_sol') == min_size and
            bot_control.get('max_position_size_sol') == max_size and
            trading_params.get('min_position_size_sol') == min_size and
            trading_params.get('max_position_size_sol') == max_size
        )
        
        if all_correct:
            print(f"\n✅ All position sizes correctly set to {min_size}-{max_size} SOL")
        else:
            print(f"\n❌ Position sizes are NOT correctly set!")
            print(f"   Expected: {min_size}-{max_size} SOL")

def create_position_size_checker():
    """Create a script to check what position sizes the bot is actually using"""
    checker_code = '''#!/usr/bin/env python3
"""
Check what position sizes the bot is actually using
"""
import json
import sys
import os

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.bot_config import BotConfiguration
    
    print("🔍 Checking BotConfiguration values:")
    print(f"MAX_INVESTMENT_PER_TOKEN: {BotConfiguration.TRADING_PARAMETERS.get('MAX_INVESTMENT_PER_TOKEN')}")
    print(f"MIN_INVESTMENT: {BotConfiguration.TRADING_PARAMETERS.get('MIN_INVESTMENT', 'NOT SET')}")
    
    # Load control file
    BotConfiguration.load_trading_parameters()
    print(f"\\nAfter loading from control file:")
    print(f"MAX_INVESTMENT_PER_TOKEN: {BotConfiguration.TRADING_PARAMETERS.get('MAX_INVESTMENT_PER_TOKEN')}")
    
except Exception as e:
    print(f"Error loading BotConfiguration: {e}")

# Check control files directly
print("\\n📄 Direct file check:")
with open('config/bot_control.json', 'r') as f:
    control = json.load(f)
    print(f"bot_control.json - min_investment_per_token: {control.get('min_investment_per_token')}")
    print(f"bot_control.json - max_investment_per_token: {control.get('max_investment_per_token')}")
'''
    
    with open("check_position_sizes.py", "w") as f:
        f.write(checker_code)
    print("\n✅ Created check_position_sizes.py")

def main():
    print("🚀 UNIFIED CONFIGURATION MANAGER")
    print("="*60)
    print("Creating single source of truth for all bot parameters")
    print("="*60)
    
    # Backup existing configs
    print("\n1. Backing up existing configs...")
    backup_dir = UnifiedConfig.backup_configs()
    print(f"   Backups saved to: {backup_dir}")
    
    # Create unified configs
    print("\n2. Creating unified configuration...")
    UnifiedConfig.create_unified_config()
    
    # Verify position sizes
    print("\n3. Verifying configuration...")
    UnifiedConfig.verify_position_sizes()
    
    # Create position size checker
    print("\n4. Creating diagnostic tools...")
    create_position_size_checker()
    
    print("\n" + "="*60)
    print("✅ CONFIGURATION UNIFIED!")
    print("="*60)
    print("\nKey changes made:")
    print(f"• Position sizes: 0.3-0.5 SOL (was ~0.08)")
    print(f"• Take profit: 50% (was 15%)")
    print(f"• Trailing stop: 15% (was 3%)")
    print(f"• Max price change: 10,000% (was 1,000%)")
    
    print("\n📋 Next steps:")
    print("1. Run: python check_position_sizes.py")
    print("   To verify bot is using new sizes")
    print("\n2. Restart bot: python start_bot.py simulation")
    print("   To load new configuration")
    print("\n3. Monitor: python enhanced_monitor.py")
    print("   To see if positions are now larger")
    
    print("\n⚠️  IMPORTANT: The bot might have hardcoded position size logic.")
    print("   If positions are still small after restart, we need to check")
    print("   the actual trading logic in trading_bot.py")

if __name__ == "__main__":
    main()
