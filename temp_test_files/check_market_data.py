# check_market_data.py
"""
Check what's in market_data.py and verify it has all required classes
"""
import os

def check_market_data():
    """Check the content of market_data.py"""
    file_path = "core/data/market_data.py"
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found!")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Checking market_data.py content...")
    print("=" * 60)
    
    # Check for required classes
    required_classes = ['BirdeyeAPI', 'DexScreenerAPI', 'MarketDataAggregator']
    found_classes = []
    missing_classes = []
    
    for class_name in required_classes:
        if f'class {class_name}' in content:
            found_classes.append(class_name)
            print(f"✅ Found class: {class_name}")
        else:
            missing_classes.append(class_name)
            print(f"❌ Missing class: {class_name}")
    
    print("=" * 60)
    
    # Show file stats
    lines = content.split('\n')
    print(f"\nFile stats:")
    print(f"  Total lines: {len(lines)}")
    print(f"  File size: {len(content)} bytes")
    
    # Check if it's the old version
    if 'MarketDataAggregator' not in content:
        print("\n⚠️ Your market_data.py is missing the MarketDataAggregator class!")
        print("This means you have an older version of the file.")
        print("\nYou need to:")
        print("1. Copy the complete content from the 'Final Fixed market_data.py' artifact")
        print("2. Replace your entire core/data/market_data.py file with it")
        
        # Show what the file currently starts with
        print("\nYour file currently starts with:")
        print("-" * 40)
        for i, line in enumerate(lines[:10]):
            print(f"{i+1}: {line}")
        print("-" * 40)
        
        return False
    
    return True

def create_simple_test():
    """Create a simple test script"""
    test_content = '''# test_market_data_simple.py
"""
Simple test to verify market_data.py has all required components
"""
try:
    from core.data.market_data import BirdeyeAPI
    print("✅ BirdeyeAPI imported successfully")
except ImportError as e:
    print(f"❌ Failed to import BirdeyeAPI: {e}")

try:
    from core.data.market_data import DexScreenerAPI
    print("✅ DexScreenerAPI imported successfully")
except ImportError as e:
    print(f"❌ Failed to import DexScreenerAPI: {e}")

try:
    from core.data.market_data import MarketDataAggregator
    print("✅ MarketDataAggregator imported successfully")
except ImportError as e:
    print(f"❌ Failed to import MarketDataAggregator: {e}")

print("\\nIf all three show ✅, your market_data.py is correct!")
'''
    
    with open('test_market_data_simple.py', 'w') as f:
        f.write(test_content)
    
    print("\nCreated test_market_data_simple.py")
    print("Run it with: python test_market_data_simple.py")

if __name__ == "__main__":
    if check_market_data():
        print("\n✅ Your market_data.py appears to be complete!")
    else:
        print("\n❌ Your market_data.py needs to be updated!")
        
    create_simple_test()