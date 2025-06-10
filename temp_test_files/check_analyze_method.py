# check_analyze_method.py
"""
Check if TokenAnalyzer has the analyze method and what methods it has
"""
import ast
import os

def check_token_analyzer():
    """Check TokenAnalyzer class methods"""
    file_path = "core/analysis/token_analyzer.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Checking {file_path}...")
    print("=" * 60)
    
    # Parse the AST to find methods
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "TokenAnalyzer":
                print(f"Found class: {node.name}")
                print("\nMethods in TokenAnalyzer:")
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        print(f"  - {item.name}")
                    elif isinstance(item, ast.AsyncFunctionDef):
                        print(f"  - async {item.name}")
                        
                # Check specifically for analyze
                method_names = [item.name for item in node.body 
                              if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                if 'analyze' not in method_names:
                    print("\n❌ 'analyze' method NOT found!")
                else:
                    print("\n✅ 'analyze' method found!")
                    
    except Exception as e:
        print(f"Error parsing file: {e}")
        print("\nTrying simple text search...")
        
        # Fallback to text search
        if 'def analyze' in content or 'async def analyze' in content:
            print("✅ Found 'analyze' method via text search")
        else:
            print("❌ No 'analyze' method found via text search")
    
    # Show the first few lines of the class
    print("\nFirst 50 lines of TokenAnalyzer class:")
    print("-" * 40)
    lines = content.split('\n')
    in_class = False
    line_count = 0
    
    for i, line in enumerate(lines):
        if 'class TokenAnalyzer' in line:
            in_class = True
        
        if in_class:
            print(f"{i+1:4d}: {line}")
            line_count += 1
            
            if line_count > 50:
                break

def create_minimal_analyzer():
    """Create a minimal working TokenAnalyzer if needed"""
    
    minimal_analyzer = '''# minimal_token_analyzer.py
"""
Minimal TokenAnalyzer implementation for testing
"""
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class TokenAnalyzer:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.ml_predictor = None
        logger.info("TokenAnalyzer initialized")
    
    async def analyze(self, token_data: Dict) -> Dict:
        """Analyze a token and return analysis results"""
        try:
            # Basic scoring based on metrics
            score = 0.5
            
            # Price momentum
            price_change = token_data.get('price_change_24h', 0)
            if price_change > 20:
                score += 0.2
            elif price_change > 10:
                score += 0.1
            elif price_change < -20:
                score -= 0.2
            
            # Volume
            volume = token_data.get('volume_24h', 0)
            if volume > 1000000:
                score += 0.2
            elif volume > 100000:
                score += 0.1
            elif volume < 10000:
                score -= 0.1
            
            # Liquidity
            liquidity = token_data.get('liquidity', 0)
            if liquidity > 500000:
                score += 0.1
            elif liquidity < 50000:
                score -= 0.1
            
            # Ensure score is between 0 and 1
            score = max(0, min(1, score))
            
            return {
                'score': score,
                'price_change_24h': price_change,
                'volume_24h': volume,
                'liquidity': liquidity,
                'recommendation': 'BUY' if score > 0.7 else 'HOLD' if score > 0.4 else 'SKIP'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing token: {e}")
            return {'score': 0, 'error': str(e)}
'''
    
    with open('minimal_token_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(minimal_analyzer)
    
    print("\nCreated minimal_token_analyzer.py")
    print("You can copy the analyze method from this file to your TokenAnalyzer class")

if __name__ == "__main__":
    check_token_analyzer()
    print("\n" + "=" * 60)
    create_minimal_analyzer()