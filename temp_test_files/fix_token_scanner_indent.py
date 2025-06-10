# fix_token_scanner_indent.py
"""
Fix the indentation error in token_scanner.py
"""
import os
import re

def fix_token_scanner():
    """Fix indentation in token_scanner.py"""
    file_path = "core/data/token_scanner.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return False
        
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic scan_for_tokens method
    # It seems the method was inserted without proper class context
    
    # First, let's check if there's a class definition
    if 'class TokenScanner' not in content:
        print("Error: TokenScanner class not found in file!")
        return False
    
    # Remove any standalone scan_for_tokens method that's not properly indented
    # This regex finds scan_for_tokens at the beginning of a line (wrong indentation)
    content = re.sub(r'^async def scan_for_tokens\(self\):', '    async def scan_for_tokens(self):', content, flags=re.MULTILINE)
    
    # Also fix the method body if it exists
    lines = content.split('\n')
    fixed_lines = []
    in_scan_method = False
    class_indent_level = 0
    
    for i, line in enumerate(lines):
        # Detect class definition
        if 'class TokenScanner' in line:
            class_indent_level = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
            
        # Detect our scan_for_tokens method
        if 'async def scan_for_tokens(self):' in line and not line.strip().startswith('#'):
            # Ensure it's properly indented as a class method
            proper_indent = ' ' * (class_indent_level + 4)
            fixed_lines.append(f'{proper_indent}async def scan_for_tokens(self):')
            in_scan_method = True
            continue
            
        # If we're in the scan_for_tokens method, ensure proper indentation
        if in_scan_method:
            if line.strip() and not line.startswith(' '):
                # This line should be indented
                fixed_lines.append(' ' * (class_indent_level + 8) + line.strip())
            elif 'async def' in line or 'def ' in line:
                # We've hit another method, stop fixing indentation
                in_scan_method = False
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    # Backup the current file
    backup_path = f"{file_path}.backup_indent"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup: {backup_path}")
    
    # Write the fixed file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed indentation in {file_path}")
    return True

def verify_fix():
    """Try to import the fixed module"""
    try:
        from core.data.token_scanner import TokenScanner
        print("✅ TokenScanner imports successfully!")
        return True
    except IndentationError as e:
        print(f"❌ Still has indentation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

if __name__ == "__main__":
    print("Fixing TokenScanner indentation issue...")
    
    if fix_token_scanner():
        print("\nVerifying fix...")
        if verify_fix():
            print("\n✅ TokenScanner is fixed! Run the verification script again.")
        else:
            print("\n❌ Fix didn't work. You may need to manually edit the file.")
            print("\nTo manually fix:")
            print("1. Open core/data/token_scanner.py")
            print("2. Find the 'async def scan_for_tokens(self):' line")
            print("3. Make sure it's indented with 4 spaces (as a class method)")
            print("4. Make sure all code inside the method is indented with 8 spaces")
    else:
        print("Failed to fix the file.")