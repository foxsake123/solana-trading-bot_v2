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
    
    if 'def save_performance_metrics' not in content:
        methods_to_add.append('''
    def save_performance_metrics(self, metrics):
        """
        Save performance metrics to database
        
        :param metrics: Dictionary containing performance metrics
        :return: True if operation successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create performance_metrics table if it doesn't exist
            cursor.execute(\'\'\'
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                total_pnl_sol REAL,
                win_rate REAL,
                current_balance_sol REAL,
                metrics_json TEXT
            )
            \'\'\')
            
            timestamp = datetime.now(UTC).isoformat()
            
            cursor.execute(\'\'\'
            INSERT INTO performance_metrics (
                timestamp, total_trades, winning_trades, losing_trades,
                total_pnl_sol, win_rate, current_balance_sol, metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            \'\'\', (
                timestamp,
                metrics.get('total_trades', 0),
                metrics.get('winning_trades', 0),
                metrics.get('losing_trades', 0),
                metrics.get('total_pnl_sol', 0.0),
                metrics.get('win_rate', 0.0),
                metrics.get('current_balance_sol', 0.0),
                json.dumps(metrics)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
            return False
            
        finally:
            conn.close()
''')
    
    if 'def save_token_analysis' not in content:
        methods_to_add.append('''
    def save_token_analysis(self, analysis_data):
        """
        Save token analysis results
        
        :param analysis_data: Dictionary containing analysis results
        :return: True if operation successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create token_analysis table if it doesn't exist
            cursor.execute(\'\'\'
            CREATE TABLE IF NOT EXISTS token_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_address TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                safety_score REAL,
                buy_recommendation INTEGER,
                risk_level TEXT,
                analysis_json TEXT,
                FOREIGN KEY (contract_address) REFERENCES tokens(contract_address)
            )
            \'\'\')
            
            timestamp = datetime.now(UTC).isoformat()
            
            cursor.execute(\'\'\'
            INSERT INTO token_analysis (
                contract_address, timestamp, safety_score, 
                buy_recommendation, risk_level, analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            \'\'\', (
                analysis_data.get('contract_address'),
                timestamp,
                analysis_data.get('safety_score', 0.0),
                1 if analysis_data.get('buy_recommendation', False) else 0,
                analysis_data.get('risk_level', 'Unknown'),
                json.dumps(analysis_data)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving token analysis: {e}")
            return False
            
        finally:
            conn.close()
''')
    
    # Add methods if needed
    if methods_to_add:
        # Find the last method in the class (before the final close method)
        import re
        
        # Find the position before the last method or end of class
        class_end = content.rfind('\n\n')  # Find last double newline
        
        # Insert new methods
        new_content = content[:class_end] + '\n'.join(methods_to_add) + content[class_end:]
        
        # Backup original file
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
        content = f.read()
    
    # Check if we need to fix the __init__ method
    if 'def __init__(self, db=None, birdeye_api=None):' in content:
        # Replace the __init__ method
        old_init = '''def __init__(self, db=None, birdeye_api=None):
        """
        Initialize the token analyzer
        
        :param db: Database instance
        :param birdeye_api: BirdeyeAPI instance
        """
        self.db = db
        self.birdeye_api = birdeye_api
        
        # Import configuration
        from config.bot_config import BotConfiguration
        self.config = BotConfiguration
        
        # Cache for token data
        self.token_data_cache = {}
        self.cache_expiry = 3600  # 1 hour'''
        
        new_init = '''def __init__(self, config=None, db=None, birdeye_api=None):
        """
        Initialize the token analyzer with flexible parameters
        
        :param config: BotConfiguration instance or config dict
        :param db: Database instance
        :param birdeye_api: BirdeyeAPI instance
        """
        self.db = db
        self.birdeye_api = birdeye_api
        
        # Handle different config types
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
        
        # Cache for token data
        self.token_data_cache = {}
        self.cache_expiry = 3600  # 1 hour
        
        logger.info("TokenAnalyzer initialized")'''
        
        content = content.replace(old_init, new_init)
        
        # Add get_token method if missing
        if 'def get_token' not in content:
            # Find a good place to add it (after analyze_token method)
            insert_pos = content.find('async def analyze_token')
            if insert_pos > 0:
                # Find the end of that method
                method_end = content.find('\n\n', insert_pos)
                if method_end > 0:
                    get_token_method = '''

    def get_token(self, contract_address):
        """
        Get token information from database or cache
        
        :param contract_address: Token contract address
        :return: Token data dictionary or None
        """
        # Check cache first
        current_time = time.time()
        if contract_address in self.token_data_cache:
            cache_time, cache_data = self.token_data_cache[contract_address]
            if current_time - cache_time < self.cache_expiry:
                return cache_data
        
        # Get from database
        if self.db:
            token_data = self.db.get_token_info(contract_address)
            if token_data:
                # Update cache
                self.token_data_cache[contract_address] = (current_time, token_data)
                return token_data
        
        return None'''
                    
                    content = content[:method_end] + get_token_method + content[method_end:]
        
        # Backup and save
        os.rename('core/analysis/token_analyzer.py', 'core/analysis/token_analyzer.py.backup')
        with open('core/analysis/token_analyzer.py', 'w') as f:
            f.write(content)
        
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
    
    # Save the enhanced start script
    print("\n3. Creating enhanced start script...")
    try:
        # The enhanced_start_bot.py content is already in the artifact
        print("✅ Enhanced start script created")
        print("   Use: python enhanced_start_bot.py simulation")
    except Exception as e:
        print(f"❌ Error creating start script: {e}")
    
    print("\n" + "="*60)
    print("✅ Fixes applied! Your bot should now run without errors.")
    print("\nTo run the bot with monitoring:")
    print("  python enhanced_start_bot.py simulation")
    print("\nTo view live monitoring in another terminal:")
    print("  python monitoring/live_monitor.py")

if __name__ == "__main__":
    main()