# Solana Trading Bot Enhancement Plan - June 2025

## Current Status
- **Performance**: 84.9% win rate, 6.37 SOL profit, Sharpe 28.67
- **Strategy**: Citadel-Barra implementation active
- **ML Model**: 95.83% accuracy, percentage_change as top feature (61% importance)
- **Position Sizing**: 3-5% of balance (percentage-based)
- **API Integration**: Birdeye API for token data

## 1. Project Structure Organization

### Core Structure
```
solana-trading-bot-v2/
├── config/
│   ├── trading_params.json          # Main configuration
│   ├── optimized_strategy_v2.json   # Partial exit strategy
│   └── citadel_params.json          # Citadel-specific settings
├── core/
│   ├── analysis/
│   │   ├── token_analyzer.py
│   │   ├── sentiment_analyzer.py    # NEW: Twitter sentiment
│   │   └── ml_predictor.py
│   ├── data/
│   │   ├── market_data.py           # Birdeye integration
│   │   ├── twitter_data.py          # NEW: Twitter API
│   │   └── jupiter_aggregator.py   # NEW: Jupiter integration
│   ├── strategies/
│   │   ├── citadel_barra.py
│   │   ├── partial_exits.py         # NEW: Multi-level exits
│   │   └── top_traders.py           # NEW: Birdeye whale tracking
│   └── trading/
│       ├── trading_bot.py
│       └── position_manager.py
├── monitoring/
│   ├── real_trading_monitor.py
│   └── citadel_performance_monitor.py
├── ml/
│   ├── training/
│   │   ├── ml_retraining_pipeline.py # NEW: Auto-retraining
│   │   └── feature_engineering.py
│   └── models/
└── data/
    └── db/

### Files to Remove
- duplicate monitors (keep enhanced_monitor.py)
- old configuration files (consolidate into config/)
- unused test files
- backup files (.bak, .old)
```

## 2. Twitter Sentiment Analysis Implementation

### Setup
```python
# config/twitter_config.json
{
    "api_key": "YOUR_TWITTER_API_KEY",
    "bearer_token": "YOUR_BEARER_TOKEN",
    "sentiment_weight": 0.15,
    "min_followers": 1000,
    "tracked_accounts": [
        "ansemtrades",
        "thecryptoskull", 
        "solbuckets",
        "solanalegend"
    ],
    "keywords": ["$SOL", "Solana", "bullish", "pump"],
    "sentiment_threshold": 0.7
}
```

### Twitter Sentiment Analyzer
```python
# core/analysis/sentiment_analyzer.py
import tweepy
from transformers import pipeline
import numpy as np
from datetime import datetime, timedelta

class TwitterSentimentAnalyzer:
    def __init__(self, config):
        self.config = config
        self.client = tweepy.Client(bearer_token=config['bearer_token'])
        self.sentiment_model = pipeline(
            "sentiment-analysis", 
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )
        
    async def analyze_token_sentiment(self, token_symbol: str) -> dict:
        """Analyze Twitter sentiment for a specific token"""
        
        # Search recent tweets
        query = f"${token_symbol} -is:retweet lang:en"
        tweets = self.client.search_recent_tweets(
            query=query,
            max_results=100,
            tweet_fields=['created_at', 'public_metrics', 'author_id']
        )
        
        if not tweets.data:
            return {"sentiment": 0.5, "volume": 0, "confidence": 0}
        
        # Analyze sentiment
        sentiments = []
        weights = []
        
        for tweet in tweets.data:
            # Weight by engagement
            weight = np.log1p(
                tweet.public_metrics['like_count'] + 
                tweet.public_metrics['retweet_count'] * 2
            )
            
            # Get sentiment
            result = self.sentiment_model(tweet.text)[0]
            score = self._convert_to_numeric(result)
            
            sentiments.append(score)
            weights.append(weight)
        
        # Calculate weighted sentiment
        weighted_sentiment = np.average(sentiments, weights=weights)
        
        return {
            "sentiment": weighted_sentiment,
            "volume": len(tweets.data),
            "confidence": min(len(tweets.data) / 50, 1.0),
            "trending": self._is_trending(token_symbol)
        }
    
    def _convert_to_numeric(self, result):
        """Convert sentiment labels to numeric scores"""
        label_map = {
            'POSITIVE': 1.0,
            'NEGATIVE': 0.0,
            'NEUTRAL': 0.5
        }
        return label_map.get(result['label'], 0.5)
    
    def _is_trending(self, token_symbol):
        """Check if token is trending"""
        # Implementation for trend detection
        pass
```

