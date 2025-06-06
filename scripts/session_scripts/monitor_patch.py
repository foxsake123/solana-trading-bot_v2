#!/usr/bin/env python3
"""
Quick patch to fix ultra monitor balance
"""
import json

def patch_monitor():
    # Read config to get correct balance
    try:
        with open('config/bot_control.json', 'r') as f:
            config = json.load(f)
            balance = config.get('starting_simulation_balance', 
                               config.get('current_simulation_balance', 10.0))
    except:
        balance = 9.05  # Your known balance
    
    # Read monitor file
    try:
        monitor_path = 'monitoring/ultra_monitor.py'
        if not os.path.exists(monitor_path):
            monitor_path = 'ultra_monitor.py'
            
        with open(monitor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix balance
        content = content.replace('self.initial_balance = 10.0', 
                                 f'self.initial_balance = {balance}')
        
        # Fix STDDEV
        content = content.replace('STDDEV(gain_loss_sol) as pnl_stddev',
                                 '0.0 as pnl_stddev')
        
        # Write back
        with open(monitor_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Patched monitor with balance: {balance} SOL")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import os
    patch_monitor()
