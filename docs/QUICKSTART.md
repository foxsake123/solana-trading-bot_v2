# Quick Start Guide

## Starting Real Trading

1. **Final Safety Check**
   ```bash
   python scripts/view_parameters.py
   ```

2. **Start Trading Bot**
   ```bash
   python start_bot.py real --config config/bot_control_real.json
   ```

3. **Monitor Performance**
   ```bash
   # In another terminal
   python monitoring/ultra_monitor.py
   ```

## Your Configuration
- Wallet: 16um9NG9V88CWR9vESe42WfmNrDcTNq9jUit5t5mpgf
- Balance: 1.0014 SOL
- Position Size: 0.02-0.05 SOL per trade
- ML Confidence: 75% required
- Daily Loss Limit: 0.05 SOL

## Emergency Stop
Press `Ctrl+C` to stop the bot immediately.

## Support Scripts
- `scripts/ml_assessment.py` - Check ML readiness
- `scripts/parameter_optimizer.py` - Optimize parameters
- `monitoring/ultra_monitor.py` - Advanced monitoring
