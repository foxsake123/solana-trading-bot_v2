# configs/unified_config.py (Final Version)

import json
import os
from dotenv import load_dotenv

class Config:
    """
    A unified configuration manager for the trading bot.
    This class is instantiated once in main.py and passed to all components.
    """
    def __init__(self, mode='simulation'):
        print(f"Initializing config in '{mode}' mode...")
        self.mode = mode
        self.settings = {}
        self.load_all_configs()
        self.load_env_vars()
        print("Configuration loaded successfully.")

    def load_all_configs(self):
        """Loads and merges all JSON configuration files."""
        base_path = 'configs'
        files_to_load = [
            'trading_params.json', 'bot_control.json',
            'factor_models.json', 'MASTER_CONFIG.json'
        ]
        for file_name in files_to_load:
            file_path = os.path.join(base_path, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.settings.update(json.load(f))
                print(f"  - Loaded '{file_path}'")
        
        mode_file_path = os.path.join(base_path, f'bot_control_{self.mode}.json')
        if os.path.exists(mode_file_path):
            with open(mode_file_path, 'r') as f:
                self.settings.update(json.load(f))
            print(f"  - Overridden with mode-specific config: '{mode_file_path}'")

    def load_env_vars(self):
        """Loads environment variables from .env file into class attributes."""
        load_dotenv()
        self.birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
        self.solana_rpc_url = os.getenv('SOLANA_RPC_URL')
        self.wallet_private_key = os.getenv('WALLET_PRIVATE_KEY')

        if self.birdeye_api_key: print("  - Loaded Birdeye API key from .env")
        if self.solana_rpc_url: print("  - Loaded Solana RPC URL from .env")
        if self.wallet_private_key: print("  - Loaded Wallet Private Key from .env")

    def get(self, key, default=None):
        """Safely retrieves a configuration value from the JSON settings."""
        return self.settings.get(key, default)

    def __getitem__(self, key):
        """Allows for dictionary-style access, e.g., CONFIG['some_key']"""
        return self.settings[key]

# Note: We have removed the global "CONFIG = Config()" line from this file.