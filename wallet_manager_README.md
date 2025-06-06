# Solana Wallet Management Tools

## Prerequisites

1. Install required libraries:
```bash
pip install solana
```

2. Prepare your wallet JSON file (`config/trading_wallet.json`):
```json
{
    "privateKey": [list of private key bytes],
    "publicKey": "your_wallet_public_key"
}
```

## Wallet Manager CLI Usage

### Check Balance
```bash
python wallet_interaction_cli.py --balance
# Optional: specify network
python wallet_interaction_cli.py --balance --network devnet
```

### Transfer Funds
```bash
python wallet_interaction_cli.py --transfer RECIPIENT_ADDRESS 0.1
# Optional: add memo
python wallet_interaction_cli.py --transfer RECIPIENT_ADDRESS 0.1 --memo "Trading bot transfer"
```

### View Transactions
```bash
# View last 10 transactions (default)
python wallet_interaction_cli.py --transactions

# View last 20 transactions
python wallet_interaction_cli.py --transactions 20
```

### Export Wallet
```bash
# Export to default location
python wallet_interaction_cli.py --export

# Export to custom path
python wallet_interaction_cli.py --export config/wallet_backup_2.json
```

### Get Phantom Import Instructions
```bash
python wallet_interaction_cli.py --import-instructions config/trading_wallet.json
```

## Security Notes

🚨 CRITICAL SECURITY WARNINGS 🚨
1. NEVER share your private key
2. Store wallet JSON files securely
3. Use file permissions to restrict access
4. Consider encrypting sensitive wallet files

## Troubleshooting

- Ensure correct network selection
- Verify wallet JSON file path and format
- Check Solana network connectivity
- Confirm wallet has sufficient SOL for transaction fees

## Recommended Workflow

1. Create a secure, dedicated wallet for trading
2. Keep minimal balance for trading
3. Regularly transfer profits to a cold storage wallet
4. Use devnet for testing before mainnet transactions
