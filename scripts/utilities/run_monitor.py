#!/usr/bin/env python3
"""
Simple wrapper to run monitor with correct mode
"""
import os
import sys
import subprocess

def run_monitor(mode='simulation'):
    """Run monitor with specified mode"""
    
    if mode.lower() == 'real':
        # Set environment variable for real mode
        os.environ['TRADING_MODE'] = 'real'
        os.environ['INITIAL_BALANCE'] = '1.0014'
        print("Starting monitor in REAL mode (1.0014 SOL)")
    else:
        # Set environment variable for simulation
        os.environ['TRADING_MODE'] = 'simulation'
        os.environ['INITIAL_BALANCE'] = '9.05'
        print("Starting monitor in SIMULATION mode (9.05 SOL)")
    
    # Run the monitor
    subprocess.run([sys.executable, 'monitoring/ultra_monitor.py'])

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'simulation'
    run_monitor(mode)
