# Solana Trading Bot v2 - Project Instructions

## Bot Overview
A high-performance Solana trading bot using Birdeye API for token discovery, implementing the Citadel-Barra strategy with 84.9% win rate in simulation.

## Current Status
- ✅ Token discovery working (20+ tokens per scan)
- ✅ Birdeye API integrated (Starter tier)
- ✅ Database field mapping fixed
- ⏳ Waiting for first trade execution
- 📊 Simulation mode active

## Key Files
- **Main Entry**: `python start_bot.py` or `python final_working_starter.py`
- **Monitor**: `python citadel_performance_monitor.py`
- **Config**: `config/trading_params.json`
- **Strategy**: `core/strategies/citadel_barra_strategy.py`

## Critical Settings
```json
{
  "min_token_score": 0.7,
  "position_size_min": 0.03,
  "position_size_max": 0.05,
  "max_positions": 10,
  "simulation_mode": true
}
```

## Recent Fixes
1. **Contract Address Mapping**: Fixed in `market_data.py` line 245
2. **Field Mapper**: Added `utils/field_mapper.py` for consistent data handling
3. **Token Discovery**: Confirmed working with real Solana tokens

## Performance Targets
- Win Rate: 84.9% (current)
- Position Sizing: 3-5% (target: 4-7%)
- Exit Strategy: 20%, 50%, 100%, 200% levels
- Risk Management: Citadel-Barra factor model

## Dependencies
- Birdeye API (Starter tier)
- Solana Web3.py
- SQLite database
- Python 3.8+