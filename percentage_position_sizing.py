#!/usr/bin/env python3
"""
Implement percentage-based position sizing with single source of truth
Only trading_params.json will control position sizes
"""
import json
import os
import shutil
from datetime import datetime

class PositionSizingConfig:
    """Single source of truth for position sizing"""
    
    # THE ONLY PLACE WHERE POSITION SIZES ARE DEFINED
    POSITION_SIZING = {
        # Percentage of total balance per position
        "min_position_size_pct": 3.0,      # Minimum 3% of balance
        "default_position_size_pct": 4.0,   # Default 4% of balance  
        "max_position_size_pct": 5.0,       # Maximum 5% of balance
        
        # Absolute limits (safety bounds)
        "absolute_min_sol": 0.1,           # Never less than 0.1 SOL
        "absolute_max_sol": 2.0,           # Never more than 2 SOL
        
        # Other position controls
        "max_open_positions": 10,          # Maximum concurrent positions
        "max_portfolio_risk_pct": 30.0,    # Max 30% of portfolio at risk
    }
    
    @staticmethod
    def calculate_position_size(balance: float, 
                               risk_factor: float = 1.0,
                               use_default: bool = True) -> float:
        """
        Calculate position size based on percentage of balance
        
        Args:
            balance: Current SOL balance
            risk_factor: Risk multiplier (0.5 = half risk, 2.0 = double risk)
            use_default: If True, use default percentage, else calculate dynamically
            
        Returns:
            Position size in SOL
        """
        config = PositionSizingConfig.POSITION_SIZING
        
        if use_default:
            # Use default percentage
            pct = config["default_position_size_pct"]
        else:
            # Dynamic sizing based on risk
            pct = config["min_position_size_pct"] + (
                (config["max_position_size_pct"] - config["min_position_size_pct"]) * risk_factor
            )
        
        # Calculate position size
        position_size = balance * (pct / 100.0)
        
        # Apply absolute limits
        position_size = max(config["absolute_min_sol"], position_size)
        position_size = min(config["absolute_max_sol"], position_size)
        
        return round(position_size, 4)

def update_all_configs():
    """Update all config files to use percentage-based sizing"""
    
    print("🔧 UPDATING ALL CONFIGS TO PERCENTAGE-BASED SIZING")
    print("="*60)
    
    # Backup existing configs
    backup_dir = f"config/backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 1. Update trading_params.json (PRIMARY CONFIG)
    trading_params_path = "config/trading_params.json"
    if os.path.exists(trading_params_path):
        shutil.copy2(trading_params_path, os.path.join(backup_dir, "trading_params.json"))
        with open(trading_params_path, 'r') as f:
            params = json.load(f)
    else:
        params = {}
    
    # Remove all fixed SOL position sizes and add percentage-based
    params.update({
        # PERCENTAGE-BASED POSITION SIZING (PRIMARY)
        "min_position_size_pct": PositionSizingConfig.POSITION_SIZING["min_position_size_pct"],
        "default_position_size_pct": PositionSizingConfig.POSITION_SIZING["default_position_size_pct"],
        "max_position_size_pct": PositionSizingConfig.POSITION_SIZING["max_position_size_pct"],
        "absolute_min_sol": PositionSizingConfig.POSITION_SIZING["absolute_min_sol"],
        "absolute_max_sol": PositionSizingConfig.POSITION_SIZING["absolute_max_sol"],
        "max_open_positions": PositionSizingConfig.POSITION_SIZING["max_open_positions"],
        "max_portfolio_risk_pct": PositionSizingConfig.POSITION_SIZING["max_portfolio_risk_pct"],
        
        # Keep other important params
        "take_profit_pct": params.get("take_profit_pct", 0.30),
        "stop_loss_pct": params.get("stop_loss_pct", 0.05),
        "trailing_stop_enabled": params.get("trailing_stop_enabled", True),
        "ml_confidence_threshold": params.get("ml_confidence_threshold", 0.65),
    })
    
    # Remove old fixed position size fields
    fields_to_remove = [
        "min_position_size_sol", "max_position_size_sol", 
        "min_investment_per_token", "max_investment_per_token",
        "max_position_size_pct"  # Remove old percentage field
    ]
    for field in fields_to_remove:
        params.pop(field, None)
    
    with open(trading_params_path, 'w') as f:
        json.dump(params, f, indent=4)
    print("✅ Updated trading_params.json with percentage-based sizing")
    
    # 2. Update bot_control.json to remove position sizing
    bot_control_path = "config/bot_control.json"
    if os.path.exists(bot_control_path):
        shutil.copy2(bot_control_path, os.path.join(backup_dir, "bot_control.json"))
        with open(bot_control_path, 'r') as f:
            control = json.load(f)
        
        # Remove ALL position sizing from bot_control
        # It should only have runtime controls, not trading parameters
        for field in fields_to_remove:
            control.pop(field, None)
        
        # Add reference to trading_params
        control["position_sizing_config"] = "See config/trading_params.json"
        
        with open(bot_control_path, 'w') as f:
            json.dump(control, f, indent=4)
        print("✅ Cleaned bot_control.json (removed position sizing)")
    
    print(f"\n📁 Backups saved to: {backup_dir}")

