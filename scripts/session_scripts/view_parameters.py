#!/usr/bin/env python3
"""
View and verify all trading parameters before going live
"""
import json
import os
from datetime import datetime
from colorama import init, Fore, Style, Back

init()

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

def display_parameters():
    """Display all trading parameters"""
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔍 TRADING PARAMETERS REVIEW - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    # Load all configurations
    configs = {
        'simulation': load_json_file('config/bot_control.json'),
        'real': load_json_file('config/bot_control_real.json'),
        'trading_params': load_json_file('config/trading_params.json'),
        'partial_profit': load_json_file('config/partial_profit_config.json')
    }
    
    # 1. Real Trading Configuration
    print(f"{Fore.CYAN}📋 REAL TRADING CONFIGURATION (bot_control_real.json):{Style.RESET_ALL}")
    if configs['real']:
        real_config = configs['real']
        
        # Critical settings
        print(f"\n{Fore.YELLOW}Critical Settings:{Style.RESET_ALL}")
        print(f"  Simulation Mode: {Fore.RED if not real_config.get('simulation_mode', True) else Fore.GREEN}{real_config.get('simulation_mode', True)}{Style.RESET_ALL}")
        print(f"  Starting Balance: {real_config.get('starting_balance', 2.0)} SOL")
        print(f"  Wallet Address: {real_config.get('real_wallet_address', 'NOT SET')}")
        print(f"  ML Confidence Required: {real_config.get('ml_confidence_threshold', 0.65) * 100:.0f}%")
        
        # Safety limits
        print(f"\n{Fore.YELLOW}Safety Limits:{Style.RESET_ALL}")
        print(f"  Max Daily Loss: {real_config.get('max_daily_loss_percentage', 0.05) * 100:.0f}%")
        print(f"  Max Position Size: {real_config.get('max_position_size_sol', 0.1)} SOL")
        print(f"  Max Open Positions: {real_config.get('max_open_positions', 5)}")
        print(f"  Pause on Daily Loss: {real_config.get('pause_on_daily_loss', True)}")
        
        # Token filters
        print(f"\n{Fore.YELLOW}Token Requirements:{Style.RESET_ALL}")
        print(f"  Min Volume: ${real_config.get('MIN_VOLUME', 10000):,}")
        print(f"  Min Liquidity: ${real_config.get('MIN_LIQUIDITY', 10000):,}")
        print(f"  Min Market Cap: ${real_config.get('MIN_MCAP', 50000):,}")
        print(f"  Min Holders: {real_config.get('MIN_HOLDERS', 50)}")
        
        # Exit strategy
        print(f"\n{Fore.YELLOW}Exit Strategy:{Style.RESET_ALL}")
        print(f"  Take Profit: {(real_config.get('take_profit_target', 1.3) - 1) * 100:.0f}%")
        print(f"  Stop Loss: {real_config.get('stop_loss_percentage', 0.05) * 100:.0f}%")
        print(f"  Trailing Stop: {real_config.get('trailing_stop_enabled', True)}")
        if real_config.get('trailing_stop_enabled', True):
            print(f"    - Activation: {real_config.get('trailing_stop_percentage', 0.1) * 100:.0f}%")
    
    # 2. Trading Parameters
    print(f"\n{Fore.CYAN}📊 TRADING PARAMETERS (trading_params.json):{Style.RESET_ALL}")
    if configs['trading_params']:
        params = configs['trading_params']
        
        print(f"\n{Fore.YELLOW}Position Sizing:{Style.RESET_ALL}")
        print(f"  Default Size: {params.get('default_position_size_pct', 4.0)}% of balance")
        print(f"  Min Size: {params.get('min_position_size_pct', 3.0)}% of balance")
        print(f"  Max Size: {params.get('max_position_size_pct', 5.0)}% of balance")
        print(f"  Absolute Min: {params.get('absolute_min_sol', 0.1)} SOL")
        print(f"  Absolute Max: {params.get('absolute_max_sol', 2.0)} SOL")
        
        # With 2 SOL balance
        balance = 2.0
        default_pct = params.get('default_position_size_pct', 4.0)
        position_size = balance * (default_pct / 100)
        print(f"\n{Fore.GREEN}With 2 SOL balance:{Style.RESET_ALL}")
        print(f"  Expected position size: {position_size:.4f} SOL (${position_size * 230:.2f} at $230/SOL)")
    
    # 3. Alerts Configuration
    print(f"\n{Fore.CYAN}🔔 ALERTS CONFIGURATION:{Style.RESET_ALL}")
    if configs['real']:
        webhook = configs['real'].get('alert_webhook_url', '')
        if webhook:
            print(f"  Discord Webhook: {Fore.GREEN}Configured{Style.RESET_ALL}")
        else:
            print(f"  Discord Webhook: {Fore.YELLOW}Not configured (console only){Style.RESET_ALL}")
    
    # 4. Pre-flight Checklist
    print(f"\n{Fore.CYAN}✅ PRE-FLIGHT CHECKLIST:{Style.RESET_ALL}")
    checks = []
    
    # Check wallet
    if configs['real'] and configs['real'].get('real_wallet_address', '') != 'YOUR_WALLET_ADDRESS_HERE':
        checks.append((True, "Wallet address configured"))
    else:
        checks.append((False, "Wallet address NOT configured"))
    
    # Check simulation mode
    if configs['real'] and not configs['real'].get('simulation_mode', True):
        checks.append((True, "Real trading mode enabled"))
    else:
        checks.append((False, "Still in simulation mode"))
    
    # Check safety features
    if configs['real'] and configs['real'].get('max_daily_loss_percentage', 0) > 0:
        checks.append((True, "Daily loss limit configured"))
    else:
        checks.append((False, "No daily loss limit"))
    
    # Check ML confidence
    if configs['real'] and configs['real'].get('ml_confidence_threshold', 0) >= 0.7:
        checks.append((True, f"High ML confidence required ({configs['real'].get('ml_confidence_threshold', 0.65) * 100:.0f}%)"))
    else:
        checks.append((False, "ML confidence threshold too low"))
    
    # Display checklist
    for passed, item in checks:
        if passed:
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {item}")
        else:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {item}")
    
    # 5. Commands to start
    print(f"\n{Fore.CYAN}🚀 COMMANDS TO START:{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Test in simulation first:{Style.RESET_ALL}")
    print(f"  python start_bot.py simulation")
    
    print(f"\n{Fore.YELLOW}Start real trading:{Style.RESET_ALL}")
    print(f"  python start_bot.py real --config config/bot_control_real.json")
    
    print(f"\n{Fore.YELLOW}Monitor performance:{Style.RESET_ALL}")
    print(f"  python monitoring/ultra_monitor.py")
    
    # Warnings
    print(f"\n{Fore.RED}⚠️  WARNINGS:{Style.RESET_ALL}")
    print(f"  • Start with small amounts (currently set to max 0.1 SOL per trade)")
    print(f"  • Monitor closely for the first hour")
    print(f"  • Have a plan to stop the bot quickly if needed (Ctrl+C)")
    print(f"  • Your private key should ONLY be in .env file")

