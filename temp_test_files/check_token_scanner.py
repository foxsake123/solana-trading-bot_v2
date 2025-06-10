# check_token_scanner.py
"""
Display the content around the error in token_scanner.py
"""
import os

def check_token_scanner():
    """Display content of token_scanner.py around line 4"""
    file_path = "core/data/token_scanner.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines in file: {len(lines)}")
    print("\nContent around line 4 (showing lines 1-20):")
    print("=" * 60)
    
    for i, line in enumerate(lines[:20], 1):
        # Show the line number and content
        # Use arrows to highlight line 4
        marker = ">>>" if i == 4 else "   "
        print(f"{marker} {i:3d}: {line}", end='')
    
    print("=" * 60)
    
    # Check for indentation issues
    print("\nChecking for indentation issues...")
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            # Check if it's a valid top-level statement
            if not any(line.startswith(x) for x in ['import ', 'from ', 'class ', 'def ', '#', '"""', "'''", '@']):
                if 'async def scan_for_tokens' in line:
                    print(f"Found problematic line {i}: {line.strip()}")
                    print("This async def should be indented as a class method!")

if __name__ == "__main__":
    check_token_scanner()