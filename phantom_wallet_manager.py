#!/usr/bin/env python3
"""
Phantom Wallet Manager for Solana Trading Bot
Provides methods to interact with Phantom wallet
"""

import os
import json
from typing import Dict, Optional
from solana.rpc.async_api import AsyncClient
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.rpc.commitment import Confirmed

class PhantomWalletManager:
    def __init__(self, 
                 wallet_path: str = 'config/trading_wallet.json', 
                 network: str = 'mainnet-beta'):
        """
        Initialize Phantom Wallet Manager
        
        Args:
            wallet_path (str): Path to wallet JSON file
            network (str): Solana network ('mainnet-beta', 'devnet', 'testnet')
        """
        self.wallet_path = wallet_path
        self.network_urls = {
            'mainnet-beta': 'https://api.mainnet-beta.solana.com',
            'devnet': 'https://api.devnet.solana.com',
            'testnet': 'https://api.testnet.solana.com'
        }
        self.client = AsyncClient(self.network_urls[network])
        self.keypair = self._load_wallet()
    
    def _load_wallet(self) -> Keypair:
        """
        Load wallet from JSON file
        
        Returns:
            Keypair: Solana wallet keypair
        """
        if not os.path.exists(self.wallet_path):
            raise FileNotFoundError(f"Wallet file not found at {self.wallet_path}")
        
        with open(self.wallet_path, 'r') as f:
            wallet_data = json.load(f)
        
        # Assume wallet data is stored as a list of integers representing private key
        private_key = bytes(wallet_data['privateKey'])
        return Keypair.from_secret_key(private_key)
    
    async def get_balance(self) -> float:
        """
        Get wallet balance in SOL
        
        Returns:
            float: Current wallet balance in SOL
        """
        balance_response = await self.client.get_balance(self.keypair.pubkey())
        lamports = balance_response['result']['value']
        return lamports / 10**9  # Convert lamports to SOL
    
    async def transfer_sol(self, 
                            recipient_address: str, 
                            amount: float, 
                            memo: Optional[str] = None) -> Dict:
        """
        Transfer SOL to another wallet
        
        Args:
            recipient_address (str): Destination wallet address
            amount (float): Amount of SOL to transfer
            memo (str, optional): Transaction memo
        
        Returns:
            Dict: Transaction result
        """
        # Convert SOL to lamports
        lamports = int(amount * 10**9)
        
        # Create transaction
        transaction = Transaction().add(
            Transaction.transfer(
                Transaction.get_transfer_instruction(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=PublicKey(recipient_address),
                    lamports=lamports
                )
            )
        )
        
        # Add memo if provided
        if memo:
            transaction.add(
                Transaction.memo(memo)
            )
        
        # Sign and send transaction
        try:
            result = await self.client.send_transaction(
                transaction, 
                self.keypair,
                opts={"preflightCommitment": Confirmed}
            )
            return result
        except Exception as e:
            print(f"Transfer failed: {e}")
            return {"error": str(e)}
    
    async def get_transaction_history(self, 
                                      limit: int = 10, 
                                      before: Optional[str] = None) -> list:
        """
        Retrieve recent transaction history
        
        Args:
            limit (int): Number of transactions to retrieve
            before (str, optional): Transaction signature to start before
        
        Returns:
            list: Recent transactions
        """
        signatures = await self.client.get_signatures_for_address(
            self.keypair.pubkey(), 
            limit=limit,
            before=before
        )
        
        # Fetch full transaction details
        transactions = []
        for sig in signatures['result']:
            tx_details = await self.client.get_transaction(sig['signature'])
            transactions.append(tx_details)
        
        return transactions
    
    def export_wallet(self, export_path: Optional[str] = None):
        """
        Export wallet private key securely
        
        Args:
            export_path (str, optional): Path to export wallet JSON
        
        Returns:
            Dict: Wallet export information
        """
        if not export_path:
            export_path = 'config/wallet_backup.json'
        
        wallet_export = {
            'publicKey': str(self.keypair.pubkey()),
            'privateKey': list(self.keypair.secret_key),
            'exportedAt': datetime.now().isoformat()
        }
        
        # Secure file permissions
        with open(export_path, 'w') as f:
            json.dump(wallet_export, f)
        os.chmod(export_path, 0o600)  # Read/write for owner only
        
        return wallet_export
    
    @classmethod
    async def import_wallet_to_phantom(cls, private_key_path: str):
        """
        Generate instructions for importing wallet to Phantom
        
        Args:
            private_key_path (str): Path to wallet private key JSON
        
        Returns:
            Dict: Import instructions
        """
        # Load private key
        with open(private_key_path, 'r') as f:
            wallet_data = json.load(f)
        
        return {
            "method": "Import to Phantom Wallet",
            "steps": [
                "Open Phantom Wallet",
                "Click 'Add/Connect Wallet'",
                "Select 'Import Private Key'",
                f"Public Key to verify: {wallet_data['publicKey']}"
            ],
            "warning": "NEVER share your private key with anyone!"
        }

async def main():
    # Example usage
    wallet_manager = PhantomWalletManager()
    
    # Get balance
    balance = await wallet_manager.get_balance()
    print(f"Current Balance: {balance} SOL")
    
    # Example transfer (commented out for safety)
    # await wallet_manager.transfer_sol(
    #     recipient_address='RECIPIENT_WALLET_ADDRESS', 
    #     amount=0.1, 
    #     memo='Trading bot transfer'
    # )
    
    # Get transaction history
    transactions = await wallet_manager.get_transaction_history()
    for tx in transactions:
        print(json.dumps(tx, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
