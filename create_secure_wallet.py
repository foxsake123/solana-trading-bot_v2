#!/usr/bin/env python3
"""
Simple secure wallet setup for Solana trading bot
Works with existing solana-py installation
"""
import os
import json
from datetime import datetime
from pathlib import Path
import shutil
from solders.keypair import Keypair  # This is from solana-py

def create_secure_wallet():
    """Create a new wallet with proper security measures"""
    
    print("🔐 SECURE WALLET SETUP FOR SOLANA TRADING BOT")
    print("=" * 60)
    
    # Generate new keypair using solders (from solana-py)
    new_keypair = Keypair()
    
    # Get wallet info
    public_key = str(new_keypair.pubkey())
    # Convert private key to base58 string (Solana standard format)
    private_key_bytes = bytes(new_keypair)  # This gets the full 64-byte keypair
    # For Phantom wallet compatibility, we need the base58 format
    # We'll store it as a list of integers for now
    private_key_list = list(private_key_bytes)
    
    print(f"\n✅ New wallet created!")
    print(f"Public Address: {public_key}")
    print(f"\n⚠️  IMPORTANT: Your private key will be saved securely!")
    print("=" * 60)
    
    # Create backup directory
    backup_dir = Path("wallet_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Save wallet info securely
    wallet_info = {
        "created_at": datetime.now().isoformat(),
        "public_address": public_key,
        "network": "mainnet-beta",
        "purpose": "solana_trading_bot"
    }
    
    # Save public info (safe to commit)
    with open("config/wallet_info.json", "w") as f:
        json.dump(wallet_info, f, indent=2)
    
    print("\n📁 Setting up secure configuration...")
    
    # Check if .env exists and backup
    if os.path.exists(".env"):
        backup_path = backup_dir / f".env_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(".env", backup_path)
        print(f"✅ Backed up existing .env to {backup_path}")
    
    # Update .env file
    env_lines = []
    
    # Read existing .env if it exists
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if not line.strip().startswith("WALLET_PRIVATE_KEY") and not line.strip().startswith("WALLET_PUBLIC_ADDRESS"):
                    env_lines.append(line)
    
    # Add new wallet private key (as JSON array for now)
    env_lines.append(f"\n# Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    env_lines.append(f"# Private key as byte array - import into Phantom wallet\n")
    env_lines.append(f"WALLET_PRIVATE_KEY={json.dumps(private_key_list)}\n")
    env_lines.append(f"WALLET_PUBLIC_ADDRESS={public_key}\n")
    
    # Write updated .env
    with open(".env", "w") as f:
        f.writelines(env_lines)
    
    print("✅ Updated .env file with new wallet")
    
    # Create .env.example (safe to commit)
    example_lines = [
        "# Solana Trading Bot Environment Variables\n",
        "# Copy this file to .env and fill in your values\n\n",
        "# Wallet Configuration\n",
        "WALLET_PRIVATE_KEY=your_wallet_private_key_here\n",
        f"WALLET_PUBLIC_ADDRESS={public_key}\n\n",
        "# API Keys\n",
        "HELIUS_API_KEY=your_helius_api_key_here\n",
        "BIRDEYE_API_KEY=your_birdeye_api_key_here\n",
        "DEXSCREENER_API_KEY=your_dexscreener_api_key_here\n\n",
        "# Network\n",
        "SOLANA_RPC_URL=https://api.mainnet-beta.solana.com\n"
    ]
    
    with open(".env.example", "w") as f:
        f.writelines(example_lines)
    
    print("✅ Created .env.example file (safe to commit)")
    
    # Update .gitignore
    gitignore_entries = [
        "\n# Private keys and sensitive data\n",
        ".env\n",
        ".env.local\n",
        ".env.*.local\n",
        "wallet_backup/\n",
        "*_private_key*\n",
        "*_secret*\n",
        "\n# Database\n",
        "*.db\n",
        "*.sqlite\n",
        "*.sqlite3\n",
        "data/db/\n",
        "\n# Logs\n",
        "logs/\n",
        "*.log\n",
        "\n# Python\n",
        "__pycache__/\n",
        "*.pyc\n",
        "venv/\n",
        ".venv/\n",
        "env/\n",
        "\n# Models and reports\n",
        "data/models/\n",
        "*.pkl\n",
        "*_report_*.json\n",
        "*_backup_*.json\n",
        "\n# IDE\n",
        ".vscode/\n",
        ".idea/\n",
        "*.swp\n",
        "*.swo\n",
        "\n# OS\n",
        ".DS_Store\n",
        "Thumbs.db\n",
        "\n# Trading specific\n",
        "performance_report*.json\n",
        "optimization_report*.json\n",
        "wallet_balance*.json\n",
        "trade_history_export.csv\n",
        "data/safety_state.json\n"
    ]
    
    # Read existing gitignore
    existing_lines = []
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            existing_lines = f.readlines()
    
    # Write comprehensive gitignore
    with open(".gitignore", "w") as f:
        # If gitignore was empty or very small, write all entries
        if len(existing_lines) < 10:
            for entry in gitignore_entries:
                f.write(entry)
        else:
            # Otherwise append only new entries
            f.writelines(existing_lines)
            existing_content = ''.join(existing_lines)
            for entry in gitignore_entries:
                if entry.strip() and entry.strip() not in existing_content:
                    f.write(entry)
    
    print("✅ Updated .gitignore file")
    
    # Update bot configuration files
    config_files = [
        "config/bot_control.json",
        "config/bot_control_real.json"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                
                # Update wallet address
                if "real_wallet_address" in config:
                    config["real_wallet_address"] = public_key
                
                # Update starting balance for new wallet
                if "starting_balance" in config:
                    config["starting_balance"] = 0.0
                
                with open(config_file, "w") as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated {config_file}")
            except Exception as e:
                print(f"⚠️  Could not update {config_file}: {e}")
    
    # Create security documentation
    security_doc = f"""# Wallet Security Information

## Public Wallet Address (Safe to Share)
`{public_key}`

## Security Checklist
- [ ] Private key saved securely
- [ ] .env file verified in .gitignore
- [ ] No private keys in config files
- [ ] Backup created in wallet_backup/
- [ ] Verified files before committing to GitHub

## GitHub Safety Commands
```bash
# Before committing, always check:
git status
git diff --staged

# Safe files to commit:
git add .gitignore .env.example config/wallet_info.json WALLET_SECURITY.md
git add config/bot_control*.json

# NEVER commit:
# - .env
# - wallet_backup/
# - Any file with private keys
```

## Import Private Key to Phantom Wallet
1. Open your .env file
2. Copy the WALLET_PRIVATE_KEY array [x, x, x...]
3. Use a tool to convert the byte array to base58 format
4. Or use the bot directly (it reads the array format)

## Funding Instructions
1. Send test amount: 0.01 SOL
2. Verify arrival at: `{public_key}`
3. Send trading amount: 0.5-1 SOL

## Bot Safety Configuration
- Max position: 0.02 SOL
- Max positions: 3
- Daily loss limit: 3%
- ML confidence: 80%
"""
    
    with open("WALLET_SECURITY.md", "w") as f:
        f.write(security_doc)
    
    print("✅ Created WALLET_SECURITY.md")
    
    # Save private key to secure backup
    private_key_backup = backup_dir / f"wallet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(private_key_backup, "w") as f:
        backup_data = {
            "wallet_address": public_key,
            "private_key_array": private_key_list,
            "created": datetime.now().isoformat(),
            "network": "mainnet-beta",
            "note": "Import this array into your Solana wallet app"
        }
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Wallet backup saved to: {private_key_backup}")
    
    # Create Phantom import helper
    phantom_helper = f"""#!/usr/bin/env python3
# Helper to show private key for Phantom import

import json
import os

with open('.env', 'r') as f:
    for line in f:
        if line.startswith('WALLET_PRIVATE_KEY='):
            # Extract the JSON array
            key_str = line.split('=', 1)[1].strip()
            key_array = json.loads(key_str)
            
            print("Your private key array for Phantom Wallet:")
            print("=" * 60)
            print(json.dumps(key_array))
            print("=" * 60)
            print("\\nTo import to Phantom:")
            print("1. Copy the array above")
            print("2. Go to Phantom > Settings > Security & Privacy")
            print("3. Show Secret Recovery Phrase")
            print("4. Import using private key option")
            break
"""
    
    with open("show_private_key.py", "w") as f:
        f.write(phantom_helper)
    
    # Final instructions
    print("\n" + "=" * 60)
    print("🎉 WALLET SETUP COMPLETE!")
    print("=" * 60)
    
    print(f"\n📋 Your new wallet address:")
    print(f"   {public_key}")
    
    print("\n🔐 Your private key has been saved to:")
    print(f"   .env (as byte array)")
    print(f"   {private_key_backup}")
    
    print("\n📝 Next steps:")
    print("1. Run: python show_private_key.py (to see your private key)")
    print("2. Import private key to Phantom Wallet")
    print("3. Fund wallet with 0.5-1 SOL")
    print("4. Commit safe files to GitHub:")
    print("   git add .gitignore .env.example config/ WALLET_SECURITY.md")
    print("   git commit -m 'Add secure wallet configuration'")
    print("   git push")
    
    print("\n✅ Your wallet is ready for secure trading!")

if __name__ == "__main__":
    create_secure_wallet()
