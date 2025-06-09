#!/usr/bin/env python3
"""
Quick script to move citadel_barra_strategy.py to strategies folder
"""

import shutil
from pathlib import Path

# Move citadel_barra_strategy.py if it exists in root
source = Path("citadel_barra_strategy.py")
dest = Path("strategies/citadel_barra_strategy.py")

if source.exists():
    dest.parent.mkdir(exist_ok=True)
    shutil.move(str(source), str(dest))
    print(f"✓ Moved citadel_barra_strategy.py to strategies/")
else:
    print("✗ citadel_barra_strategy.py not found in root")

# Check if enhanced_monitor.py exists
if Path("enhanced_monitor.py").exists():
    shutil.move("enhanced_monitor.py", "monitoring/enhanced_monitor.py")
    print("✓ Moved enhanced_monitor.py to monitoring/")
elif Path("monitoring/enhanced_monitor.py").exists():
    print("✓ enhanced_monitor.py already in monitoring/")
else:
    print("✗ enhanced_monitor.py not found")

print("\nCreating missing scripts...")

# Create real_trading_setup.py in scripts/
Path("scripts").mkdir(exist_ok=True)

# Save the real trading setup from earlier
with open("scripts/real_trading_setup.py", "w") as f:
    f.write(open("real_trading_setup.py").read() if Path("real_trading_setup.py").exists() else "# Placeholder")
    
# Create EMERGENCY_STOP.py
emergency_stop = '''#!/usr/bin/env python3
"""EMERGENCY STOP - Immediately halt all trading"""
import json

print("🚨 EMERGENCY STOP ACTIVATED 🚨")

with open('config/bot_control.json', 'r') as f:
    config = json.load(f)

config['running'] = False
config['emergency_stop'] = True

with open('config/bot_control.json', 'w') as f:
    json.dump(config, f, indent=4)

print("✓ Bot stopped")
print("✓ Check positions manually")
'''

with open("scripts/EMERGENCY_STOP.py", "w") as f:
    f.write(emergency_stop)
    
print("✓ Created scripts/EMERGENCY_STOP.py")
print("\nAll files organized!")
