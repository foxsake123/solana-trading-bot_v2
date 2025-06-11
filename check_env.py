# check_env.py

import os
from dotenv import load_dotenv

print("--- Running Environment Check ---")

# Attempt to load the .env file from the current directory
load_success = load_dotenv()

if load_success:
    print("SUCCESS: .env file was found and loaded.")
else:
    print("WARNING: .env file not found. Make sure it's in the same directory as this script.")

# Now, let's check the specific variables
print("\n--- Checking Variables ---")

private_key = os.getenv('WALLET_PRIVATE_KEY')
rpc_url = os.getenv('SOLANA_RPC_URL')

print(f"WALLET_PRIVATE_KEY: {private_key}")
print(f"SOLANA_RPC_URL: {rpc_url}")

print("\n--- Analysis ---")
if private_key:
    print("✅ Private key loaded successfully.")
else:
    print("❌ ERROR: Private key is 'None'. Check for typos in your .env file or the variable name 'WALLET_PRIVATE_KEY'.")

if rpc_url:
    print("✅ RPC URL loaded successfully.")
else:
    print("❌ ERROR: RPC URL is 'None'.")