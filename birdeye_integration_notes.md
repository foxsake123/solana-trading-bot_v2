# Birdeye API Integration Notes

## Working Endpoints (as of June 2025)
- /defi/tokenlist - Get token lists with sorting
- /defi/price - Get token prices
- /defi/token_overview - Get token details
- /defi/token_security - Get security info

## Important Notes
- NO v3 endpoints - use /defi/ directly
- Starter package: 100 req/min limit
- Rate limiting: 600ms between requests
- Cache responses for 5 minutes

## Common Issues Fixed
- Wrong endpoints (remove /v3/)
- Huge percentage gains (filter >10,000%)
- Zero prices (fetch separately if needed)