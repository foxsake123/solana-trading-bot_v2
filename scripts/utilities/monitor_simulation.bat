@echo off
set TRADING_MODE=simulation  
set INITIAL_BALANCE=9.05
echo Starting monitor in SIMULATION mode (9.05 SOL)
python monitoring/ultra_monitor.py
