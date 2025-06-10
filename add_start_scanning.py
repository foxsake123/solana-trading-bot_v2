#!/usr/bin/env python3
"""
Add start_scanning method to TokenScanner
"""
import os

def add_start_scanning_method():
    """Add the missing start_scanning method"""
    
    method_code = '''
    async def start_scanning(self):
        """Start the token scanning loop"""
        logger.info("Token scanner started - scanning every %d seconds", self.scan_interval)
        
        while True:
            try:
                # Discover new tokens
                logger.info("Scanning for new tokens...")
                
                # Get top gainers
                if hasattr(self, 'birdeye_api') and self.birdeye_api:
                    try:
                        tokens = await self.birdeye_api.get_token_list(limit=10)
                        if tokens:
                            logger.info(f"Found {len(tokens)} tokens from Birdeye")
                            
                            # Analyze each token
                            for token in tokens:
                                try:
                                    # Skip if already processing
                                    address = token.get('address', '')
                                    if not address:
                                        continue
                                    
                                    # Analyze token
                                    if self.token_analyzer:
                                        analysis = await self.token_analyzer.analyze(token)
                                        
                                        # Store in database if good
                                        if analysis.get('score', 0) > 0.5:
                                            if self.db:
                                                self.db.store_token(token)
                                            logger.info(f"Found promising token: {token.get('symbol')} (score: {analysis.get('score', 0):.2f})")
                                    
                                except Exception as e:
                                    logger.error(f"Error analyzing token: {e}")
                                    
                    except Exception as e:
                        logger.error(f"Error getting tokens: {e}")
                
                # Wait before next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                await asyncio.sleep(10)  # Wait 10 seconds on error
'''
    
    # Read token_scanner.py
    scanner_file = 'core/data/token_scanner.py'
    with open(scanner_file, 'r') as f:
        content = f.read()
    
    # Check if method already exists
    if 'async def start_scanning' in content:
        print("start_scanning method already exists")
        return
    
    # Add import for asyncio if not present
    if 'import asyncio' not in content:
        content = 'import asyncio\n' + content
    
    # Find the class definition and add method
    import re
    class_match = re.search(r'class TokenScanner[^:]*:', content)
    if class_match:
        # Find the end of __init__ method
        init_end = content.find('\n    def ', class_match.end())
        if init_end == -1:
            # No other methods, add at end of class
            insert_pos = len(content)
        else:
            insert_pos = init_end
        
        # Insert the method
        content = content[:insert_pos] + method_code + content[insert_pos:]
        
        # Save the file
        with open(scanner_file, 'w') as f:
            f.write(content)
        
        print("[OK] Added start_scanning method to TokenScanner")
    else:
        print("[ERROR] Could not find TokenScanner class")

if __name__ == "__main__":
    add_start_scanning_method()
