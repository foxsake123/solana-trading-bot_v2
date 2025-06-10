# Solana Trading Bot v2 - Setup & Operations Guide

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your Birdeye API key to .env

# Run in simulation mode
python start_bot.py

# Monitor performance
python citadel_performance_monitor.py
```

## Architecture
- **Token Discovery**: Birdeye API (20+ tokens/scan)
- **Strategy**: Citadel-Barra (84.9% win rate)
- **Database**: SQLite with contract_address mapping
- **Position Sizing**: 3-5% per trade
- **Risk Management**: Factor-based scoring

## Key Configuration Files
- `config/trading_params.json` - Trading parameters
- `config/bot_control.json` - Bot state control
- `.env` - API keys and secrets

## Monitoring
- **Performance**: `python citadel_performance_monitor.py`
- **Simple Stats**: `python citadel_monitor_simple.py`
- **Logs**: Check `logs/` directory

## Known Issues & Fixes
1. **Contract Address Mapping**: Run `python fix_contract_address_mapping.py`
2. **No Trades Executing**: Lower `min_token_score` in trading_params.json

## Next Development Steps
1. Implement partial exit strategy (20/50/100/200%)
2. Add Twitter sentiment integration
3. Optimize position sizing (target 4-7%)
4. Enable real trading mode