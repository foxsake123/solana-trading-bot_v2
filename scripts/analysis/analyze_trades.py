#!/usr/bin/env python3
"""
Analyze trade history to understand performance
"""
import pandas as pd
import json
import numpy as np

def analyze_trades():
    """Detailed analysis of trading performance"""
    print("="*60)
    print("DETAILED TRADE ANALYSIS")
    print("="*60)
    
    # Load trade history
    try:
        trades_df = pd.read_csv('trade_history_export.csv')
    except:
        print("❌ Could not load trade_history_export.csv")
        return
    
    # Separate buys and sells
    buys = trades_df[trades_df['action'] == 'BUY']
    sells = trades_df[trades_df['action'] == 'SELL']
    
    print(f"\n📊 TRADE OVERVIEW:")
    print(f"Total trades: {len(trades_df)}")
    print(f"Buy orders: {len(buys)}")
    print(f"Sell orders: {len(sells)}")
    
    # Analyze sells only (completed trades)
    if 'gain_loss_sol' in sells.columns:
        profitable_sells = sells[sells['gain_loss_sol'] > 0]
        losing_sells = sells[sells['gain_loss_sol'] < 0]
        
        print(f"\n💰 PROFIT/LOSS ANALYSIS:")
        print(f"Profitable trades: {len(profitable_sells)} ({len(profitable_sells)/len(sells)*100:.1f}%)")
        print(f"Losing trades: {len(losing_sells)} ({len(losing_sells)/len(sells)*100:.1f}%)")
        print(f"Total P&L: {sells['gain_loss_sol'].sum():.4f} SOL")
        
        if len(profitable_sells) > 0:
            print(f"\n📈 WINNING TRADES:")
            print(f"Average profit: {profitable_sells['gain_loss_sol'].mean():.4f} SOL")
            print(f"Best trade: {profitable_sells['gain_loss_sol'].max():.4f} SOL")
            print(f"Average % gain: {profitable_sells['percentage_change'].mean():.1f}%")
            print(f"Best % gain: {profitable_sells['percentage_change'].max():.1f}%")
        
        if len(losing_sells) > 0:
            print(f"\n📉 LOSING TRADES:")
            print(f"Average loss: {losing_sells['gain_loss_sol'].mean():.4f} SOL")
            print(f"Worst trade: {losing_sells['gain_loss_sol'].min():.4f} SOL")
            print(f"Average % loss: {losing_sells['percentage_change'].mean():.1f}%")
            print(f"Worst % loss: {losing_sells['percentage_change'].min():.1f}%")
        
        # Calculate risk/reward ratio
        if len(profitable_sells) > 0 and len(losing_sells) > 0:
            avg_win = profitable_sells['gain_loss_sol'].mean()
            avg_loss = abs(losing_sells['gain_loss_sol'].mean())
            risk_reward = avg_win / avg_loss
            print(f"\n⚖️  RISK/REWARD RATIO: {risk_reward:.2f}:1")
            
            if risk_reward < 1:
                print("⚠️  Warning: Your average loss is bigger than average win!")
                print("   This explains the small profit despite high win rate.")
    
    # Analyze position sizes
    if 'amount' in trades_df.columns:
        print(f"\n📏 POSITION SIZING:")
        print(f"Average position size: {trades_df['amount'].mean():.4f} SOL")
        print(f"Largest position: {trades_df['amount'].max():.4f} SOL")
        print(f"Smallest position: {trades_df['amount'].min():.4f} SOL")
    
    # Timing analysis
    if 'timestamp' in trades_df.columns:
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df['hour'] = trades_df['timestamp'].dt.hour
        
        print(f"\n⏰ TIMING ANALYSIS:")
        print("Most active hours (UTC):")
        hourly_trades = trades_df.groupby('hour').size().sort_values(ascending=False).head(5)
        for hour, count in hourly_trades.items():
            print(f"  Hour {hour:02d}: {count} trades")
    
    # Token analysis
    print(f"\n🪙 TOKEN ANALYSIS:")
    unique_tokens = trades_df['contract_address'].nunique()
    print(f"Unique tokens traded: {unique_tokens}")
    
    # Find most profitable tokens
    if 'gain_loss_sol' in sells.columns:
        token_performance = sells.groupby('contract_address')['gain_loss_sol'].sum().sort_values(ascending=False)
        
        print(f"\nMost profitable tokens:")
        for token, profit in token_performance.head(5).items():
            print(f"  {token[:12]}...: {profit:.4f} SOL")
        
        print(f"\nLeast profitable tokens:")
        for token, profit in token_performance.tail(5).items():
            print(f"  {token[:12]}...: {profit:.4f} SOL")
    
    # Recommendations
    print(f"\n" + "="*60)
    print("💡 RECOMMENDATIONS BASED ON ANALYSIS:")
    print("="*60)
    
    if 'gain_loss_sol' in sells.columns and len(profitable_sells) > 0 and len(losing_sells) > 0:
        if risk_reward < 1.5:
            print("\n1. IMPROVE RISK/REWARD RATIO:")
            print("   - Increase take profit target from 15% to 20-25%")
            print("   - OR reduce stop loss from 5% to 3-4%")
            print("   - Current settings are cutting winners too early")
        
        if trades_df['amount'].mean() < 0.05:
            print("\n2. INCREASE POSITION SIZES:")
            print("   - Your average position is very small")
            print("   - With 76.7% win rate, you can afford larger positions")
            print("   - Consider increasing max_investment_per_token to 0.2-0.3 SOL")
        
        if profitable_sells['percentage_change'].max() > 100:
            print("\n3. LET WINNERS RUN:")
            print("   - You've had trades with 100%+ potential")
            print("   - Consider using trailing stop instead of fixed take profit")
            print("   - Or increase take profit to 30-50% for high momentum tokens")

if __name__ == "__main__":
    analyze_trades()
