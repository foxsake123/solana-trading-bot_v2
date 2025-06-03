#!/usr/bin/env python3
"""
Export important project data for future reference
"""
import json
import sqlite3
import os
from datetime import datetime
import pandas as pd

def export_configuration():
    """Export current configuration files"""
    print("Exporting configuration files...")
    
    configs = {
        'bot_control': 'config/bot_control.json',
        'trading_params': 'config/trading_params.json'
    }
    
    exported = {}
    for name, path in configs.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                exported[name] = json.load(f)
    
    # Save consolidated config
    with open('project_config_export.json', 'w') as f:
        json.dump(exported, f, indent=2)
    
    print("✅ Configuration exported to project_config_export.json")
    return exported

def export_trade_history():
    """Export trade history and performance metrics"""
    print("\nExporting trade history...")
    
    db_path = 'data/db/sol_bot.db'
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return None
    
    conn = sqlite3.connect(db_path)
    
    # Export trades
    trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", conn)
    if not trades_df.empty:
        trades_df.to_csv('trade_history_export.csv', index=False)
        print(f"✅ Exported {len(trades_df)} trades to trade_history_export.csv")
    
    # Export tokens
    tokens_df = pd.read_sql_query("SELECT * FROM tokens", conn)
    if not tokens_df.empty:
        tokens_df.to_csv('tokens_export.csv', index=False)
        print(f"✅ Exported {len(tokens_df)} tokens to tokens_export.csv")
    
    # Calculate summary statistics
    if not trades_df.empty:
        summary = {
            'total_trades': len(trades_df),
            'total_buys': len(trades_df[trades_df['action'] == 'BUY']),
            'total_sells': len(trades_df[trades_df['action'] == 'SELL']),
            'unique_tokens': trades_df['contract_address'].nunique(),
            'date_range': {
                'first_trade': trades_df['timestamp'].min(),
                'last_trade': trades_df['timestamp'].max()
            }
        }
        
        # Calculate P&L for sells
        sells = trades_df[trades_df['action'] == 'SELL']
        if not sells.empty and 'gain_loss_sol' in sells.columns:
            summary['performance'] = {
                'total_sells': len(sells),
                'profitable_sells': len(sells[sells['gain_loss_sol'] > 0]),
                'total_pnl': sells['gain_loss_sol'].sum(),
                'avg_gain': sells[sells['gain_loss_sol'] > 0]['gain_loss_sol'].mean() if len(sells[sells['gain_loss_sol'] > 0]) > 0 else 0,
                'avg_loss': sells[sells['gain_loss_sol'] < 0]['gain_loss_sol'].mean() if len(sells[sells['gain_loss_sol'] < 0]) > 0 else 0,
                'best_trade': sells['gain_loss_sol'].max() if not sells.empty else 0,
                'worst_trade': sells['gain_loss_sol'].min() if not sells.empty else 0
            }
    else:
        summary = {'message': 'No trades found'}
    
    conn.close()
    
    # Save summary
    with open('trading_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Trading summary exported to trading_summary.json")
    return summary

def create_project_archive():
    """Create a project information archive"""
    print("\nCreating project archive...")
    
    archive = {
        'project': 'Solana Trading Bot v2',
        'export_date': datetime.now().isoformat(),
        'environment': {
            'python_version': '3.13',
            'main_packages': [
                'solana',
                'pandas',
                'scikit-learn',
                'aiohttp',
                'sqlite3'
            ]
        },
        'bot_status': {
            'mode': 'simulation',
            'working_components': [
                'Token scanning',
                'Token analysis',
                'Trade execution',
                'Position monitoring',
                'Performance tracking'
            ],
            'ml_status': 'Collecting training data',
            'issues_resolved': [
                'Database schema mismatch',
                'Missing get_token_info method',
                'TokenAnalyzer initialization',
                'is_simulation parameter error'
            ]
        },
        'file_structure': {
            'config': ['bot_control.json', 'trading_params.json', 'bot_config.py'],
            'core': ['trading_bot.py', 'token_analyzer.py', 'database.py', 'solana_client.py'],
            'monitoring': ['working_monitor.py', 'performance_tracker.py'],
            'ml': ['ml_predictor.py', 'ml_enhancement_strategy.py'],
            'data': ['sol_bot.db', 'ml_model.pkl (when trained)']
        }
    }
    
    with open('project_archive.json', 'w') as f:
        json.dump(archive, f, indent=2)
    
    print("✅ Project archive created: project_archive.json")

def main():
    """Export all project data"""
    print("="*60)
    print("SOLANA TRADING BOT - PROJECT DATA EXPORT")
    print("="*60)
    
    # Export configurations
    config = export_configuration()
    
    # Export trade history
    summary = export_trade_history()
    
    # Create project archive
    create_project_archive()
    
    print("\n" + "="*60)
    print("EXPORT COMPLETE!")
    print("="*60)
    print("\nFiles created:")
    print("1. project_config_export.json - Current bot configuration")
    print("2. trade_history_export.csv - All trades")
    print("3. tokens_export.csv - All analyzed tokens")
    print("4. trading_summary.json - Performance summary")
    print("5. project_archive.json - Project information")
    print("\nAttach these files to your Claude project for future reference.")
    
    # Display quick summary
    if summary and 'performance' in summary:
        print(f"\nQuick Performance Summary:")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total P&L: {summary['performance']['total_pnl']:.4f} SOL")
        print(f"Win Rate: {summary['performance']['profitable_sells'] / summary['performance']['total_sells'] * 100:.1f}%" if summary['performance']['total_sells'] > 0 else "No sells yet")

if __name__ == "__main__":
    main()