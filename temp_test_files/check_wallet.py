#!/usr/bin/env python3
"""Check wallet configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

wallet = os.getenv('WALLET_PUBLIC_ADDRESS')
private = os.getenv('WALLET_PRIVATE_KEY')

print("🔍 Wallet Configuration Check")
print("=" * 50)
print(f"Wallet Address: {wallet}")
print(f"Private Key: {'✅ Configured' if private and private != 'REPLACE_WITH_YOUR_PRIVATE_KEY' else '❌ NOT SET'}")
print("=" * 50)

if wallet:
    print(f"\n📊 Check your balance at:")
    print(f"https://solscan.io/account/{wallet}")
