import os
import shutil

# --- Configuration: Define the new project structure ---

# Define the new directory structure we want to create
# This is based on the plan we discussed
new_dirs = [
    "configs",
    "core/alerts",
    "core/analysis",
    "core/blockchain",
    "core/data",
    "core/safety",
    "core/storage",
    "core/trading",
    "core/strategies", 
    "data/databases",
    "data/logs",
    "data/models",
    "monitoring",
    "scripts/archive",
    "scripts/maintenance",
    "scripts/utilities",
    "tests"
]

# Define where each existing file should go.
# Format is: "new/path/to/file.py": "current/path/to/file.py"
file_mapping = {
    # Core Bot Logic
    "main.py": "start_bot.py",
    "core/trading/enhanced_trading_bot.py": "enhanced_trading_bot.py",
    "core/strategies/citadel_barra_strategy.py": "citadel_barra_strategy.py",
    "core/trading/position_manager.py": "core/trading/position_manager.py",
    "core/trading/risk_manager.py": "core/trading/risk_manager.py",

    # Config Files
    "configs/trading_params.json": "config/trading_params.json",
    "configs/bot_control.json": "config/bot_control.json",
    "configs/MASTER_CONFIG.json": "config/MASTER_CONFIG.json",
    "configs/factor_models.json": "config/factor_models.json",
    "configs/unified_config.py": "unified_config.py",

    # Safety and Database
    "core/safety/safety_manager.py": "core/safety/safety_manager.py",
    "core/storage/database.py": "core/storage/database.py",
    
    # Data Sources
    "core/data/market_data.py": "core/data/market_data.py",
    "core/data/token_scanner.py": "core/data/token_scanner.py",
    "core/data/birdeye_api_proper.py": "birdeye_api_proper.py",
    
    # Monitoring
    "monitoring/citadel_performance_monitor.py": "citadel_performance_monitor.py",
    "monitoring/citadel_monitor_simple.py": "citadel_monitor_simple.py",
    "monitoring/live_monitor.py": "monitoring/live_monitor.py",
    
    # Utilities & Scripts
    "scripts/maintenance/fix_contract_address_mapping.py": "fix_contract_address_mapping.py",
    "scripts/utilities/analyze_factors.py": "analyze_factors.py",
    "scripts/archive/quick_fixes.py": "quick_fixes.py", # Archiving this one
}

# --- Script Logic ---

def organize_project():
    """
    Automates the process of reorganizing the project files and directories.
    """
    print("Starting project reorganization...")

    # 1. Create all the new directories
    print("\nCreating new directory structure...")
    for d in new_dirs:
        try:
            os.makedirs(d, exist_ok=True)
            print(f"  - Created directory: {d}")
        except OSError as e:
            print(f"Error creating directory {d}: {e}")
            return

    # 2. Move files to their new locations
    print("\nMoving files to new locations...")
    for new_path, old_path in file_mapping.items():
        if os.path.exists(old_path):
            try:
                # Ensure the destination directory exists before moving
                dest_dir = os.path.dirname(new_path)
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                
                shutil.move(old_path, new_path)
                print(f"  - Moved: '{old_path}' -> '{new_path}'")
            except Exception as e:
                print(f"  - ERROR moving '{old_path}': {e}")
        else:
            print(f"  - WARNING: Source file not found, skipping: '{old_path}'")
    
    # 3. Clean up empty old directories if necessary (optional)
    # For now, we'll leave them to be safe.

    print("\nProject reorganization complete!")
    print("Please check the new structure and delete this script ('organize_project.py') when done.")

if __name__ == "__main__":
    organize_project()