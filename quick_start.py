#!/usr/bin/env python3
"""
Quick Start Script for Solana Trading Bot
"""
import subprocess
import sys
import os

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    
    print("="*60)
    print(f"STARTING SOLANA TRADING BOT - {mode.upper()} MODE")
    print("="*60)
    
    # Check for required files
    if not os.path.exists('data/safety_state.json'):
        print("[!] Running setup first...")
        subprocess.run([sys.executable, 'bot_setup_fix.py'])
    
    # Start the bot
    print("\n[LAUNCH] Starting bot...")
    subprocess.run([sys.executable, 'start_enhanced_bot.py', mode])

if __name__ == "__main__":
    main()
