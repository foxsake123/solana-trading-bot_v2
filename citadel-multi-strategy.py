#!/usr/bin/env python3
"""
Citadel-Inspired Multi-Strategy Trading System
Implements multiple uncorrelated strategies for Solana trading
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum
import talib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import tensorflow as tf
from collections import deque

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    ML_ALPHA = "ml_alpha"

class CitadelMultiStrategy:
    """Multi-strategy trading system inspired by Citadel's approach"""
    
    def __init__(self, config: Dict, db, ml_models=None):
        self.config = config
        self.db = db
        self.ml_models = ml_models or {}
        self.citadel_config = config.get('citadel_mode', {})
        
        # Strategy weights
        self.strategy_weights = {
            StrategyType.MOMENTUM: self.citadel_config['strategies']['momentum']['weight'],
            StrategyType.MEAN_REVERSION: self.citadel_config['strategies']['mean_reversion']['weight'],
            StrategyType.ARBITRAGE: self.citadel_config['strategies']['arbitrage']['weight'],
            StrategyType.ML_ALPHA: self.citadel_config['strategies']['ml_alpha']['weight']
        }
        
        # Performance tracking
        self.strategy_performance = {
            strategy: {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0.0,
                'sharpe': 0.0,
                'last_update': datetime.now()
            } for strategy in StrategyType
        }
        
        # Initialize ML models if not provided
        if not self.ml_models:
            self._initialize_ml_models()
    
    def _initialize_ml_models(self):
        """Initialize ensemble ML models"""
        self.ml_models = {
            'rf': RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=50,
                random_state=42
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                random_state=42
            ),
            'lstm': self._build_lstm_model()
        }
        
        # Feature scaler
        self.scaler = StandardScaler()
    
    def _build_lstm_model(self):
        """Build LSTM model for price prediction"""
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(128, return_sequences=True, input_shape=(20, 10)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    async def analyze_token(self, token_data: Dict) -> Dict:
        """Analyze token using all strategies"""
        signals = {}
        
        # Get historical data
        history = await self._get_token_history(token_data['contract_address'])
        
        if len(history) < 50:  # Need enough data
            return {
                'recommendation': False,
                'confidence': 0.0,
                'reasons': ['Insufficient historical data']
            }
        
        # Run each strategy
        if self.citadel_config['strategies']['momentum']['enabled']:
            signals[StrategyType.MOMENTUM] = self._momentum_strategy(history)
        
        if self.citadel_config['strategies']['mean_reversion']['enabled']:
            signals[StrategyType.MEAN_REVERSION] = self._mean_reversion_strategy(history)
        
        if self.citadel_config['strategies']['arbitrage']['enabled']:
            signals[StrategyType.ARBITRAGE] = await self._arbitrage_strategy(token_data, history)
        
        if self.citadel_config['strategies']['ml_alpha']['enabled']:
            signals[StrategyType.ML_ALPHA] = self._ml_alpha_strategy(history)
        
        # Combine signals with dynamic weights
        final_signal = self._combine_signals(signals)
        
        # Apply winner amplification
        if self.citadel_config['winner_amplification']['enabled']:
            final_signal = self._apply_winner_amplification(final_signal)
        
        return final_signal
    
    def _momentum_strategy(self, history: pd.DataFrame) -> Dict:
        """Momentum-based strategy"""
        config = self.citadel_config['strategies']['momentum']
        
        # Calculate momentum indicators
        momentum_scores = []
        
        for period in config['lookback_periods']:
            if len(history) > period:
                returns = history['price'].pct_change(period).iloc[-1]
                momentum_scores.append(returns)
        
        if not momentum_scores:
            return {'signal': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Average momentum score
        avg_momentum = np.mean(momentum_scores)
        
        # Volume momentum
        volume_momentum = history['volume'].pct_change(5).iloc[-1]
        
        # Combined score
        combined_score = 0.7 * avg_momentum + 0.3 * volume_momentum
        
        # Signal strength
        signal = 1.0 if combined_score > config['min_momentum_score'] else 0.0
        confidence = min(abs(combined_score), 1.0)
        
        reasons = []
        if signal > 0:
            reasons.append(f"Strong momentum: {combined_score:.2%}")
            reasons.append(f"Volume increasing: {volume_momentum:.2%}")
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'metrics': {
                'momentum_score': combined_score,
                'volume_momentum': volume_momentum
            }
        }
    
    def _mean_reversion_strategy(self, history: pd.DataFrame) -> Dict:
        """Mean reversion strategy"""
        config = self.citadel_config['strategies']['mean_reversion']
        
        # Calculate indicators
        prices = history['price'].values
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(
            prices,
            timeperiod=config['bollinger_periods'],
            nbdevup=config['bollinger_std'],
            nbdevdn=config['bollinger_std']
        )
        
        # RSI
        rsi = talib.RSI(prices, timeperiod=config['rsi_period'])
        
        current_price = prices[-1]
        current_rsi = rsi[-1]
        
        # Check for oversold/overbought conditions
        signal = 0.0
        reasons = []
        
        if current_price < lower[-1] and current_rsi < config['oversold_threshold']:
            signal = 1.0
            reasons.append(f"Oversold: RSI={current_rsi:.1f}")
            reasons.append(f"Price below lower BB: {(current_price/lower[-1]-1)*100:.1f}%")
        elif current_price > upper[-1] and current_rsi > config['overbought_threshold']:
            signal = -1.0  # Short signal (not implemented yet)
            reasons.append(f"Overbought: RSI={current_rsi:.1f}")
        
        # Calculate z-score
        price_mean = np.mean(prices[-20:])
        price_std = np.std(prices[-20:])
        z_score = (current_price - price_mean) / price_std if price_std > 0 else 0
        
        confidence = min(abs(z_score) / 3, 1.0)  # Normalize z-score to [0,1]
        
        return {
            'signal': max(signal, 0),  # Only long signals for now
            'confidence': confidence,
            'reasons': reasons,
            'metrics': {
                'rsi': current_rsi,
                'z_score': z_score,
                'bb_position': (current_price - lower[-1]) / (upper[-1] - lower[-1])
            }
        }
    
    async def _arbitrage_strategy(self, token_data: Dict, history: pd.DataFrame) -> Dict:
        """Cross-DEX arbitrage strategy"""
        config = self.citadel_config['strategies']['arbitrage']
        
        # Get prices from multiple DEXs
        dex_prices = await self._get_multi_dex_prices(token_data['contract_address'])
        
        if len(dex_prices) < 2:
            return {'signal': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Find arbitrage opportunities
        prices = list(dex_prices.values())
        max_price = max(prices)
        min_price = min(prices)
        
        spread_pct = (max_price - min_price) / min_price
        
        signal = 0.0
        reasons = []
        
        if spread_pct > config['min_spread_pct']:
            signal = 1.0
            buy_dex = [dex for dex, price in dex_prices.items() if price == min_price][0]
            sell_dex = [dex for dex, price in dex_prices.items() if price == max_price][0]
            reasons.append(f"Arbitrage opportunity: {spread_pct:.2%} spread")
            reasons.append(f"Buy on {buy_dex}, sell on {sell_dex}")
        
        confidence = min(spread_pct / 0.05, 1.0)  # Normalize to [0,1]
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'metrics': {
                'spread_pct': spread_pct,
                'dex_prices': dex_prices
            }
        }
    
    def _ml_alpha_strategy(self, history: pd.DataFrame) -> Dict:
        """ML-based alpha generation"""
        config = self.citadel_config['strategies']['ml_alpha']
        
        # Prepare features
        features = self._prepare_ml_features(history)
        
        if features is None:
            return {'signal': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Get predictions from ensemble
        predictions = {}
        
        for model_name in config['ensemble_models']:
            if model_name in self.ml_models and model_name != 'lstm':
                try:
                    if hasattr(self.ml_models[model_name], 'predict_proba'):
                        pred = self.ml_models[model_name].predict_proba(features)[:, 1][0]
                    else:
                        pred = self.ml_models[model_name].predict(features)[0]
                    predictions[model_name] = pred
                except:
                    logger.warning(f"ML model {model_name} prediction failed")
        
        if not predictions:
            return {'signal': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Calculate agreement
        avg_prediction = np.mean(list(predictions.values()))
        agreement = sum(1 for p in predictions.values() if p > 0.5) / len(predictions)
        
        signal = 1.0 if agreement >= config['min_agreement'] else 0.0
        confidence = avg_prediction
        
        reasons = []
        if signal > 0:
            reasons.append(f"ML ensemble agreement: {agreement:.0%}")
            reasons.append(f"Average confidence: {avg_prediction:.2%}")
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons,
            'metrics': {
                'predictions': predictions,
                'agreement': agreement
            }
        }
    
    def _prepare_ml_features(self, history: pd.DataFrame) -> Optional[np.ndarray]:
        """Prepare features for ML models"""
        try:
            prices = history['price'].values
            volumes = history['volume'].values
            
            features = []
            
            # Price features
            features.extend([
                prices[-1] / prices[-2] - 1,  # 1-period return
                prices[-1] / prices[-5] - 1,  # 5-period return
                prices[-1] / prices[-10] - 1, # 10-period return
                np.std(prices[-20:]) / np.mean(prices[-20:]),  # Volatility
            ])
            
            # Volume features
            features.extend([
                volumes[-1] / np.mean(volumes[-5:]),  # Volume ratio
                np.std(volumes[-20:]) / np.mean(volumes[-20:])  # Volume volatility
            ])
            
            # Technical indicators
            rsi = talib.RSI(prices, timeperiod=14)[-1]
            macd, signal, _ = talib.MACD(prices)
            features.extend([
                rsi / 100,
                (macd[-1] - signal[-1]) / prices[-1]  # MACD signal
            ])
            
            # Market microstructure
            if 'liquidity' in history.columns:
                features.append(history['liquidity'].iloc[-1] / history['liquidity'].mean())
            
            if 'holders' in history.columns:
                features.append(history['holders'].pct_change(5).iloc[-1])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return None
    
    def _combine_signals(self, signals: Dict[StrategyType, Dict]) -> Dict:
        """Combine signals from all strategies"""
        if not signals:
            return {'recommendation': False, 'confidence': 0.0, 'reasons': []}
        
        # Calculate weighted signal
        total_weight = 0
        weighted_signal = 0
        weighted_confidence = 0
        all_reasons = []
        all_metrics = {}
        
        for strategy, signal_data in signals.items():
            if signal_data['signal'] > 0:
                weight = self.strategy_weights[strategy]
                weighted_signal += signal_data['signal'] * weight
                weighted_confidence += signal_data['confidence'] * weight
                total_weight += weight
                
                # Add strategy name to reasons
                for reason in signal_data['reasons']:
                    all_reasons.append(f"[{strategy.value}] {reason}")
                
                # Collect metrics
                all_metrics[strategy.value] = signal_data.get('metrics', {})
        
        if total_weight == 0:
            return {'recommendation': False, 'confidence': 0.0, 'reasons': ['No positive signals']}
        
        # Normalize
        final_signal = weighted_signal / total_weight
        final_confidence = weighted_confidence / total_weight
        
        return {
            'recommendation': final_signal > 0.5,
            'confidence': final_confidence,
            'signal_strength': final_signal,
            'reasons': all_reasons,
            'strategy_metrics': all_metrics,
            'active_strategies': len([s for s in signals.values() if s['signal'] > 0])
        }
    
    def _apply_winner_amplification(self, signal: Dict) -> Dict:
        """Amplify signals for winning strategies"""
        if not signal['recommendation']:
            return signal
        
        config = self.citadel_config['winner_amplification']
        
        # Get recent performance
        best_strategy = self._get_best_performing_strategy(
            window_hours=config['performance_window']
        )
        
        if best_strategy and self.strategy_performance[best_strategy]['sharpe'] > 2.0:
            # Amplify signal
            scale = min(
                config['scale_factor'] * (1 + self.strategy_performance[best_strategy]['sharpe'] / 10),
                config['max_scale']
            )
            
            signal['confidence'] = min(signal['confidence'] * scale, 1.0)
            signal['reasons'].append(f"Signal amplified {scale:.1f}x due to {best_strategy.value} performance")
            signal['amplification_factor'] = scale
        
        return signal
    
    def _get_best_performing_strategy(self, window_hours: int = 24) -> Optional[StrategyType]:
        """Get best performing strategy in recent window"""
        best_strategy = None
        best_sharpe = 0.0
        
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        
        for strategy, performance in self.strategy_performance.items():
            if performance['last_update'] > cutoff_time and performance['sharpe'] > best_sharpe:
                best_sharpe = performance['sharpe']
                best_strategy = strategy
        
        return best_strategy
    
    async def _get_token_history(self, contract_address: str) -> pd.DataFrame:
        """Get token price history from database"""
        # This would query your database for historical data
        # For now, returning mock data structure
        return pd.DataFrame()
    
    async def _get_multi_dex_prices(self, contract_address: str) -> Dict[str, float]:
        """Get token prices from multiple DEXs"""
        # This would query multiple DEX APIs
        # For now, returning mock data
        return {}
    
    def update_strategy_performance(self, strategy: StrategyType, trade_result: Dict):
        """Update strategy performance metrics"""
        perf = self.strategy_performance[strategy]
        
        perf['trades'] += 1
        if trade_result['profit'] > 0:
            perf['wins'] += 1
        perf['total_pnl'] += trade_result['profit']
        
        # Update Sharpe ratio (simplified)
        if perf['trades'] > 10:
            returns = []  # Would get from database
            perf['sharpe'] = self._calculate_sharpe_ratio(returns)
        
        perf['last_update'] = datetime.now()
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        return np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
