# Next Steps for Solana Trading Bot v2

## Immediate Fixes (Priority 1)
- [ ] Fix Birdeye API integration
  - Replace BirdeyeAPI with BirdeyeAPIv3 in `core/data/market_data.py`
  - Update TokenScanner to use new endpoints
  - Test token discovery with rate limiting
- [ ] Verify position sizing (3-5% executing correctly)
- [ ] Test partial exit levels in simulation

## Short Term (This Week)
- [ ] Twitter sentiment integration
  - Add bearer token to .env
  - Test sentiment scoring on real tokens
  - Monitor influencer accounts (ansem, etc.)
- [ ] Performance dashboard
  - Real-time P&L tracking
  - Win rate by strategy component
  - Factor attribution analysis
- [ ] Database optimization
  - Add indexes for faster queries
  - Implement data retention policy

## Medium Term (Next 2 Weeks)
- [ ] Backtesting framework
  - Test strategy variations
  - Optimize signal weights
  - Risk/reward analysis
- [ ] Advanced risk management
  - Portfolio-level VAR
  - Correlation limits
  - Sector exposure tracking
- [ ] Jupiter integration
  - Implement swap execution
  - Route optimization
  - Slippage reduction

## Long Term (Month+)
- [ ] Advanced ML features
  - Ensemble models
  - Feature engineering pipeline
  - Real-time model updates
- [ ] Multi-chain expansion
  - Base/Arbitrum support
  - Cross-chain arbitrage
- [ ] Telegram bot interface
  - Trade notifications
  - Performance alerts
  - Remote control

## Performance Targets
- Win rate: 85%+ (current: 84.9%)
- Sharpe ratio: 30+ (current: 28.67)
- Daily profit: 50+ SOL (current: 6.37)
- Max drawdown: <10%