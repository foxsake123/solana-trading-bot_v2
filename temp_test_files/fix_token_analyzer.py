# fix_token_analyzer.py
"""
Add the missing analyze method to TokenAnalyzer
"""
import os

def fix_token_analyzer():
    """Add analyze method to TokenAnalyzer"""
    
    # The analyze method to add
    analyze_method = '''
    async def analyze(self, token_data: Dict) -> Dict:
        """
        Analyze a token and return analysis results
        
        :param token_data: Token data dictionary
        :return: Analysis results with score
        """
        try:
            # Basic token metrics
            price_change = token_data.get('price_change_24h', 0)
            volume = token_data.get('volume_24h', 0)
            liquidity = token_data.get('liquidity', 0)
            market_cap = token_data.get('market_cap', 0)
            
            # Calculate base score
            score = 0.5  # Start neutral
            
            # Price momentum scoring
            if price_change > 20:
                score += 0.2
            elif price_change > 10:
                score += 0.1
            elif price_change < -20:
                score -= 0.2
                
            # Volume scoring
            if volume > 1000000:  # $1M+ volume
                score += 0.2
            elif volume > 100000:  # $100k+ volume
                score += 0.1
            elif volume < 10000:  # Low volume
                score -= 0.2
                
            # Liquidity scoring
            if liquidity > 500000:  # $500k+ liquidity
                score += 0.1
            elif liquidity < 50000:  # Low liquidity
                score -= 0.1
                
            # Ensure score is between 0 and 1
            score = max(0, min(1, score))
            
            # Get ML prediction if available
            ml_score = score  # Default to base score
            if hasattr(self, 'ml_predictor') and self.ml_predictor:
                try:
                    prediction = self.ml_predictor.predict_token(token_data)
                    if prediction:
                        ml_score = prediction.get('probability', score)
                except Exception as e:
                    logger.debug(f"ML prediction failed: {e}")
            
            # Combine scores
            final_score = (score * 0.6 + ml_score * 0.4)
            
            return {
                'score': final_score,
                'price_change_24h': price_change,
                'volume_24h': volume,
                'liquidity': liquidity,
                'market_cap': market_cap,
                'recommendation': 'BUY' if final_score > 0.7 else 'HOLD' if final_score > 0.4 else 'SKIP',
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing token: {e}")
            return {
                'score': 0,
                'error': str(e),
                'recommendation': 'SKIP'
            }
'''
    
    # Read the current file
    file_path = "core/analysis/token_analyzer.py"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if analyze method already exists
    if 'async def analyze' in content:
        print("analyze method already exists in TokenAnalyzer")
        return True
        
    # Find the class definition and add the method
    import re
    
    # Find the last method in the class
    class_pattern = r'class TokenAnalyzer[^:]*:\s*"""[^"]*"""'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if not class_match:
        print("Could not find TokenAnalyzer class")
        return False
    
    # Add necessary imports at the top if missing
    if 'from datetime import datetime' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import') or line.startswith('from'):
                continue
            else:
                lines.insert(i, 'from datetime import datetime')
                break
        content = '\n'.join(lines)
    
    # Find a good place to insert the analyze method
    # Look for the end of __init__ or another method
    init_pattern = r'def __init__[^:]*:(?:\n(?:[ \t]+.*|\s*\n))*'
    init_match = re.search(init_pattern, content)
    
    if init_match:
        # Insert after __init__
        insert_pos = init_match.end()
        content = content[:insert_pos] + '\n' + analyze_method + content[insert_pos:]
    else:
        # Just add it to the end of the class
        content = content.rstrip() + '\n' + analyze_method
    
    # Backup and write
    backup_path = f"{file_path}.backup_analyze"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Added analyze method to {file_path}")
    return True

def fix_enhanced_bot():
    """Fix the scanner variable issue in enhanced_trading_bot.py"""
    file_path = "enhanced_trading_bot.py"
    
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the scanner variable issue
    # The problem is 'scanner' is used before it's defined as a parameter
    # Change the problematic line
    old_line = "if hasattr(scanner, 'birdeye_api') and not scanner.birdeye_api:"
    new_line = "if hasattr(token_scanner, 'birdeye_api') and not token_scanner.birdeye_api:"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Also fix the next line
        content = content.replace(
            "scanner.birdeye_api = BirdeyeAPI",
            "token_scanner.birdeye_api = BirdeyeAPI"
        )
        
        # Backup and write
        backup_path = f"{file_path}.backup_scanner"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed scanner variable issue in {file_path}")
        return True
    else:
        print("Scanner issue not found or already fixed")
        return False

if __name__ == "__main__":
    print("Fixing bot issues...")
    print("=" * 50)
    
    # Fix TokenAnalyzer
    print("\n1. Fixing TokenAnalyzer...")
    if fix_token_analyzer():
        print("   SUCCESS: TokenAnalyzer fixed")
    else:
        print("   FAILED: Could not fix TokenAnalyzer")
    
    # Fix Enhanced Bot
    print("\n2. Fixing EnhancedTradingBot...")
    if fix_enhanced_bot():
        print("   SUCCESS: EnhancedTradingBot fixed")
    else:
        print("   FAILED: Could not fix EnhancedTradingBot")
    
    print("\n" + "=" * 50)
    print("Run 'python verify_bot_integration.py' again to test")