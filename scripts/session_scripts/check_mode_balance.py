#!/usr/bin/env python3
"""
Check current mode and display correct balance
"""
import json
import os
from colorama import init, Fore, Style
import sqlite3

init()

def check_current_mode():
    """Check which mode the bot is running in"""
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🔍 CHECKING BOT MODE AND BALANCE{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Check simulation config
    print(f"{Fore.CYAN}1. SIMULATION CONFIG (bot_control.json):{Style.RESET_ALL}")
    try:
        with open('config/bot_control.json', 'r') as f:
            sim_config = json.load(f)
        print(f"   Mode: {'SIMULATION' if sim_config.get('simulation_mode', True) else 'REAL'}")
        print(f"   Balance: {sim_config.get('starting_simulation_balance', 'Not set')} SOL")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check real config
    print(f"\n{Fore.CYAN}2. REAL CONFIG (bot_control_real.json):{Style.RESET_ALL}")
    try:
        with open('config/bot_control_real.json', 'r') as f:
            real_config = json.load(f)
        print(f"   Mode: {'SIMULATION' if real_config.get('simulation_mode', True) else 'REAL'}")
        print(f"   Balance: {real_config.get('starting_balance', 'Not set')} SOL")
        print(f"   Wallet: {real_config.get('real_wallet_address', 'Not set')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check database to see what's actually happening
    print(f"\n{Fore.CYAN}3. DATABASE ACTIVITY:{Style.RESET_ALL}")
    try:
        conn = sqlite3.connect('data/db/sol_bot.db')
        cursor = conn.cursor()
        
        # Get recent trades
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp) 
            FROM trades 
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        count, last_trade = cursor.fetchone()
        print(f"   Recent trades (last hour): {count}")
        print(f"   Last trade: {last_trade}")
        
        # Check wallet addresses in trades
        cursor.execute("""
            SELECT DISTINCT tx_hash 
            FROM trades 
            WHERE tx_hash IS NOT NULL 
            AND tx_hash != 'simulated'
            LIMIT 1
        """)
        real_tx = cursor.fetchone()
        
        if real_tx:
            print(f"   {Fore.GREEN}Real transactions found!{Style.RESET_ALL}")
        else:
            print(f"   {Fore.YELLOW}Only simulated transactions found{Style.RESET_ALL}")
        
        conn.close()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Show how to start in each mode
    print(f"\n{Fore.CYAN}HOW TO START:{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}For SIMULATION mode (9.05 SOL):{Style.RESET_ALL}")
    print("   python start_bot.py simulation")
    print("   Monitor will show: 9.05 SOL starting balance")
    
    print(f"\n{Fore.YELLOW}For REAL mode (1.0014 SOL):{Style.RESET_ALL}")
    print("   python start_bot.py real --config config/bot_control_real.json")
    print("   Monitor will show: 1.0014 SOL starting balance")
    
    # Important note
    print(f"\n{Fore.RED}⚠️  IMPORTANT:{Style.RESET_ALL}")
    print("The monitor shows balance based on which mode the BOT is running in,")
    print("not which config file you're looking at.")
    print("\nIf you want to see your real wallet balance in the monitor,")
    print("you need to start the bot in REAL mode.")
    
    # Safety check
    print(f"\n{Fore.CYAN}SAFETY CHECK:{Style.RESET_ALL}")
    if real_config.get('simulation_mode', True) == False:
        print(f"{Fore.GREEN}✓ Real config is set for REAL trading{Style.RESET_ALL}")
        print(f"  Starting balance: {real_config.get('starting_balance', 'Not set')} SOL")
        print(f"  Max position: {real_config.get('max_position_size_sol', 'Not set')} SOL")
    else:
        print(f"{Fore.RED}✗ Real config still in simulation mode!{Style.RESET_ALL}")
        print("  Update 'simulation_mode' to false in bot_control_real.json")

def show_monitor_explanation():
    """Explain how the monitor determines which balance to show"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📊 HOW THE MONITOR WORKS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print("The UltraMonitor reads from the DATABASE, which contains trades from")
    print("whichever mode the bot is running in:")
    
    print(f"\n{Fore.YELLOW}Simulation Mode:{Style.RESET_ALL}")
    print("- Database has simulated trades")
    print("- Starting balance: 9.05 SOL")
    print("- No real wallet connection")
    print("- Monitor shows simulation performance")
    
    print(f"\n{Fore.YELLOW}Real Mode:{Style.RESET_ALL}")
    print("- Database has real trades")
    print("- Starting balance: 1.0014 SOL")
    print("- Connected to your wallet")
    print("- Monitor shows real wallet performance")
    
    print(f"\n{Fore.GREEN}To see your real wallet in the monitor:{Style.RESET_ALL}")
    print("1. Stop the simulation bot (Ctrl+C)")
    print("2. Start in real mode:")
    print("   python start_bot.py real --config config/bot_control_real.json")
    print("3. The monitor will then show your real balance")

if __name__ == "__main__":
    check_current_mode()
    show_monitor_explanation()
    
    print(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    input()
