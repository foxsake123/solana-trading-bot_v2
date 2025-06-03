# Solana Trading Bot v2

## Current Status (June 3, 2025)
- [x] Bot is functional and trading in simulation mode
- [x] Fixed balance tracking issue (was showing 0.05 SOL instead of actual balance)
- [x] Position sizing now works correctly (3-5% of balance)
- [x] ML model trained with 95.83% accuracy
- [x] Win rate: ~76% on 1000+ trades

## Quick Start
```bash
# Activate virtual environment
.\venv\Scripts\Activate  # Windows
source venv/bin/activate   # Linux/Mac

# Start bot in simulation mode
python start_bot.py simulation

# Monitor performance
python scripts/monitoring/enhanced_monitor.py

# Adjust position sizes
python scripts/utilities/adjust_positions.py
```

## Recent Changes
1. Fixed balance tracking in simulation mode
2. Implemented percentage-based position sizing
3. Enhanced monitoring with real-time balance display
4. Trained ML model on actual trading data

## Configuration Files
- `config/bot_control.json` - Main bot settings
- `config/trading_params.json` - Trading parameters (position sizes, stop loss, etc.)

## Key Scripts
- `start_bot.py` - Main entry point
- `scripts/monitoring/enhanced_monitor.py` - Performance monitoring
- `scripts/utilities/adjust_positions.py` - Position size adjustment
- `scripts/analysis/analyze_trades.py` - Trade analysis

## Important Notes
- Bot tracks balance internally, not from wallet in simulation mode
- Position sizes are percentage-based (default 4% of balance)
- ML model provides confidence scores for trades
- Database stores all trades for analysis

## Next Steps
1. Continue monitoring performance in simulation
2. Fine-tune position sizing based on results
3. Consider implementing partial profit-taking
4. Prepare for real trading mode when ready
