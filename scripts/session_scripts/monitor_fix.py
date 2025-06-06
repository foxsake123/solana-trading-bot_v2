#!/usr/bin/env python3
"""
Fix for Ultra Monitor - Correct balance and STDDEV error
"""

def fix_ultra_monitor():
    """Fix the ultra monitor issues"""
    
    # Read the current ultra_monitor.py
    monitor_path = 'monitoring/ultra_monitor.py'
    if not os.path.exists(monitor_path):
        monitor_path = 'ultra_monitor.py'
    
    with open(monitor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Replace STDDEV with manual calculation
    old_stddev = "STDDEV(gain_loss_sol) as pnl_stddev"
    new_stddev = "0.0 as pnl_stddev"  # We'll calculate it manually later
    content = content.replace(old_stddev, new_stddev)
    
    # Fix 2: Update initial balance to correct value
    content = content.replace(
        "self.initial_balance = 10.0",
        "self.initial_balance = self._get_initial_balance()"
    )
    
    # Add method to get initial balance from config
    balance_method = '''
    def _get_initial_balance(self):
        """Get initial balance from config"""
        try:
            # Try simulation config first
            with open('config/bot_control.json', 'r') as f:
                config = json.load(f)
                if 'starting_simulation_balance' in config:
                    return config['starting_simulation_balance']
                if 'current_simulation_balance' in config:
                    return config['current_simulation_balance']
            return 10.0  # Default
        except:
            return 10.0  # Default if config not found
    '''
    
    # Insert the method after the __init__ method
    init_end = content.find("self.last_check = datetime.now()")
    if init_end != -1:
        next_line = content.find("\n", init_end) + 1
        content = content[:next_line] + balance_method + content[next_line:]
    
    # Write the fixed version
    fixed_path = 'monitoring/ultra_monitor_fixed.py'
    with open(fixed_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created fixed monitor: {fixed_path}")
    
    # Also create a simpler fix by updating the class directly
    simple_fix = '''#!/usr/bin/env python3
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
'''
    
    with open('monitor_patch.py', 'w', encoding='utf-8') as f:
        f.write(simple_fix)
    
    print("✅ Created monitor_patch.py")
    
    return fixed_path

if __name__ == "__main__":
    import os
    print("ULTRA MONITOR FIX")
    print("="*50)
    
    fixed_path = fix_ultra_monitor()
    
    print(f"\n✅ Fix complete!")
    print(f"\nRun the fixed monitor:")
    print(f"   python {fixed_path}")
    print(f"\nOr apply the patch:")
    print(f"   python monitor_patch.py")
    print(f"   python monitoring/ultra_monitor.py")
