#!/usr/bin/env python3
"""
Fix monitor to detect mode and use correct balance
"""
import json
import os

def fix_ultra_monitor():
    """Fix the ultra monitor to detect mode and use correct balance"""
    
    print("FIXING ULTRA MONITOR FOR MODE DETECTION")
    print("="*50)
    
    # Create a new version of the monitor initialization
    monitor_init_fix = '''    def __init__(self, db_path='data/db/sol_bot.db'):
        self.db_path = db_path
        self.initial_balance = self._detect_initial_balance()
        self.performance_history = deque(maxlen=100)  # Track last 100 data points
        self.alerts = []
        self.last_check = datetime.now()
        print(f"Monitor initialized with balance: {self.initial_balance} SOL")
        
    def _detect_initial_balance(self):
        """Detect which mode we're in and get correct initial balance"""
        # First, check if we have a safety state file (indicates real mode)
        if os.path.exists('data/safety_state.json'):
            try:
                with open('data/safety_state.json', 'r') as f:
                    safety_state = json.load(f)
                    # If safety state exists, we might be in real mode
            except:
                pass
        
        # Check for active config by looking at recent database entries
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if we have real transactions
            cursor.execute("""
                SELECT tx_hash 
                FROM trades 
                WHERE tx_hash IS NOT NULL 
                AND tx_hash != 'simulated'
                AND timestamp > datetime('now', '-1 day')
                LIMIT 1
            """)
            
            real_tx = cursor.fetchone()
            conn.close()
            
            if real_tx:
                # We have real transactions, use real config
                try:
                    with open('config/bot_control_real.json', 'r') as f:
                        config = json.load(f)
                        balance = config.get('starting_balance', 1.0014)
                        print(f"Detected REAL mode - using balance: {balance} SOL")
                        return balance
                except:
                    return 1.0014  # Your known real balance
            
        except:
            pass
        
        # Default: Check simulation config
        try:
            with open('config/bot_control.json', 'r') as f:
                config = json.load(f)
                balance = config.get('starting_simulation_balance', 
                                   config.get('current_simulation_balance', 10.0))
                print(f"Detected SIMULATION mode - using balance: {balance} SOL")
                return balance
        except:
            return 9.05  # Your known simulation balance
'''
    
    # Read the current monitor file
    monitor_path = 'monitoring/ultra_monitor.py'
    if not os.path.exists(monitor_path):
        monitor_path = 'ultra_monitor.py'
    
    try:
        with open(monitor_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the __init__ method
        init_start = content.find('def __init__(self, db_path=')
        if init_start == -1:
            print("❌ Could not find __init__ method")
            return False
        
        # Find the end of __init__ method
        # Look for the next method definition
        next_method = content.find('\n    def ', init_start + 1)
        if next_method == -1:
            print("❌ Could not find end of __init__ method")
            return False
        
        # Replace the __init__ method
        new_content = content[:init_start] + monitor_init_fix.strip() + '\n' + content[next_method:]
        
        # Make sure we have the json import
        if 'import json' not in new_content:
            import_pos = new_content.find('import sqlite3')
            if import_pos != -1:
                new_content = new_content[:import_pos] + 'import json\n' + new_content[import_pos:]
        
        # Save the fixed version
        fixed_path = 'monitoring/ultra_monitor_mode_aware.py'
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Created mode-aware monitor: {fixed_path}")
        
        # Also create a simple environment variable approach
        create_env_approach()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_env_approach():
    """Create a simpler approach using environment variable"""
    
    simple_fix = '''#!/usr/bin/env python3
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
'''
    
    with open('run_monitor.py', 'w') as f:
        f.write(simple_fix)
    
    # Also create a batch file for Windows
    batch_real = '''@echo off
set TRADING_MODE=real
set INITIAL_BALANCE=1.0014
echo Starting monitor in REAL mode (1.0014 SOL)
python monitoring/ultra_monitor.py
'''
    
    batch_sim = '''@echo off
set TRADING_MODE=simulation  
set INITIAL_BALANCE=9.05
echo Starting monitor in SIMULATION mode (9.05 SOL)
python monitoring/ultra_monitor.py
'''
    
    with open('monitor_real.bat', 'w') as f:
        f.write(batch_real)
    
    with open('monitor_simulation.bat', 'w') as f:
        f.write(batch_sim)
    
    print("\n✅ Created helper scripts:")
    print("   - run_monitor.py - Python wrapper")
    print("   - monitor_real.bat - Windows batch for real mode")
    print("   - monitor_simulation.bat - Windows batch for simulation")

def main():
    if fix_ultra_monitor():
        print("\n" + "="*50)
        print("✅ MONITOR FIX COMPLETE")
        print("="*50)
        
        print("\nYou now have several options:")
        
        print("\n1. Use the mode-aware monitor:")
        print("   python monitoring/ultra_monitor_mode_aware.py")
        
        print("\n2. Use the wrapper script:")
        print("   python run_monitor.py real        # For real mode")
        print("   python run_monitor.py simulation  # For simulation")
        
        print("\n3. Use batch files (Windows):")
        print("   monitor_real.bat        # For real mode")
        print("   monitor_simulation.bat  # For simulation")
        
        print("\n4. Or set environment variable manually:")
        print("   set INITIAL_BALANCE=1.0014")
        print("   python monitoring/ultra_monitor.py")

if __name__ == "__main__":
    main()
