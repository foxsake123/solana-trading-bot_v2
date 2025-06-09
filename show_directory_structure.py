#!/usr/bin/env python3
"""
Show current directory structure to help with cleanup
"""

import os
from pathlib import Path
from colorama import init, Fore, Style

init()

def show_directory_tree(directory=".", prefix="", max_depth=3, current_depth=0):
    """Display directory tree structure"""
    if current_depth > max_depth:
        return
        
    path = Path(directory)
    contents = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(contents):
        # Skip hidden files and __pycache__
        if item.name.startswith('.') or item.name == '__pycache__':
            continue
            
        is_last = i == len(contents) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and current_depth < max_depth:
            extension = "    " if is_last else "│   "
            show_directory_tree(item, prefix + extension, max_depth, current_depth + 1)

def analyze_project_structure():
    """Analyze and suggest organization improvements"""
    print(f"{Fore.CYAN}CURRENT PROJECT STRUCTURE{Style.RESET_ALL}")
    print("="*60)
    
    show_directory_tree()
    
    print(f"\n{Fore.YELLOW}FILE ANALYSIS{Style.RESET_ALL}")
    print("="*60)
    
    # Check for key files
    root_files = list(Path(".").glob("*.py"))
    config_files = list(Path(".").glob("*.json"))
    
    print(f"\nPython files in root: {len(root_files)}")
    for f in root_files[:10]:  # Show first 10
        print(f"  - {f.name}")
    
    if len(root_files) > 10:
        print(f"  ... and {len(root_files) - 10} more")
    
    print(f"\nConfig files in root: {len(config_files)}")
    for f in config_files:
        print(f"  - {f.name}")
    
    # Suggest organization
    print(f"\n{Fore.GREEN}SUGGESTED ORGANIZATION{Style.RESET_ALL}")
    print("="*60)
    
    suggestions = {
        "strategies/": ["citadel_barra_strategy.py", "enhanced_trading_bot.py"],
        "monitoring/": ["citadel_monitor_simple.py", "enhanced_monitor.py"],
        "scripts/": ["real_trading_setup.py", "EMERGENCY_STOP.py"],
        "DELETE": ["test_*.py", "fix_*.py", "check_*.py", "update_*.py"]
    }
    
    for folder, files in suggestions.items():
        print(f"\n{folder}:")
        for file in files:
            exists = any(Path(".").glob(file))
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if exists else f"{Fore.RED}✗{Style.RESET_ALL}"
            print(f"  {status} {file}")
    
    # Check for important files
    print(f"\n{Fore.CYAN}CRITICAL FILES CHECK{Style.RESET_ALL}")
    print("="*60)
    
    critical_files = {
        "start_bot.py": "Main entry point",
        "config/bot_config.py": "Bot configuration",
        "config/MASTER_CONFIG.json": "Master configuration",
        "core/trading/trading_bot.py": "Core trading logic",
        ".env": "API keys (should not be in git)"
    }
    
    for file, description in critical_files.items():
        exists = Path(file).exists()
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if exists else f"{Fore.RED}✗{Style.RESET_ALL}"
        print(f"{status} {file:<30} - {description}")

if __name__ == "__main__":
    analyze_project_structure()
