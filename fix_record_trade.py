#!/usr/bin/env python3
"""
Fix the is_simulation parameter error in record_trade calls
"""
import os
import re

def find_files_with_record_trade():
    """Find all Python files that might have record_trade calls"""
    files_found = []
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment
        if 'venv' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'record_trade' in content and 'is_simulation' in content:
                            files_found.append(filepath)
                except:
                    pass
    
    return files_found

def fix_record_trade_calls(filepath):
    """Remove is_simulation parameter from record_trade calls"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_path = f"{filepath}.backup_trade"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Fix the calls - remove is_simulation parameter
    # Pattern to match record_trade calls with is_simulation
    pattern = r'(\.record_trade\([^)]+?),\s*is_simulation\s*=\s*[^,\)]+([,\)])'
    
    # Replace with the call without is_simulation
    fixed_content = re.sub(pattern, r'\1\2', content)
    
    # Write back if changed
    if fixed_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        return True
    return False

def add_runtime_patch():
    """Create a runtime patch for the database"""
    patch_content = '''#!/usr/bin/env python3
"""
Runtime patch to make database.record_trade accept is_simulation parameter
Add this to your startup script
"""
import types

def patch_database_record_trade(db):
    """Patch the database to accept is_simulation parameter"""
    
    # Save original method
    original_record_trade = db.record_trade
    
    # Create new method that accepts and ignores is_simulation
    def record_trade_with_simulation(self, contract_address, action, amount, price, 
                                    tx_hash=None, gain_loss_sol=0.0, 
                                    percentage_change=0.0, price_multiple=1.0, 
                                    is_simulation=None, **kwargs):
        """Modified record_trade that accepts is_simulation parameter"""
        # Just ignore is_simulation and call original method
        return original_record_trade(
            contract_address, action, amount, price, tx_hash,
            gain_loss_sol, percentage_change, price_multiple
        )
    
    # Replace method
    db.record_trade = types.MethodType(record_trade_with_simulation, db)
    print("✅ Patched database.record_trade to accept is_simulation parameter")

# Usage: 
# from database_patch import patch_database_record_trade
# patch_database_record_trade(db)
'''
    
    with open('database_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ Created database_patch.py for runtime patching")

def main():
    print("🔧 Fixing record_trade parameter errors")
    print("="*60)
    
    # Find files with the issue
    print("\n1. Searching for files with record_trade and is_simulation...")
    files = find_files_with_record_trade()
    
    if files:
        print(f"Found {len(files)} files with potential issues:")
        for file in files:
            print(f"   - {file}")
        
        print("\n2. Fixing record_trade calls...")
        fixed_count = 0
        for file in files:
            if fix_record_trade_calls(file):
                print(f"   ✅ Fixed: {file}")
                fixed_count += 1
            else:
                print(f"   ⏭️  No changes needed: {file}")
        
        print(f"\nFixed {fixed_count} files")
    else:
        print("No files found with is_simulation in record_trade calls")
    
    # Create runtime patch as alternative
    print("\n3. Creating runtime patch as alternative...")
    add_runtime_patch()
    
    print("\n" + "="*60)
    print("✅ Complete!")
    print("\nThe error should now be fixed. If it persists, you can add this to your")
    print("startup script after initializing the database:")
    print("\n   from database_patch import patch_database_record_trade")
    print("   patch_database_record_trade(db)")

if __name__ == "__main__":
    main()