def create_position_calculator():
    """Create a position size calculator module"""
    
    calculator_code = '''#!/usr/bin/env python3
"""
Position Size Calculator - Single source of truth
Reads from trading_params.json and calculates position sizes
"""
import json
import logging

logger = logging.getLogger(__name__)

class PositionCalculator:
    """Calculate position sizes based on percentage of balance"""
    
    def __init__(self, config_path="config/trading_params.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from trading_params.json"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Default values if config fails
            return {
                "min_position_size_pct": 3.0,
                "default_position_size_pct": 4.0,
                "max_position_size_pct": 5.0,
                "absolute_min_sol": 0.1,
                "absolute_max_sol": 2.0,
            }
    
    def calculate_position_size(self, balance: float, 
                               confidence: float = None,
                               volatility: float = None) -> float:
        """
        Calculate position size based on balance and optional factors
        
        Args:
            balance: Current SOL balance
            confidence: ML confidence score (0-1)
            volatility: Token volatility metric
            
        Returns:
            Position size in SOL
        """
        # Reload config to get latest values
        self.config = self._load_config()
        
        # Start with default percentage
        position_pct = self.config["default_position_size_pct"]
        
        # Adjust based on confidence if provided
        if confidence is not None:
            # Higher confidence = larger position (within bounds)
            min_pct = self.config["min_position_size_pct"]
            max_pct = self.config["max_position_size_pct"]
            position_pct = min_pct + (max_pct - min_pct) * confidence
        
        # Calculate position size
        position_size = balance * (position_pct / 100.0)
        
        # Apply absolute limits
        position_size = max(self.config["absolute_min_sol"], position_size)
        position_size = min(self.config["absolute_max_sol"], position_size)
        
        logger.info(f"Position size calculated: {position_size:.4f} SOL "
                   f"({position_pct:.1f}% of {balance:.4f} SOL balance)")
        
        return round(position_size, 4)
    
    def get_max_positions(self) -> int:
        """Get maximum number of open positions allowed"""
        return self.config.get("max_open_positions", 10)
    
    def check_portfolio_risk(self, open_positions: int, balance: float) -> bool:
        """Check if we can open another position based on portfolio risk"""
        max_risk_pct = self.config.get("max_portfolio_risk_pct", 30.0)
        position_size = self.calculate_position_size(balance)
        
        # Calculate total risk if we open another position
        total_risk = (open_positions + 1) * position_size
        risk_pct = (total_risk / balance) * 100
        
        return risk_pct <= max_risk_pct

# Global instance
position_calculator = PositionCalculator()

# Convenience function
def calculate_position_size(balance: float, **kwargs) -> float:
    """Calculate position size using global calculator"""
    return position_calculator.calculate_position_size(balance, **kwargs)
'''
    
    with open("position_calculator.py", "w") as f:
        f.write(calculator_code)
    print("✅ Created position_calculator.py")

def create_bot_patcher():
    """Create a patcher to update the bot to use percentage-based sizing"""
    
    patcher_code = '''#!/usr/bin/env python3
"""
Patch trading bot to use percentage-based position sizing
"""
import os
import re

def patch_trading_bot():
    """Patch the trading bot to use position_calculator"""
    
    print("🔧 Patching trading bot to use percentage-based sizing...")
    
    # Find trading bot files
    bot_files = []
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if 'trading_bot' in file and file.endswith('.py'):
                bot_files.append(os.path.join(root, file))
    
    for bot_file in bot_files:
        print(f"\\nPatching {bot_file}...")
        
        with open(bot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        backup_path = f"{bot_file}.backup_pct"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Add import if not present
        if 'from position_calculator import calculate_position_size' not in content:
            # Add import after other imports
            import_line = "from position_calculator import calculate_position_size\\n"
            if 'import' in content:
                lines = content.split('\\n')
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import') or line.strip().startswith('from'):
                        import_idx = i
                lines.insert(import_idx + 1, import_line.strip())
                content = '\\n'.join(lines)
        
        # Replace position calculations
        # Look for buy_token method
        pattern = r'async def buy_token.*?amount.*?(?=async def|class|$)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            method_content = match.group()
            # Replace amount calculations
            new_method = re.sub(
                r'amount\\s*=\\s*[^\\n]+',
                'amount = calculate_position_size(self.balance)',
                method_content
            )
            content = content.replace(method_content, new_method)
        
        # Save patched file
        with open(bot_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Patched {bot_file}")

if __name__ == "__main__":
    patch_trading_bot()
'''
    
    with open("patch_bot_percentage.py", "w") as f:
        f.write(patcher_code)
    print("✅ Created patch_bot_percentage.py")