## 3. Partial Exit Strategy Implementation

### Configuration
```json
// config/optimized_strategy_v2.json
{
    "partial_exits": {
        "enabled": true,
        "levels": [
            {"profit_pct": 0.5, "exit_pct": 0.3},   // 50% profit: exit 30%
            {"profit_pct": 1.0, "exit_pct": 0.4},   // 100% profit: exit 40%
            {"profit_pct": 2.0, "exit_pct": 0.3}    // 200% profit: keep 30% moonbag
        ],
        "trailing_stop": {
            "enabled": true,
            "activation": 3.0,  // Activate at 300% profit
            "distance": 0.2     // 20% trailing distance
        }
    }
}
```

### Partial Exit Manager
```python
# core/strategies/partial_exits.py
class PartialExitManager:
    def __init__(self, config):
        self.config = config
        self.exit_levels = config['partial_exits']['levels']
        self.executed_exits = {}  # Track which levels executed
        
    async def check_exits(self, position, current_price):
        """Check if any partial exit levels are hit"""
        
        profit_pct = (current_price - position.entry_price) / position.entry_price
        
        for level in self.exit_levels:
            level_key = f"{position.token}_{level['profit_pct']}"
            
            if (profit_pct >= level['profit_pct'] and 
                level_key not in self.executed_exits):
                
                # Calculate exit amount
                exit_amount = position.amount * level['exit_pct']
                
                # Execute partial exit
                result = await self.execute_partial_exit(
                    position, exit_amount, current_price
                )
                
                if result['success']:
                    self.executed_exits[level_key] = True
                    logger.info(f"Partial exit at {level['profit_pct']*100}% profit")
                
        # Check trailing stop for moonbag
        if profit_pct >= self.config['trailing_stop']['activation']:
            await self.manage_trailing_stop(position, current_price)
```

## 4. Birdeye Top Traders Integration

```python
# core/data/birdeye_top_traders.py
class BirdeyeTopTraders:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://public-api.birdeye.so"
        
    async def get_top_traders_activity(self, token_address):
        """Get top traders' recent activity for a token"""
        
        headers = {"X-API-KEY": self.api_key}
        
        # Get top holders
        holders_url = f"{self.base_url}/defi/token_holders"
        params = {"address": token_address, "limit": 20}
        
        response = await self._make_request(holders_url, headers, params)
        
        # Analyze whale movements
        whale_score = self._calculate_whale_score(response)
        
        return {
            "whale_accumulation": whale_score > 0.7,
            "whale_distribution": whale_score < 0.3,
            "whale_score": whale_score,
            "top_holders": response.get('data', [])[:10]
        }
    
    def _calculate_whale_score(self, holder_data):
        """Calculate whale accumulation/distribution score"""
        # Analyze recent transactions of top holders
        # Return score 0-1 (0 = heavy selling, 1 = heavy buying)
        pass
```

## 5. ML Retraining Pipeline

```python
# ml/training/ml_retraining_pipeline.py
import schedule
import time
from datetime import datetime, timedelta

class MLRetrainingPipeline:
    def __init__(self, db, model_path):
        self.db = db
        self.model_path = model_path
        self.min_new_trades = 50
        self.retrain_interval_hours = 24
        
    def start_pipeline(self):
        """Start automated retraining schedule"""
        schedule.every(self.retrain_interval_hours).hours.do(self.retrain_if_needed)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    def retrain_if_needed(self):
        """Retrain model if enough new data"""
        
        # Check new trades since last training
        last_training = self.get_last_training_time()
        new_trades = self.count_new_trades(last_training)
        
        if new_trades >= self.min_new_trades:
            logger.info(f"Starting retraining with {new_trades} new trades")
            
            # Prepare data
            features, labels = self.prepare_training_data()
            
            # Add new features
            features = self.add_enhanced_features(features)
            
            # Retrain model
            model = self.train_enhanced_model(features, labels)
            
            # Validate performance
            if self.validate_model(model):
                self.save_model(model)
                self.update_training_log()
                logger.info("Model retrained successfully")
            else:
                logger.warning("New model didn't pass validation")
    
    def add_enhanced_features(self, features):
        """Add new features including sentiment"""
        # Add Twitter sentiment
        # Add whale activity scores
        # Add market regime indicators
        return features
```