def check_wallet_monitoring():
    """Explain wallet monitoring in real mode"""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 WALLET MONITORING IN REAL MODE{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}Yes, the monitor will track your real wallet P&L!{Style.RESET_ALL}\n")
    
    print("In REAL trading mode, the monitor will show:")
    print("1. Your actual wallet balance (fetched from blockchain)")
    print("2. Real-time P&L based on actual trades")
    print("3. All trades executed on your wallet")
    print("4. Actual SOL spent and received")
    
    print("\nThe monitor tracks:")
    print("• Starting balance: 2.0 SOL (from config)")
    print("• Current balance: Live from blockchain")
    print("• Each trade: Logged in database")
    print("• Total P&L: Current - Starting balance")
    print("• Daily P&L: Resets each day")
    
    print("\nMonitoring differences:")
    print(f"{Fore.YELLOW}Simulation Mode:{Style.RESET_ALL}")
    print("  - Tracks simulated balance")
    print("  - No blockchain queries")
    print("  - Instant updates")
    
    print(f"\n{Fore.YELLOW}Real Mode:{Style.RESET_ALL}")
    print("  - Tracks actual wallet balance")
    print("  - Queries blockchain for balance")
    print("  - Shows real transaction fees")
    print("  - Includes slippage impact")
    
    print(f"\n{Fore.GREEN}The database stores all trades permanently, so you'll have a complete history!{Style.RESET_ALL}")

if __name__ == "__main__":
    display_parameters()
    check_wallet_monitoring()
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press Enter when ready to proceed...{Style.RESET_ALL}")
