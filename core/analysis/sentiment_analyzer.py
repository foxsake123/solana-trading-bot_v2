# core/analysis/sentiment_analyzer.py
"""
Twitter Sentiment Analysis for Solana Trading Bot
Analyzes social sentiment to enhance entry signals
"""

import tweepy
import asyncio
import numpy as np
from datetime import datetime, timedelta
from transformers import pipeline
import aiohttp
import logging
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TwitterSentimentAnalyzer:
    """Enhanced Twitter sentiment analyzer with RoBERTa model"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.bearer_token = config.get('bearer_token')
        
        # Initialize Twitter client
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        
        # Initialize sentiment model - using RoBERTa for better accuracy
        self.sentiment_model = pipeline(
            "sentiment-analysis", 
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=-1  # CPU, set to 0 for GPU
        )
        
        # Cache for API rate limiting
        self.sentiment_cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Influencer accounts to track
        self.tracked_accounts = config.get('tracked_accounts', [
            "ansemtrades",
            "thecryptoskull", 
            "solbuckets",
            "solanalegend",
            "blknoiz06",
            "CryptoGodJohn",
            "inversebrah"
        ])
        
        # Sentiment thresholds
        self.bullish_threshold = config.get('bullish_threshold', 0.7)
        self.bearish_threshold = config.get('bearish_threshold', 0.3)
        
    async def analyze_token_sentiment(self, token_symbol: str, contract_address: str = None) -> Dict:
        """
        Analyze Twitter sentiment for a specific token
        Returns sentiment score, volume, and signals
        """
        
        # Check cache first
        cache_key = f"{token_symbol}_{datetime.now().hour}"
        if cache_key in self.sentiment_cache:
            cached_time, cached_data = self.sentiment_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                logger.debug(f"Using cached sentiment for {token_symbol}")
                return cached_data
        
        try:
            # Build search query
            query = self._build_search_query(token_symbol)
            
            # Search recent tweets
            tweets = await self._search_tweets(query)
            
            if not tweets:
                return self._empty_sentiment_result()
            
            # Analyze sentiment
            sentiment_data = await self._analyze_tweets(tweets, token_symbol)
            
            # Check influencer sentiment
            influencer_sentiment = await self._check_influencer_sentiment(token_symbol)
            
            # Combine results
            final_sentiment = self._combine_sentiment_signals(
                sentiment_data, 
                influencer_sentiment
            )
            
            # Cache result
            self.sentiment_cache[cache_key] = (datetime.now(), final_sentiment)
            
            return final_sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {token_symbol}: {e}")
            return self._empty_sentiment_result()
    
    def _build_search_query(self, token_symbol: str) -> str:
        """Build optimized Twitter search query"""
        
        # Basic query with common patterns
        base_query = f"(${token_symbol} OR #{token_symbol})"
        
        # Add sentiment keywords
        sentiment_keywords = "(bullish OR moon OR pump OR gem OR buying OR accumulating)"
        
        # Exclude spam and retweets
        exclusions = "-is:retweet -is:reply lang:en -giveaway -airdrop"
        
        # Combine query parts
        query = f"{base_query} {sentiment_keywords} {exclusions}"
        
        return query
    
    async def _search_tweets(self, query: str, max_results: int = 100) -> List:
        """Search tweets with rate limiting protection"""
        
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id', 'context_annotations'],
                user_fields=['username', 'public_metrics', 'verified'],
                expansions=['author_id']
            )
            
            if tweets.data:
                return tweets
            else:
                return None
                
        except tweepy.TooManyRequests:
            logger.warning("Twitter API rate limit reached")
            await asyncio.sleep(60)  # Wait 1 minute
            return None
        except Exception as e:
            logger.error(f"Twitter search error: {e}")
            return None
    
    async def _analyze_tweets(self, tweets_response, token_symbol: str) -> Dict:
        """Analyze sentiment from tweets"""
        
        sentiments = []
        weights = []
        volume_data = {
            'total_tweets': 0,
            'total_engagement': 0,
            'unique_authors': set()
        }
        
        # Extract user data
        users = {u.id: u for u in tweets_response.includes.get('users', [])}
        
        for tweet in tweets_response.data:
            # Get author info
            author = users.get(tweet.author_id)
            
            # Calculate engagement weight
            metrics = tweet.public_metrics
            engagement = (
                metrics['like_count'] + 
                metrics['retweet_count'] * 2 + 
                metrics['reply_count'] * 0.5
            )
            
            # Apply author credibility weight
            if author:
                follower_count = author.public_metrics['followers_count']
                credibility = np.log1p(follower_count) / 10  # Normalize
                weight = np.sqrt(engagement) * (1 + credibility)
            else:
                weight = np.sqrt(engagement)
            
            # Analyze sentiment
            try:
                result = self.sentiment_model(tweet.text)[0]
                score = self._convert_sentiment_to_score(result)
                
                sentiments.append(score)
                weights.append(weight)
                
                # Update volume data
                volume_data['total_tweets'] += 1
                volume_data['total_engagement'] += engagement
                volume_data['unique_authors'].add(tweet.author_id)
                
            except Exception as e:
                logger.debug(f"Error analyzing tweet sentiment: {e}")
                continue
        
        if not sentiments:
            return {
                'sentiment_score': 0.5,
                'confidence': 0,
                'volume': 0
            }
        
        # Calculate weighted sentiment
        weighted_sentiment = np.average(sentiments, weights=weights)
        
        # Calculate momentum (recent vs older tweets)
        if len(sentiments) > 10:
            recent_sentiment = np.mean(sentiments[:len(sentiments)//2])
            older_sentiment = np.mean(sentiments[len(sentiments)//2:])
            momentum = recent_sentiment - older_sentiment
        else:
            momentum = 0
        
        return {
            'sentiment_score': weighted_sentiment,
            'confidence': min(len(sentiments) / 50, 1.0),
            'volume': volume_data['total_tweets'],
            'engagement': volume_data['total_engagement'],
            'unique_authors': len(volume_data['unique_authors']),
            'momentum': momentum
        }
    
    async def _check_influencer_sentiment(self, token_symbol: str) -> Dict:
        """Check sentiment from tracked influencer accounts"""
        
        influencer_signals = []
        
        for account in self.tracked_accounts:
            query = f"from:{account} ${token_symbol} -is:retweet"
            
            try:
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['created_at', 'public_metrics']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        # Analyze sentiment
                        result = self.sentiment_model(tweet.text)[0]
                        score = self._convert_sentiment_to_score(result)
                        
                        # Weight by recency
                        hours_ago = (datetime.now() - tweet.created_at).total_seconds() / 3600
                        recency_weight = np.exp(-hours_ago / 24)  # Decay over 24 hours
                        
                        influencer_signals.append({
                            'account': account,
                            'sentiment': score,
                            'weight': recency_weight,
                            'engagement': tweet.public_metrics['like_count']
                        })
                        
            except Exception as e:
                logger.debug(f"Error checking influencer {account}: {e}")
                continue
        
        if not influencer_signals:
            return {'score': 0.5, 'signal_strength': 0}
        
        # Calculate weighted influencer sentiment
        total_weight = sum(s['weight'] for s in influencer_signals)
        if total_weight > 0:
            weighted_score = sum(s['sentiment'] * s['weight'] for s in influencer_signals) / total_weight
        else:
            weighted_score = 0.5
        
        return {
            'score': weighted_score,
            'signal_strength': min(len(influencer_signals) / len(self.tracked_accounts), 1.0),
            'signals': influencer_signals
        }
    
    def _convert_sentiment_to_score(self, result: Dict) -> float:
        """Convert model output to normalized score"""
        
        label = result['label'].upper()
        confidence = result['score']
        
        # Map labels to base scores
        label_map = {
            'POSITIVE': 0.8,
            'NEGATIVE': 0.2,
            'NEUTRAL': 0.5
        }
        
        base_score = label_map.get(label, 0.5)
        
        # Adjust by confidence
        if label == 'POSITIVE':
            score = 0.5 + (base_score - 0.5) * confidence
        elif label == 'NEGATIVE':
            score = 0.5 - (0.5 - base_score) * confidence
        else:
            score = base_score
        
        return score
    
    def _combine_sentiment_signals(self, general_sentiment: Dict, influencer_sentiment: Dict) -> Dict:
        """Combine general and influencer sentiment signals"""
        
        # Weight influencer sentiment higher if strong signal
        if influencer_sentiment['signal_strength'] > 0.5:
            influencer_weight = 0.4
        else:
            influencer_weight = 0.2
        
        general_weight = 1 - influencer_weight
        
        # Combined sentiment score
        combined_score = (
            general_sentiment['sentiment_score'] * general_weight +
            influencer_sentiment['score'] * influencer_weight
        )
        
        # Determine signal strength
        if combined_score > self.bullish_threshold:
            signal = 'BULLISH'
            signal_strength = (combined_score - self.bullish_threshold) / (1 - self.bullish_threshold)
        elif combined_score < self.bearish_threshold:
            signal = 'BEARISH'
            signal_strength = (self.bearish_threshold - combined_score) / self.bearish_threshold
        else:
            signal = 'NEUTRAL'
            signal_strength = 0
        
        # Volume spike detection
        volume_spike = general_sentiment['volume'] > 50  # Significant discussion
        
        return {
            'sentiment_score': combined_score,
            'signal': signal,
            'signal_strength': signal_strength,
            'confidence': general_sentiment['confidence'],
            'volume': general_sentiment['volume'],
            'engagement': general_sentiment['engagement'],
            'unique_authors': general_sentiment['unique_authors'],
            'momentum': general_sentiment['momentum'],
            'influencer_sentiment': influencer_sentiment,
            'volume_spike': volume_spike,
            'timestamp': datetime.now()
        }
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result"""
        return {
            'sentiment_score': 0.5,
            'signal': 'NEUTRAL',
            'signal_strength': 0,
            'confidence': 0,
            'volume': 0,
            'engagement': 0,
            'unique_authors': 0,
            'momentum': 0,
            'volume_spike': False,
            'timestamp': datetime.now()
        }
    
    async def get_trending_tokens(self, limit: int = 10) -> List[Dict]:
        """Get trending tokens based on Twitter activity"""
        
        # Search for trending crypto discussions
        query = "(solana OR $SOL) (gem OR moon OR bullish OR pump) -is:retweet lang:en"
        
        tweets = await self._search_tweets(query, max_results=100)
        if not tweets:
            return []
        
        # Extract mentioned tokens
        token_mentions = defaultdict(int)
        
        for tweet in tweets.data:
            # Look for $ mentions
            import re
            tokens = re.findall(r'\$([A-Z]{2,10})', tweet.text)
            for token in tokens:
                if token not in ['SOL', 'BTC', 'ETH', 'USDT', 'USDC']:  # Exclude majors
                    token_mentions[token] += tweet.public_metrics['like_count'] + 1
        
        # Sort by mention weight
        trending = sorted(token_mentions.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{'symbol': symbol, 'weight': weight} for symbol, weight in trending]
