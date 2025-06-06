#!/usr/bin/env python3
"""
Solana Wallet Balance Checker
Shows SOL balance and all token holdings with USD values
"""
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional
from colorama import init, Fore, Style, Back
import os

# Initialize colorama
init()

class WalletBalanceChecker:
    def __init__(self, wallet_address: str = None):
        # Load wallet address from .env if not provided
        if wallet_address is None:
            from dotenv import load_dotenv
            load_dotenv()
            wallet_address = os.getenv('WALLET_PUBLIC_ADDRESS')
            if not wallet_address:
                wallet_address = "16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf"  # Fallback
        
        self.wallet_address = wallet_address
        self.helius_api_key = os.getenv('HELIUS_API_KEY', '')
        self.birdeye_api_key = os.getenv('BIRDEYE_API_KEY', '')
        
    async def get_sol_balance(self) -> float:
        """Get SOL balance using Solana RPC"""
        url = "https://api.mainnet-beta.solana.com"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [self.wallet_address]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if 'result' in data:
                    # Balance is in lamports, convert to SOL
                    return data['result']['value'] / 1e9
                return 0
    
    async def get_token_accounts(self) -> List[Dict]:
        """Get all token accounts for the wallet"""
        url = "https://api.mainnet-beta.solana.com"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                self.wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                if 'result' in data:
                    return data['result']['value']
                return []
    
    async def get_token_prices_dexscreener(self, mint_addresses: List[str]) -> Dict[str, Dict]:
        """Get token prices from DexScreener"""
        prices = {}
        
        # DexScreener API endpoint
        base_url = "https://api.dexscreener.com/latest/dex/tokens/"
        
        async with aiohttp.ClientSession() as session:
            # Process in batches of 30 (API limit)
            for i in range(0, len(mint_addresses), 30):
                batch = mint_addresses[i:i+30]
                addresses = ','.join(batch)
                
                try:
                    async with session.get(f"{base_url}{addresses}") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for pair in data.get('pairs', []):
                                token_addr = pair.get('baseToken', {}).get('address')
                                if token_addr and pair.get('priceUsd'):
                                    prices[token_addr] = {
                                        'price': float(pair['priceUsd']),
                                        'symbol': pair['baseToken'].get('symbol', 'Unknown'),
                                        'name': pair['baseToken'].get('name', 'Unknown'),
                                        'liquidity': pair.get('liquidity', {}).get('usd', 0),
                                        'volume24h': pair.get('volume', {}).get('h24', 0),
                                        'priceChange24h': pair.get('priceChange', {}).get('h24', 0)
                                    }
                except Exception as e:
                    print(f"Error fetching prices for batch: {e}")
                
                # Rate limit
                await asyncio.sleep(0.5)
        
        return prices
    
    async def get_token_metadata(self, mint_address: str) -> Optional[Dict]:
        """Get token metadata from Solana"""
        # This is simplified - in production, you'd use Metaplex
        # For now, return basic info
        return {
            'symbol': 'Unknown',
            'name': 'Unknown Token',
            'decimals': 9
        }
    
    async def get_sol_price(self) -> float:
        """Get current SOL price in USD"""
        try:
            async with aiohttp.ClientSession() as session:
                # Using CoinGecko API
                url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('solana', {}).get('usd', 0)
        except:
            pass
        
        # Fallback to approximate price
        return 240.0  # Update this with current SOL price
    
    async def check_complete_balance(self):
        """Check complete wallet balance including all tokens"""
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔍 SOLANA WALLET BALANCE CHECKER{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        print(f"Wallet Address: {Fore.WHITE}{self.wallet_address}{Style.RESET_ALL}")
        print(f"Checking Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Get SOL balance
        print(f"{Fore.CYAN}Fetching SOL balance...{Style.RESET_ALL}")
        sol_balance = await self.get_sol_balance()
        sol_price = await self.get_sol_price()
        sol_value = sol_balance * sol_price
        
        print(f"\n{Fore.GREEN}✅ SOL Balance:{Style.RESET_ALL}")
        print(f"   Amount: {sol_balance:.4f} SOL")
        print(f"   Price: ${sol_price:.2f}")
        print(f"   Value: ${sol_value:.2f}\n")
        
        # Get token accounts
        print(f"{Fore.CYAN}Fetching token accounts...{Style.RESET_ALL}")
        token_accounts = await self.get_token_accounts()
        
        if not token_accounts:
            print(f"{Fore.YELLOW}No SPL tokens found in wallet{Style.RESET_ALL}")
            total_value = sol_value
        else:
            print(f"Found {len(token_accounts)} token accounts\n")
            
            # Extract token details
            tokens = []
            mint_addresses = []
            
            for account in token_accounts:
                parsed_info = account['account']['data']['parsed']['info']
                mint = parsed_info['mint']
                token_amount = parsed_info['tokenAmount']
                
                # Only include tokens with balance
                if float(token_amount['uiAmount']) > 0:
                    tokens.append({
                        'mint': mint,
                        'amount': float(token_amount['uiAmount']),
                        'decimals': token_amount['decimals']
                    })
                    mint_addresses.append(mint)
            
            # Get token prices
            print(f"{Fore.CYAN}Fetching token prices...{Style.RESET_ALL}\n")
            token_prices = await self.get_token_prices_dexscreener(mint_addresses)
            
            # Display token holdings
            print(f"{Fore.GREEN}📊 TOKEN HOLDINGS:{Style.RESET_ALL}")
            print(f"{'─'*80}")
            print(f"{'Token':<15} {'Amount':>15} {'Price':>12} {'Value':>12} {'24h %':>8}")
            print(f"{'─'*80}")
            
            total_token_value = 0
            token_details = []
            
            for token in tokens:
                mint = token['mint']
                amount = token['amount']
                
                if mint in token_prices:
                    price_info = token_prices[mint]
                    price = price_info['price']
                    value = amount * price
                    total_token_value += value
                    
                    symbol = price_info['symbol'][:12]
                    change_24h = price_info.get('priceChange24h', 0)
                    
                    # Color code price change
                    if change_24h > 0:
                        change_color = Fore.GREEN
                    elif change_24h < 0:
                        change_color = Fore.RED
                    else:
                        change_color = Fore.WHITE
                    
                    print(f"{symbol:<15} {amount:>15.4f} ${price:>11.6f} ${value:>11.2f} "
                          f"{change_color}{change_24h:>7.1f}%{Style.RESET_ALL}")
                    
                    token_details.append({
                        'symbol': symbol,
                        'amount': amount,
                        'price': price,
                        'value': value,
                        'change_24h': change_24h,
                        'mint': mint
                    })
                else:
                    # Unknown token
                    print(f"{mint[:8]+'...':<15} {amount:>15.4f} {'Unknown':>12} {'Unknown':>12} {'N/A':>8}")
            
            print(f"{'─'*80}")
            print(f"{'Total Token Value:':>45} ${total_token_value:>11.2f}\n")
            
            # Portfolio summary
            total_value = sol_value + total_token_value
            
            print(f"{Fore.CYAN}💼 PORTFOLIO SUMMARY:{Style.RESET_ALL}")
            print(f"{'─'*50}")
            print(f"SOL Value:        ${sol_value:>10.2f} ({sol_value/total_value*100:>5.1f}%)")
            print(f"Token Value:      ${total_token_value:>10.2f} ({total_token_value/total_value*100:>5.1f}%)")
            print(f"{'─'*50}")
            print(f"{Fore.GREEN}TOTAL PORTFOLIO:  ${total_value:>10.2f}{Style.RESET_ALL}")
            
            # Top holdings
            if token_details:
                print(f"\n{Fore.CYAN}🏆 TOP HOLDINGS BY VALUE:{Style.RESET_ALL}")
                sorted_tokens = sorted(token_details, key=lambda x: x['value'], reverse=True)[:5]
                
                for i, token in enumerate(sorted_tokens, 1):
                    percentage = (token['value'] / total_value) * 100
                    print(f"{i}. {token['symbol']}: ${token['value']:.2f} ({percentage:.1f}% of portfolio)")
        
        # Trading bot positions check
        print(f"\n{Fore.CYAN}🤖 TRADING BOT CHECK:{Style.RESET_ALL}")
        print(f"{'─'*50}")
        
        # Check if any tokens match recent trades
        try:
            # Check for bot's trade history
            if os.path.exists('data/db/sol_bot.db'):
                import sqlite3
                conn = sqlite3.connect('data/db/sol_bot.db')
                cursor = conn.cursor()
                
                # Get recent open positions
                cursor.execute("""
                    SELECT DISTINCT contract_address
                    FROM trades
                    WHERE action = 'BUY'
                    AND contract_address NOT IN (
                        SELECT contract_address 
                        FROM trades 
                        WHERE action = 'SELL'
                    )
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                
                open_positions = cursor.fetchall()
                
                if open_positions:
                    print("Bot's open positions found in wallet:")
                    for pos in open_positions:
                        contract = pos[0]
                        if contract in [t['mint'] for t in token_details]:
                            matching_token = next(t for t in token_details if t['mint'] == contract)
                            print(f"✅ {matching_token['symbol']}: ${matching_token['value']:.2f}")
                else:
                    print("No open bot positions detected")
                
                conn.close()
        except Exception as e:
            print(f"Could not check bot positions: {e}")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'wallet_address': self.wallet_address,
            'sol_balance': sol_balance,
            'sol_price': sol_price,
            'sol_value': sol_value,
            'tokens': token_details if 'token_details' in locals() else [],
            'total_token_value': total_token_value if 'total_token_value' in locals() else 0,
            'total_portfolio_value': total_value if 'total_value' in locals() else sol_value
        }
        
        filename = f"wallet_balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Fore.GREEN}✅ Report saved to: {filename}{Style.RESET_ALL}")
        
        # Quick links
        print(f"\n{Fore.CYAN}🔗 QUICK LINKS:{Style.RESET_ALL}")
        print(f"Solscan: https://solscan.io/account/{self.wallet_address}")
        print(f"Birdeye: https://birdeye.so/profile/{self.wallet_address}")
        print(f"SolanaFM: https://solana.fm/address/{self.wallet_address}")

async def main():
    """Run the wallet balance checker"""
    # You can pass a different wallet address here if needed
    checker = WalletBalanceChecker()
    
    print(f"{Fore.YELLOW}Checking wallet balance...{Style.RESET_ALL}\n")
    
    try:
        await checker.check_complete_balance()
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        print("\nTry checking your wallet on:")
        print(f"https://solscan.io/account/{checker.wallet_address}")

if __name__ == "__main__":
    asyncio.run(main())
