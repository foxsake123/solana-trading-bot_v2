# fix_safety_state.py
"""
Fix the safety manager JSON error
"""
import os
import json

def fix_safety_state():
    """Fix or create the safety state file"""
    
    # Common locations for the safety state file
    possible_paths = [
        "data/safety_state.json",
        "safety_state.json",
        "config/safety_state.json",
        "data/db/safety_state.json"
    ]
    
    # Check each possible location
    found_files = []
    for path in possible_paths:
        if os.path.exists(path):
            found_files.append(path)
            print(f"Found safety state file: {path}")
    
    # If no files found, create the default one
    if not found_files:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        path = "data/safety_state.json"
        print(f"No safety state file found. Creating new one at: {path}")
    else:
        # Fix the existing files
        for path in found_files:
            print(f"\nChecking {path}...")
            
            # Try to read the file
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    
                if not content.strip():
                    print(f"  File is empty. Fixing...")
                else:
                    try:
                        data = json.loads(content)
                        print(f"  File is valid JSON with {len(data)} keys")
                        continue
                    except json.JSONDecodeError:
                        print(f"  File has invalid JSON. Fixing...")
                        
            except Exception as e:
                print(f"  Error reading file: {e}")
    
    # Create default safety state
    default_state = {
        "daily_loss_limit": 0.1,  # 10% daily loss limit
        "max_position_size": 0.05,  # 5% max position
        "emergency_stop": False,
        "trades_today": 0,
        "loss_today": 0.0,
        "last_reset": "2025-06-10T00:00:00",
        "simulation_mode": True,
        "blocked_tokens": [],
        "circuit_breaker_triggered": False
    }
    
    # Write to all found files or create new one
    if found_files:
        for path in found_files:
            with open(path, 'w') as f:
                json.dump(default_state, f, indent=2)
            print(f"✅ Fixed {path}")
    else:
        path = "data/safety_state.json"
        with open(path, 'w') as f:
            json.dump(default_state, f, indent=2)
        print(f"✅ Created {path}")

def check_all_json_files():
    """Check all JSON files in the project"""
    print("\nChecking all JSON files...")
    print("=" * 60)
    
    for root, dirs, files in os.walk("."):
        # Skip venv and git directories
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                    if not content.strip():
                        print(f"❌ EMPTY: {filepath}")
                    else:
                        try:
                            json.loads(content)
                            # print(f"✅ Valid: {filepath}")
                        except json.JSONDecodeError as e:
                            print(f"❌ INVALID: {filepath} - {e}")
                            
                except Exception as e:
                    print(f"❌ ERROR: {filepath} - {e}")

if __name__ == "__main__":
    print("Fixing Safety Manager JSON Error")
    print("=" * 60)
    
    fix_safety_state()
    check_all_json_files()
    
    print("\n" + "=" * 60)
    print("Fix complete! Try running the bot again:")
    print("python start_bot.py simulation")