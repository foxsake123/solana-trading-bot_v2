#!/usr/bin/env python3
"""
Repository cleanup script - Python version
Works on all platforms without security restrictions
"""

import os
import shutil
from pathlib import Path
from colorama import init, Fore, Style

init()

class RepositoryCleaner:
    def __init__(self):
        self.root = Path(".")
        self.moved_files = []
        self.deleted_files = []
        self.created_dirs = []
        
    def create_directories(self):
        """Create organized directory structure"""
        directories = [
            "strategies",
            "monitoring/scripts",
            "scripts", 
            "docs",
            "tests",
            "data/ml",
            "data/logs",
            "data/db"
        ]
        
        print(f"{Fore.CYAN}Creating directory structure...{Style.RESET_ALL}")
        
        for dir_path in directories:
            path = self.root / dir_path
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                self.created_dirs.append(dir_path)
                print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Created: {dir_path}")
    
    def move_files(self):
        """Move files to organized locations"""
        file_moves = {
            "citadel_barra_strategy.py": "strategies/citadel_barra_strategy.py",
            "enhanced_trading_bot.py": "strategies/enhanced_trading_bot.py",
            "citadel_monitor_simple.py": "monitoring/citadel_monitor_simple.py",
            "enhanced_monitor.py": "monitoring/enhanced_monitor.py",
            "real_trading_setup.py": "scripts/real_trading_setup.py",
            "EMERGENCY_STOP.py": "scripts/EMERGENCY_STOP.py",
            "position_calculator.py": "scripts/position_calculator.py",
            "position_override.py": "scripts/position_override.py",
            "implement_optimization.py": "scripts/implement_optimization.py",
            "strategy_optimizer.py": "strategies/strategy_optimizer.py"
        }
        
        print(f"\n{Fore.CYAN}Moving files to organized locations...{Style.RESET_ALL}")
        
        for source, destination in file_moves.items():
            source_path = self.root / source
            dest_path = self.root / destination
            
            if source_path.exists():
                try:
                    # Create destination directory if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(source_path), str(dest_path))
                    self.moved_files.append((source, destination))
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Moved: {source} → {destination}")
                except Exception as e:
                    print(f"  {Fore.RED}✗{Style.RESET_ALL} Failed to move {source}: {e}")
    
    def delete_unnecessary_files(self):
        """Delete test and temporary files"""
        patterns_to_delete = [
            "test_*.py",
            "check_*.py",
            "fix_*.py",
            "update_*.py",
            "quick_*.py",
            "analyze_*.py",
            "simple_ml_training.py",
            "working_monitor.py"
        ]
        
        specific_files = [
            "bot_control.json",  # If exists in root (keep only config/bot_control.json)
            "trading_params.json",  # If exists in root
            "factor_models.json",  # If using MASTER_CONFIG.json
            "Citadel-Barra Implementation Guide.md",
            "solana-trading-bot_v2",
            "Cleanup Repository PowerShell Script.txt"
        ]
        
        print(f"\n{Fore.CYAN}Deleting unnecessary files...{Style.RESET_ALL}")
        
        # Delete by pattern
        for pattern in patterns_to_delete:
            for file_path in self.root.glob(pattern):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        self.deleted_files.append(file_path.name)
                        print(f"  {Fore.RED}✗{Style.RESET_ALL} Deleted: {file_path.name}")
                    except Exception as e:
                        print(f"  {Fore.YELLOW}!{Style.RESET_ALL} Could not delete {file_path.name}: {e}")
        
        # Delete specific files
        for filename in specific_files:
            file_path = self.root / filename
            if file_path.exists():
                # Special handling for config files - check if duplicate exists
                if filename in ["bot_control.json", "trading_params.json"]:
                    config_version = self.root / "config" / filename
                    if config_version.exists():
                        try:
                            file_path.unlink()
                            self.deleted_files.append(filename)
                            print(f"  {Fore.RED}✗{Style.RESET_ALL} Deleted duplicate: {filename} (keeping config/{filename})")
                        except Exception as e:
                            print(f"  {Fore.YELLOW}!{Style.RESET_ALL} Could not delete {filename}: {e}")
                    else:
                        print(f"  {Fore.YELLOW}!{Style.RESET_ALL} Keeping {filename} (no config version found)")
                else:
                    try:
                        file_path.unlink()
                        self.deleted_files.append(filename)
                        print(f"  {Fore.RED}✗{Style.RESET_ALL} Deleted: {filename}")
                    except Exception as e:
                        print(f"  {Fore.YELLOW}!{Style.RESET_ALL} Could not delete {filename}: {e}")
    
    def check_duplicates(self):
        """Check for duplicate configuration files"""
        print(f"\n{Fore.CYAN}Checking for duplicate configurations...{Style.RESET_ALL}")
        
        duplicates = [
            ("bot_control.json", "config/bot_control.json"),
            ("trading_params.json", "config/trading_params.json"),
            ("MASTER_CONFIG.json", "config/MASTER_CONFIG.json")
        ]
        
        for root_file, config_file in duplicates:
            root_path = self.root / root_file
            config_path = self.root / config_file
            
            if root_path.exists() and config_path.exists():
                print(f"  {Fore.YELLOW}⚠{Style.RESET_ALL}  Found duplicate: {root_file} and {config_file}")
                print(f"     Consider removing the root version")
    
    def create_gitignore(self):
        """Create or update .gitignore file"""
        gitignore_path = self.root / ".gitignore"
        
        if not gitignore_path.exists():
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Trading Bot Specific
.env
data/db/*.db
data/logs/
data/ml/*.csv
config/real_trading_config.json
monitoring/*.log
monitoring/real_trading.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Sensitive
*.key
*.pem
wallet_*.json
private_keys/

# Temporary
*.tmp
*.bak
*~
"""
            gitignore_path.write_text(gitignore_content)
            print(f"\n{Fore.GREEN}✓{Style.RESET_ALL} Created .gitignore file")
    
    def show_summary(self):
        """Show cleanup summary"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}CLEANUP COMPLETE!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}Summary:{Style.RESET_ALL}")
        print(f"  • Created {len(self.created_dirs)} directories")
        print(f"  • Moved {len(self.moved_files)} files")
        print(f"  • Deleted {len(self.deleted_files)} unnecessary files")
        
        print(f"\n{Fore.YELLOW}Recommended structure:{Style.RESET_ALL}")
        print("""
solana-trading-bot/
├── config/               # All configuration files
├── core/                 # Core trading logic
├── strategies/           # Trading strategies (Citadel-Barra, etc)
├── ml/                   # Machine learning models
├── monitoring/           # Monitoring and analysis tools
├── scripts/              # Utility and setup scripts
├── data/                 # Database, logs, ML data
├── docs/                 # Documentation
├── tests/                # Unit tests
├── start_bot.py          # Main entry point
└── .env                  # API keys (not in git)
""")
        
        print(f"\n{Fore.YELLOW}Next steps:{Style.RESET_ALL}")
        print("1. Review the changes")
        print("2. Run: python show_directory_structure.py")
        print("3. Commit: git add -A && git commit -m 'Reorganized repository structure'")
        print("4. Run pre-flight: python scripts/real_trading_setup.py")
    
    def run(self):
        """Run the complete cleanup process"""
        print(f"{Fore.CYAN}Starting Repository Cleanup...{Style.RESET_ALL}")
        print("="*60)
        
        try:
            self.create_directories()
            self.move_files()
            self.delete_unnecessary_files()
            self.check_duplicates()
            self.create_gitignore()
            self.show_summary()
        except Exception as e:
            print(f"\n{Fore.RED}Error during cleanup: {e}{Style.RESET_ALL}")
            print("Some operations may have completed successfully.")

if __name__ == "__main__":
    cleaner = RepositoryCleaner()
    cleaner.run()
