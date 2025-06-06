#!/usr/bin/env python3
"""
Safe update script for wallet configuration
Preserves existing settings while adding security
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def safe_update_files():
    """Safely update configuration files while preserving settings"""
    
    print("🔒 SAFE WALLET CONFIGURATION UPDATE")
    print("=" * 60)
    
    # Create backup directory
    backup_dir = Path(f"backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    print(f"📁 Created backup directory: {backup_dir}")
    
    # 1. BACKUP EXISTING FILES
    print("\n📦 Backing up existing files...")
    
    files_to_backup = [
        ".gitignore",
        ".env",
        "config/bot_control.json",
        "config/bot_control_real.json",
        "config/trading_params.json"
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            backup_path = backup_dir / file.replace('/', '_')
            shutil.copy2(file, backup_path)
            print(f"  ✓ Backed up {file}")
    
    # 2. UPDATE .GITIGNORE
    print("\n📝 Updating .gitignore...")
    
    # Comprehensive gitignore content
    gitignore_content = """# === PRIVATE FILES - NEVER COMMIT ===
.env
.env.local
.env.*.local
wallet_backup/
*private*
*secret*
*.pem
*.key

# === DATABASE ===
*.db
*.sqlite
*.sqlite3
data/db/

# === PYTHON ===
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
venv/
env/
ENV/
.venv/

# === LOGS ===
logs/
*.log
log.txt

# === ML MODELS & DATA ===
data/models/
*.pkl
*.pickle
*.h5
*.model
*_report_*.json
*_backup_*.json
*_BACKUP_*.json
trade_history_export.csv
wallet_balance_*.json
performance_report_*.json
optimization_report_*.json
ml_readiness_report.json

# === BOT SPECIFIC ===
data/safety_state.json
config/SAFETY_OVERRIDE.json
performance_summary_*.txt
session_summary_*.json
wallet_backup_*.json

# === IDE ===
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject

# === OS ===
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# === TEMPORARY FILES ===
*.tmp
*.temp
*.bak
*.cache
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  ✓ Updated .gitignore with comprehensive security rules")
    
    # 3. CHECK/UPDATE .ENV
    print("\n🔑 Checking .env configuration...")
    
    env_exists = os.path.exists(".env")
    existing_env_content = {}
    
    if env_exists:
        # Parse existing .env to preserve API keys
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_env_content[key.strip()] = value.strip()
        
        print("  ✓ Found existing .env file")
        print("  ✓ Preserved existing settings")
    
    # Get wallet info from user
    print("\n🔐 WALLET CONFIGURATION")
    print("-" * 40)
    
    # Check if we already have a wallet configured
    current_wallet = existing_env_content.get("WALLET_PUBLIC_ADDRESS", "")
    
    if current_wallet:
        print(f"Current wallet: {current_wallet}")
        response = input("Do you want to create a NEW wallet? (y/n): ").lower()
        
        if response != 'y':
            print("  ✓ Keeping existing wallet configuration")
            new_wallet_address = current_wallet
            update_private_key = False
        else:
            print("\n📱 Please create a new wallet in Phantom/Solflare")
            new_wallet_address = input("Enter your NEW public wallet address: ").strip()
            update_private_key = True
    else:
        print("No wallet configured yet.")
        print("\n📱 Please create a wallet in Phantom/Solflare")
        new_wallet_address = input("Enter your public wallet address: ").strip()
        update_private_key = True
    
    # Validate wallet address
    if len(new_wallet_address) < 32 or len(new_wallet_address) > 44:
        print("❌ Invalid wallet address length!")
        print("   Solana addresses are typically 32-44 characters")
        return
    
    # Update .env file
    env_content = f"""# Solana Trading Bot Configuration
# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# WALLET CONFIGURATION
WALLET_PUBLIC_ADDRESS={new_wallet_address}
"""
    
    if update_private_key:
        print("\n⚠️  PRIVATE KEY SETUP")
        print("You'll need to add your private key manually to .env")
        print("Add this line to .env after this script completes:")
        print("WALLET_PRIVATE_KEY=your_private_key_here")
        env_content += "WALLET_PRIVATE_KEY=REPLACE_WITH_YOUR_PRIVATE_KEY\n"
    else:
        # Preserve existing private key
        if "WALLET_PRIVATE_KEY" in existing_env_content:
            env_content += f"WALLET_PRIVATE_KEY={existing_env_content['WALLET_PRIVATE_KEY']}\n"
    
    env_content += "\n# API KEYS\n"
    
    # Preserve existing API keys
    api_keys = ["HELIUS_API_KEY", "BIRDEYE_API_KEY", "DEXSCREENER_API_KEY"]
    for key in api_keys:
        if key in existing_env_content:
            env_content += f"{key}={existing_env_content[key]}\n"
        else:
            env_content += f"{key}=\n"
    
    env_content += "\n# NETWORK\n"
    env_content += f"SOLANA_RPC_URL={existing_env_content.get('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')}\n"
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("  ✓ Updated .env file")
    
    # 4. CREATE .ENV.EXAMPLE
    print("\n📄 Creating .env.example...")
    
    example_content = """# Solana Trading Bot Configuration
# Copy this file to .env and fill in your values

# WALLET CONFIGURATION
WALLET_PUBLIC_ADDRESS=your_wallet_address_here
WALLET_PRIVATE_KEY=your_private_key_here

# API KEYS (Optional but recommended)
HELIUS_API_KEY=your_helius_api_key_here
BIRDEYE_API_KEY=your_birdeye_api_key_here
DEXSCREENER_API_KEY=your_dexscreener_api_key_here

# NETWORK
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
"""
    
    with open(".env.example", "w") as f:
        f.write(example_content)
    
    print("  ✓ Created .env.example (safe for GitHub)")
    
    # 5. UPDATE CONFIG FILES
    print("\n⚙️  Updating configuration files...")
    
    # Update bot_control_real.json
    if os.path.exists("config/bot_control_real.json"):
        with open("config/bot_control_real.json", "r") as f:
            config = json.load(f)
        
        config["real_wallet_address"] = new_wallet_address
        
        # If this is a new wallet, reset balance
        if update_private_key:
            config["starting_balance"] = 0.0
        
        with open("config/bot_control_real.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("  ✓ Updated config/bot_control_real.json")
    
    # Update bot_control.json
    if os.path.exists("config/bot_control.json"):
        with open("config/bot_control.json", "r") as f:
            config = json.load(f)
        
        # Ensure simulation mode for safety
        config["simulation_mode"] = True
        config["real_wallet_address"] = new_wallet_address
        
        with open("config/bot_control.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("  ✓ Updated config/bot_control.json")
    
    # Create wallet info file
    wallet_info = {
        "public_address": new_wallet_address,
        "updated_at": datetime.now().isoformat(),
        "network": "mainnet-beta"
    }
    
    with open("config/wallet_info.json", "w") as f:
        json.dump(wallet_info, f, indent=2)
    
    print("  ✓ Created config/wallet_info.json")
    
    # 6. CHECK GIT STATUS
    print("\n🔍 Checking Git safety...")
    
    # Run git status to check
    import subprocess
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True)
        
        if ".env" in result.stdout:
            print("  ⚠️  WARNING: .env is being tracked by git!")
            print("     Run: git rm --cached .env")
        else:
            print("  ✓ .env is properly ignored by git")
    except:
        print("  ℹ️  Could not check git status")
    
    # 7. SUMMARY
    print("\n" + "="*60)
    print("✅ CONFIGURATION UPDATE COMPLETE!")
    print("="*60)
    
    print(f"\n📋 Wallet Address: {new_wallet_address}")
    print(f"📁 Backups saved in: {backup_dir}/")
    
    if update_private_key:
        print("\n⚠️  IMPORTANT: Add your private key to .env:")
        print("   1. Open .env file")
        print("   2. Replace WALLET_PRIVATE_KEY value")
        print("   3. Save the file")
    
    print("\n🔒 Security Checklist:")
    print("  ✓ .gitignore updated")
    print("  ✓ .env configured")
    print("  ✓ Config files updated")
    print("  ✓ Backups created")
    
    print("\n📤 Safe Git Commands:")
    print("  git add .gitignore .env.example config/")
    print("  git commit -m 'Update wallet configuration securely'")
    print("  git push")
    
    print("\n💰 Next Steps:")
    print("  1. Add private key to .env (if new wallet)")
    print("  2. Fund wallet with 0.5-1 SOL")
    print("  3. Run: python verify_wallet.py")
    print("  4. Start bot: python start_bot.py real")

if __name__ == "__main__":
    try:
        safe_update_files()
    except KeyboardInterrupt:
        print("\n\n❌ Update cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check the error and try again")