## 6. Jupiter Aggregator Integration

```python
# core/data/jupiter_aggregator.py
import aiohttp
import json

class JupiterAggregator:
    def __init__(self):
        self.quote_api = "https://quote-api.jup.ag/v6/quote"
        self.swap_api = "https://quote-api.jup.ag/v6/swap"
        
    async def get_best_route(self, input_mint, output_mint, amount):
        """Get best swap route from Jupiter"""
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 300,  # 3% slippage
            "onlyDirectRoutes": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.quote_api, params=params) as resp:
                quote = await resp.json()
        
        if not quote.get('data'):
            return None
            
        best_route = quote['data'][0]  # Jupiter returns sorted by best
        
        return {
            "route": best_route,
            "output_amount": int(best_route['outAmount']),
            "price_impact": float(best_route['priceImpactPct']),
            "fees": self._calculate_fees(best_route)
        }
    
    async def execute_swap(self, route, wallet_keypair):
        """Execute swap through Jupiter"""
        # Implementation for swap execution
        pass
```

## 7. Enhanced Trading Bot Integration

```python
# Update enhanced_trading_bot.py
class EnhancedTradingBot(TradingBot):
    def __init__(self, config, db, scanner, trader):
        super().__init__(config, db, scanner, trader)
        
        # Initialize new components
        self.sentiment_analyzer = TwitterSentimentAnalyzer(config['twitter'])
        self.partial_exit_manager = PartialExitManager(config)
        self.birdeye_traders = BirdeyeTopTraders(config['birdeye_api_key'])
        self.jupiter = JupiterAggregator()
        
        # Start ML retraining pipeline in background
        self.ml_pipeline = MLRetrainingPipeline(db, 'models/ml_model.pkl')
        asyncio.create_task(self.ml_pipeline.start_pipeline())
    
    async def analyze_token_enhanced(self, token_data):
        """Enhanced token analysis with all new features"""
        
        # Base analysis
        base_score = await self.analyze_token(token_data)
        
        # Add sentiment analysis
        sentiment = await self.sentiment_analyzer.analyze_token_sentiment(
            token_data['symbol']
        )
        
        # Check whale activity
        whale_data = await self.birdeye_traders.get_top_traders_activity(
            token_data['contract_address']
        )
        
        # Combine signals
        final_score = (
            base_score * 0.6 +
            sentiment['sentiment'] * sentiment['confidence'] * 0.2 +
            whale_data['whale_score'] * 0.2
        )
        
        return {
            'score': final_score,
            'sentiment': sentiment,
            'whale_activity': whale_data,
            'recommend': final_score > 0.7
        }
```

## Implementation Priority

1. **Week 1**: Organize project structure, implement Twitter sentiment
2. **Week 2**: Add partial exit strategy and test thoroughly
3. **Week 3**: Integrate Birdeye top traders and Jupiter aggregator
4. **Week 4**: Set up ML retraining pipeline and performance monitoring

## Expected Improvements

- **Entry Signal Quality**: +15-20% from Twitter sentiment
- **Exit Optimization**: +30-40% profits from partial exits
- **Execution**: -2-3% slippage reduction with Jupiter
- **Model Accuracy**: Maintain 95%+ with continuous retraining
- **Risk Management**: Better whale movement detection

## Next Session Tasks

1. Upload the required files mentioned
2. Test Twitter API integration
3. Implement first partial exit level
4. Monitor performance with new features