def create_position_adjuster():
    """Create a simple UI to adjust position percentages"""
    
    adjuster_code = '''#!/usr/bin/env python3
"""
Simple UI to adjust position sizing percentages
"""
import json

def adjust_positions():
    """Adjust position sizing percentages"""
    
    print("📊 POSITION SIZE ADJUSTER (Percentage-Based)")
    print("="*50)
    
    # Load current config
    try:
        with open("config/trading_params.json", "r") as f:
            config = json.load(f)
    except:
        print("❌ Could not load config/trading_params.json")
        return
    
    # Show current values
    print("\\nCurrent Position Sizing:")
    print(f"  Minimum: {config.get('min_position_size_pct', 3)}% of balance")
    print(f"  Default: {config.get('default_position_size_pct', 4)}% of balance")
    print(f"  Maximum: {config.get('max_position_size_pct', 5)}% of balance")
    print(f"  Absolute min: {config.get('absolute_min_sol', 0.1)} SOL")
    print(f"  Absolute max: {config.get('absolute_max_sol', 2.0)} SOL")
    
    # Calculate examples
    print("\\nExamples with 10 SOL balance:")
    for pct in [config.get('min_position_size_pct', 3), 
                config.get('default_position_size_pct', 4),
                config.get('max_position_size_pct', 5)]:
        size = 10 * (pct / 100)
        print(f"  {pct}% = {size:.3f} SOL")
    
    print("\\nEnter new values (press Enter to keep current):")
    
    # Get new values
    new_min = input(f"Minimum % [{config.get('min_position_size_pct', 3)}]: ")
    if new_min:
        config['min_position_size_pct'] = float(new_min)
    
    new_default = input(f"Default % [{config.get('default_position_size_pct', 4)}]: ")
    if new_default:
        config['default_position_size_pct'] = float(new_default)
    
    new_max = input(f"Maximum % [{config.get('max_position_size_pct', 5)}]: ")
    if new_max:
        config['max_position_size_pct'] = float(new_max)
    
    # Save
    with open("config/trading_params.json", "w") as f:
        json.dump(config, f, indent=4)
    
    print("\\n✅ Position sizing updated!")
    print("\\nNew examples with 10 SOL balance:")
    for pct in [config['min_position_size_pct'], 
                config['default_position_size_pct'],
                config['max_position_size_pct']]:
        size = 10 * (pct / 100)
        print(f"  {pct}% = {size:.3f} SOL")
    
    print("\\nRestart the bot to use new position sizes.")

if __name__ == "__main__":
    adjust_positions()
'''
    
    with open("adjust_positions.py", "w") as f:
        f.write(adjuster_code)
    print("✅ Created adjust_positions.py")

def main():
    print("🚀 IMPLEMENTING PERCENTAGE-BASED POSITION SIZING")
    print("="*60)
    print("Single source of truth: config/trading_params.json")
    print("="*60)
    
    # Update all configs
    update_all_configs()
    
    # Create position calculator
    print("\n📦 Creating position calculator module...")
    create_position_calculator()
    
    # Create bot patcher
    print("\n🔧 Creating bot patcher...")
    create_bot_patcher()
    
    # Create position adjuster
    print("\n🎛️ Creating position adjuster...")
    create_position_adjuster()
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 How it works now:")
    print("\n1. Position sizes are based on % of balance:")
    print(f"   • Minimum: {PositionSizingConfig.POSITION_SIZING['min_position_size_pct']}% of balance")
    print(f"   • Default: {PositionSizingConfig.POSITION_SIZING['default_position_size_pct']}% of balance")
    print(f"   • Maximum: {PositionSizingConfig.POSITION_SIZING['max_position_size_pct']}% of balance")
    
    print("\n2. With 10 SOL balance:")
    for pct in [3, 4, 5]:
        print(f"   • {pct}% = {10 * pct / 100:.1f} SOL")
    
    print("\n3. To adjust position sizes:")
    print("   python adjust_positions.py")
    
    print("\n4. To patch the bot:")
    print("   python patch_bot_percentage.py")
    
    print("\n5. Then restart bot:")
    print("   python start_bot.py simulation")
    
    print("\n✨ Benefits:")
    print("   • Position sizes scale with your balance")
    print("   • Single source of truth (trading_params.json)")
    print("   • Easy to adjust percentages")
    print("   • No more hunting for hardcoded values!")

if __name__ == "__main__":
    main()
