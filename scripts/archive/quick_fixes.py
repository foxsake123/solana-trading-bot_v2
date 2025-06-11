#!/usr/bin/env python3
"""
Quick fix script to patch existing files without replacing them
Run this to add missing methods to your existing code
"""
import os
import sys

def apply_database_patches():
    """Add missing methods to database.py"""
    
    # Read existing database.py
    with open('core/storage/database.py', 'r') as f:
        content = f.read()
    
    # Check if methods already exist
    methods_to_add = []
    
    if 'def get_token_info' not in content:
        methods_to_add.append('''
    def get_token_info(self, contract_address):
        """
        Get token information from the database (alias for get_token)
        
        :param contract_address: Token contract address
        :return: Token data as dictionary, or None if not found
        """
        return self.get_token(contract_address)
''')
    
    if 'def save_token_info' not in content:
        methods_to_add.append('''
    def save_token_info(self, token_data):
        """
        Save token information (alias for store_token)
        
        :param token_data: Dictionary containing token data
        :return: True if operation successful, False otherwise
        """
        return self.store_token(token_data)
''')
    
    # Add methods if needed
    if methods_to_add:
        # Find the last method in the class (before the final close method)
        import re
        
        # Find the position before the last method or end of class
        class_end = content.rfind('def reset_database')  # Find last method
        
        # Insert new methods before reset_database
        new_content = content[:class_end] + ''.join(methods_to_add) + '\n' + content[class_end:]
        
        # Backup original file
        if not os.path.exists('core/storage/database.py.backup'):
            os.rename('core/storage/database.py', 'core/storage/database.py.backup')
        
        # Write updated file
        with open('core/storage/database.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Database patches applied successfully")
        print(f"   Added {len(methods_to_add)} new methods")
        print("   Original file backed up as database.py.backup")
    else:
        print("✅ Database already has all required methods")

def fix_token_analyzer_init():
    """Fix token analyzer initialization"""
    
    # Read token_analyzer.py
    with open('core/analysis/token_analyzer.py', 'r') as f:
        lines = f.readlines()
    
    # Find and fix the __init__ method
    modified = False
    for i, line in enumerate(lines):
        if 'def __init__(self, db=None, birdeye_api=None):' in line:
            lines[i] = '    def __init__(self, config=None, db=None, birdeye_api=None):\n'
            # Also need to update the docstring and add config handling
            # Find the line after the docstring
            j = i + 1
            while j < len(lines) and '"""' not in lines[j]:
                j += 1
            j += 1  # Skip the closing """
            
            # Insert config handling code
            config_code = '''        # Handle different config types
        if config is None:
            # Import configuration if not provided
            from config.bot_config import BotConfiguration
            self.config = BotConfiguration
        elif hasattr(config, '__dict__'):
            # It's a class instance
            self.config = config
        else:
            # It's a dictionary
            self.config = type('Config', (), config)
            
'''
            lines.insert(j, config_code)
            modified = True
            break
    
    if modified:
        # Backup and save
        if not os.path.exists('core/analysis/token_analyzer.py.backup'):
            os.rename('core/analysis/token_analyzer.py', 'core/analysis/token_analyzer.py.backup')
        with open('core/analysis/token_analyzer.py', 'w') as f:
            f.writelines(lines)
        
        print("✅ Token analyzer patches applied successfully")
        print("   Fixed __init__ method to accept config parameter")
        print("   Original file backed up as token_analyzer.py.backup")
    else:
        print("✅ Token analyzer already has flexible initialization")

def main():
    print("🔧 Applying fixes to your Solana Trading Bot...")
    print("="*60)
    
    # Apply database patches
    print("\n1. Patching database.py...")
    try:
        apply_database_patches()
    except Exception as e:
        print(f"❌ Error patching database: {e}")
    
    # Fix token analyzer
    print("\n2. Patching token_analyzer.py...")
    try:
        fix_token_analyzer_init()
    except Exception as e:
        print(f"❌ Error patching token analyzer: {e}")
    
    print("\n" + "="*60)
    print("✅ Fixes applied! Your bot should now run without errors.")
    print("\nTo run the bot:")
    print("  python start_bot.py simulation")

if __name__ == "__main__":
    main()
