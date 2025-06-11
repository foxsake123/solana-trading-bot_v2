# core/analysis/twitter_sentiment.py
"""
Twitter Sentiment Analysis for Solana Tokens
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
import re
from textblob import TextBlob

logger = logging.getLogger(__name__)

class TwitterSentimentAnalyzer:
    """Analyzes Twitter sentiment for tokens"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.bearer_token = config.get('TWITTER_BEARER_TOKEN')
        self.base_url = "https://api.twitter.com/2/tweets/search/recent"
        
        # Sentiment thresholds
        self.sentiment_config = {
            'min_tweets': 10,
            'bullish_threshold': 0.3,
            'bearish_threshold': -0.3,
            'volume_spike_multiplier': 3.0
        }
        
        # Cache for avoiding rate limits
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    async def analyze_token_sentiment(self, token_symbol: str, token_address: str = None) -> Dict:
        """
        Analyze Twitter sentiment for a token
        
        Returns sentiment score and signals
        """
        # Check cache
        cache_key = f"{token_symbol}_{token_address}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data
        
        try:
            # Search for tweets
            tweets = await self._search_tweets(token_symbol)
            
            if not tweets:
                return {
                    'sentiment_score': 0,
                    'tweet_count': 0,
                    'signal': 'NEUTRAL',
                    'error': 'No tweets found'
                }
            
            # Analyze sentiment
            sentiments = []
            for tweet in tweets:
                sentiment = self._analyze_text_sentiment(tweet['text'])
                sentiments.append(sentiment)
            
            # Calculate metrics
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            tweet_count = len(tweets)
            
            # Determine signal
            signal = 'NEUTRAL'
            if tweet_count >= self.sentiment_config['min_tweets']:
                if avg_sentiment >= self.sentiment_config['bullish_threshold']:
                    signal = 'BULLISH'
                elif avg_sentiment <= self.sentiment_config['bearish_threshold']:
                    signal = 'BEARISH'
            
            # Check for volume spikes
            volume_spike = await self._check_volume_spike(token_symbol)
            
            result = {
                'sentiment_score': avg_sentiment,
                'tweet_count': tweet_count,
                'signal': signal,
                'volume_spike': volume_spike,
                'top_tweets': tweets[:3],  # Top 3 tweets
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self.cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {token_symbol}: {e}")
            return {
                'sentiment_score': 0,
                'tweet_count': 0,
                'signal': 'NEUTRAL',
                'error': str(e)
            }
    
    async def _search_tweets(self, token_symbol: str) -> List[Dict]:
        """Search for tweets mentioning the token"""
        if not self.bearer_token:
            return []
        
        # Build query
        query = f"${token_symbol} OR #{token_symbol} lang:en -is:retweet"
        
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'query': query,
            'max_results': 100,
            'tweet.fields': 'created_at,author_id,public_metrics'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"Twitter API error: {response.status}")
                    return []
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob"""
        # Clean text
        text = re.sub(r'http\S+', '', text)  # Remove URLs
        text = re.sub(r'@\w+', '', text)     # Remove mentions
        text = re.sub(r'#', '', text)        # Remove hashtags
        
        # Get sentiment
        blob = TextBlob(text)
        
        # Combine polarity and subjectivity
        # Polarity: -1 (negative) to 1 (positive)
        # Subjectivity: 0 (objective) to 1 (subjective)
        sentiment_score = blob.sentiment.polarity
        
        # Boost score for certain keywords
        bullish_keywords = ['moon', 'rocket', 'bullish', 'pump', 'gem', 'buy', 'long']
        bearish_keywords = ['dump', 'crash', 'bearish', 'sell', 'short', 'rug']
        
        text_lower = text.lower()
        for keyword in bullish_keywords:
            if keyword in text_lower:
                sentiment_score += 0.1
        
        for keyword in bearish_keywords:
            if keyword in text_lower:
                sentiment_score -= 0.1
        
        # Clamp to [-1, 1]
        return max(-1, min(1, sentiment_score))
    
    async def _check_volume_spike(self, token_symbol: str) -> bool:
        """Check if there's a spike in tweet volume"""
        # This would compare current volume to historical average
        # For now, simplified implementation
        current_tweets = await self._search_tweets(token_symbol)
        
        # If more than 50 tweets in recent search, consider it a spike
        return len(current_tweets) > 50
    
    def get_sentiment_boost(self, sentiment_data: Dict) -> float:
        """
        Get alpha boost from sentiment data
        
        Returns value between -0.1 and 0.1
        """
        if sentiment_data.get('signal') == 'BULLISH':
            boost = 0.05
            if sentiment_data.get('volume_spike'):
                boost += 0.05
            return boost
        elif sentiment_data.get('signal') == 'BEARISH':
            return -0.1
        else:
            return 0.0