#!/usr/bin/env python3
"""
CLI for Phantom Wallet Management
Provides interactive interface for wallet operations
"""

import asyncio
import argparse
from phantom_wallet_manager import PhantomWalletManager

class WalletInteractionCLI:
    def __init__(self):
        self.wallet_manager = None
    
    async def initialize(self, network='mainnet-beta'):
        """Initialize wallet manager"""
        try:
            self.wallet_manager = PhantomWalletManager(network=network)
            print(f"✅ Connected to {network} network")
        except Exception as e:
            print(f"❌ Failed to initialize wallet: {e}")
            return False
        return True
    
    async def check_balance(self):
        """Check wallet balance"""
        if not self.wallet_manager:
            await self.initialize()
        
        try:
            balance = await self.wallet_manager.get_balance()
            print(f"💰 Current Wallet Balance: {balance:.4f} SOL")
        except Exception as e:
            print(f"❌ Error checking balance: {e}")
    
    async def transfer_funds(self, recipient, amount, memo=None):
        """Transfer funds to another wallet"""
        if not self.wallet_manager:
            await self.initialize()
        
        try:
            confirm = input(f"Confirm transfer of {amount} SOL to {recipient}? (y/n): ")
            if confirm.lower() != 'y':
                print("Transfer cancelled.")
                return
            
            result = await self.wallet_manager.transfer_sol(recipient, amount, memo)
            print("✅ Transfer successful!")
            print(f"Transaction Details: {result}")
        except Exception as e:
            print(f"❌ Transfer failed: {e}")
    
    async def view_transactions(self, limit=10):
        """View recent transactions"""
        if not self.wallet_manager:
            await self.initialize()
        
        try:
            transactions = await self.wallet_manager.get_transaction_history(limit)
            print(f"🔍 Last {limit} Transactions:")
            for idx, tx in enumerate(transactions, 1):
                print(f"\nTransaction {idx}:")
                print(f"Signature: {tx.get('result', {}).get('transaction', {}).get('signatures', ['N/A'])[0]}")
                # Add more transaction details as needed
        except Exception as e:
            print(f"❌ Error retrieving transactions: {e}")
    
    async def export_wallet(self, export_path=None):
        """Export wallet securely"""
        if not self.wallet_manager:
            await self.initialize()
        
        try:
            wallet_export = self.wallet_manager.export_wallet(export_path)
            print("✅ Wallet exported successfully!")
            print(f"Public Key: {wallet_export['publicKey']}")
            print(f"Export Path: {export_path}")
        except Exception as e:
            print(f"❌ Wallet export failed: {e}")
    
    async def phantom_import_instructions(self, private_key_path):
        """Get Phantom wallet import instructions"""
        try:
            instructions = await PhantomWalletManager.import_wallet_to_phantom(private_key_path)
            print("🔑 Phantom Wallet Import Instructions:")
            for step in instructions['steps']:
                print(f"• {step}")
            print(f"\n⚠️  WARNING: {instructions['warning']}")
        except Exception as e:
            print(f"❌ Failed to generate import instructions: {e}")

def main():
    parser = argparse.ArgumentParser(description="Solana Wallet Management CLI")
    parser.add_argument('--network', choices=['mainnet-beta', 'devnet', 'testnet'], 
                        default='mainnet-beta', help='Solana network')
    parser.add_argument('--balance', action='store_true', help='Check wallet balance')
    parser.add_argument('--transfer', nargs=2, metavar=('RECIPIENT', 'AMOUNT'), 
                        help='Transfer SOL (recipient address, amount)')
    parser.add_argument('--memo', help='Optional memo for transfer', default=None)
    parser.add_argument('--transactions', type=int, default=10, 
                        help='Number of recent transactions to view')
    parser.add_argument('--export', nargs='?', const='config/wallet_backup.json', 
                        help='Export wallet (optional export path)')
    parser.add_argument('--import-instructions', help='Get Phantom import instructions')
    
    args = parser.parse_args()
    
    async def run():
        cli = WalletInteractionCLI()
        await cli.initialize(args.network)
        
        if args.balance:
            await cli.check_balance()
        
        if args.transfer:
            recipient, amount = args.transfer
            await cli.transfer_funds(recipient, float(amount), args.memo)
        
        if args.transactions:
            await cli.view_transactions(args.transactions)
        
        if args.export:
            await cli.export_wallet(args.export)
        
        if args.import_instructions:
            await cli.phantom_import_instructions(args.import_instructions)
    
    asyncio.run(run())

if __name__ == "__main__":
    main()
