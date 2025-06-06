#!/usr/bin/env python3
"""
Citadel-Inspired Winner Analysis and Amplification System
Identifies and scales winning strategies and positions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

@dataclass
class WinnerProfile:
    """Profile of a winning position or strategy"""
    token_address: str
    entry_time: datetime
    entry_price: float
    current_price: float
    peak_price: float
    position_size: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    peak_pnl_pct: float
    strategy_used: str
    entry_signals: Dict
    momentum_score: float
    time_held: timedelta
    
    @property
    def is_super_winner(self) -> bool:
        """Check if this is a super winner (100%+ gain)"""
        return self.unrealized_pnl_pct > 1.0
    
    @property
    def drawdown_from_peak(self) -> float:
        """Calculate drawdown from peak"""
        return (self.peak_price - self.current_price) / self.peak_price if self.peak_price > 0 else 0

class CitadelWinnerAnalyzer:
    """System for analyzing and amplifying winning positions"""
    
    def __init__(self, config: Dict, db, multi_strategy=None):
        self.config = config
        self.db = db
        self.multi_strategy = multi_strategy
        self.winner_config = config.get('citadel_mode', {}).get('winner_amplification', {})
        
        # Winner tracking
        self.current_winners: Dict[str, WinnerProfile] = {}
        self.historical_winners: List[WinnerProfile] = []
        self.super_winner_patterns: Dict[str, List] = defaultdict(list)
        
        # Pattern recognition parameters
        self.min_pattern_occurrences = 3
        self.pattern_confidence_threshold = 0.7
        
    async def analyze_positions(self, positions: Dict, market_data: Dict) -> Dict:
        """Analyze all positions and identify winners"""
        winners = []
        potential_winners = []
        exit_candidates = []
        scale_up_candidates = []
        
        for token_address, position in positions.items():
            # Create winner profile
            profile = await self._create_winner_profile(token_address, position, market_data)
            
            if profile.unrealized_pnl_pct > 0.1:  # 10%+ gain
                winners.append(profile)
                self.current_winners[token_address] = profile
                
                # Check for scale-up opportunity
                if self._should_scale_up(profile):
                    scale_up_candidates.append(profile)
                
                # Check for exit signals
                if self._should_exit_winner(profile):
                    exit_candidates.append(profile)
            
            elif profile.momentum_score > 0.7:  # High momentum but not yet winner
                potential_winners.append(profile)
        
        # Analyze patterns in winners
        patterns = self._analyze_winner_patterns(winners)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            winners, potential_winners, exit_candidates, scale_up_candidates, patterns
        )
        
        return {
            'winners': winners,
            'potential_winners': potential_winners,
            'exit_candidates': exit_candidates,
            'scale_up_candidates': scale_up_candidates,
            'patterns': patterns,
            'recommendations': recommendations,
            'portfolio_edge': self._calculate_portfolio_edge(winners, positions)
        }
    
    async def _create_winner_profile(self, token_address: str, position: Dict, market_data: Dict) -> WinnerProfile:
        """Create a detailed winner profile"""
        # Get current market data
        current_data = market_data.get(token_address, {})
        
        entry_price = position.get('entry_price', position.get('avg_price', 0))
        current_price = current_data.get('price', entry_price)
        
        # Calculate P&L
        position_value = position['amount'] * current_price
        entry_value = position['amount'] * entry_price
        unrealized_pnl = position_value - entry_value
        unrealized_pnl_pct = (current_price / entry_price - 1) if entry_price > 0 else 0
        
        # Get historical data for peak price
        history = await self._get_position_history(token_address, position['entry_time'])
        peak_price = history['price'].max() if not history.empty else current_price
        
        # Calculate momentum
        momentum_score = self._calculate_momentum_score(history, current_data)
        
        return WinnerProfile(
            token_address=token_address,
            entry_time=position['entry_time'],
            entry_price=entry_price,
            current_price=current_price,
            peak_price=peak_price,
            position_size=position['amount'],
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            peak_pnl_pct=(peak_price / entry_price - 1) if entry_price > 0 else 0,
            strategy_used=position.get('strategy', 'unknown'),
            entry_signals=position.get('entry_signals', {}),
            momentum_score=momentum_score,
            time_held=datetime.now(timezone.utc) - position['entry_time']
        )
    
    def _calculate_momentum_score(self, history: pd.DataFrame, current_data: Dict) -> float:
        """Calculate momentum score for a position"""
        if history.empty:
            return 0.5
        
        scores = []
        
        # Price momentum
        if len(history) > 20:
            returns_5d = history['price'].pct_change(5).iloc[-1]
            returns_10d = history['price'].pct_change(10).iloc[-1]
            returns_20d = history['price'].pct_change(20).iloc[-1]
            
            price_momentum = (returns_5d * 0.5 + returns_10d * 0.3 + returns_20d * 0.2)
            scores.append(np.clip(price_momentum * 10, 0, 1))
        
        # Volume momentum
        if 'volume' in history.columns and len(history) > 5:
            vol_ratio = history['volume'].iloc[-1] / history['volume'].iloc[-5:].mean()
            scores.append(np.clip(vol_ratio / 3, 0, 1))
        
        # Social momentum (if available)
        if 'social_score' in current_data:
            scores.append(np.clip(current_data['social_score'], 0, 1))
        
        return np.mean(scores) if scores else 0.5
    
    def _should_scale_up(self, profile: WinnerProfile) -> bool:
        """Determine if position should be scaled up"""
        if not self.winner_config.get('enabled', True):
            return False
        
        # Criteria for scaling up
        criteria = [
            profile.unrealized_pnl_pct > 0.3,  # 30%+ gain
            profile.momentum_score > 0.7,  # Strong momentum
            profile.drawdown_from_peak < 0.1,  # Not in significant drawdown
            profile.time_held.days < 7,  # Not too old
            not profile.is_super_winner  # Not already a huge winner
        ]
        
        return all(criteria)
    
    def _should_exit_winner(self, profile: WinnerProfile) -> bool:
        """Determine if winning position should be exited"""
        # Exit criteria
        exit_signals = []
        
        # Major drawdown from peak
        if profile.drawdown_from_peak > 0.2 and profile.peak_pnl_pct > 0.5:
            exit_signals.append("20% drawdown from peak")
        
        # Momentum reversal
        if profile.momentum_score < 0.3 and profile.unrealized_pnl_pct > 0.5:
            exit_signals.append("Momentum reversal")
        
        # Time-based exit for super winners
        if profile.is_super_winner and profile.time_held.days > 14:
            exit_signals.append("Super winner time limit")
        
        # Pattern-based exit
        if self._check_exit_patterns(profile):
            exit_signals.append("Exit pattern detected")
        
        profile.exit_signals = exit_signals
        return len(exit_signals) > 0
    
    def _check_exit_patterns(self, profile: WinnerProfile) -> bool:
        """Check for known exit patterns"""
        # This would check historical patterns
        # For now, simplified logic
        return profile.unrealized_pnl_pct > 5.0  # 500%+ gains
    
    def _analyze_winner_patterns(self, winners: List[WinnerProfile]) -> Dict:
        """Analyze patterns in winning trades"""
        patterns = {
            'common_entry_signals': defaultdict(int),
            'average_hold_time': timedelta(),
            'average_peak_gain': 0.0,
            'strategy_performance': defaultdict(list),
            'time_patterns': defaultdict(list),
            'super_winner_characteristics': []
        }
        
        if not winners:
            return patterns
        
        # Analyze entry signals
        for winner in winners:
            for signal, value in winner.entry_signals.items():
                if value > 0.5:  # Positive signal
                    patterns['common_entry_signals'][signal] += 1
            
            # Strategy performance
            patterns['strategy_performance'][winner.strategy_used].append(winner.unrealized_pnl_pct)
            
            # Time patterns
            hour = winner.entry_time.hour
            patterns['time_patterns'][hour].append(winner.unrealized_pnl_pct)
        
        # Calculate averages
        patterns['average_hold_time'] = sum([w.time_held for w in winners], timedelta()) / len(winners)
        patterns['average_peak_gain'] = np.mean([w.peak_pnl_pct for w in winners])
        
        # Identify super winner characteristics
        super_winners = [w for w in winners if w.is_super_winner]
        if super_winners:
            patterns['super_winner_characteristics'] = self._extract_super_winner_patterns(super_winners)
        
        return patterns
    
    def _extract_super_winner_patterns(self, super_winners: List[WinnerProfile]) -> List[Dict]:
        """Extract patterns from super winners"""
        patterns = []
        
        # Common characteristics
        common_signals = defaultdict(int)
        for winner in super_winners:
            for signal, value in winner.entry_signals.items():
                if value > 0.7:
                    common_signals[signal] += 1
        
        # Find most common signals
        total_winners = len(super_winners)
        for signal, count in common_signals.items():
            if count / total_winners > 0.6:  # Present in 60%+ of super winners
                patterns.append({
                    'type': 'entry_signal',
                    'signal': signal,
                    'frequency': count / total_winners
                })
        
        # Average characteristics
        avg_entry_momentum = np.mean([w.entry_signals.get('momentum', 0) for w in super_winners])
        if avg_entry_momentum > 0.7:
            patterns.append({
                'type': 'momentum',
                'value': avg_entry_momentum,
                'description': 'High entry momentum common in super winners'
            })
        
        # Save patterns for future use
        self._save_super_winner_patterns(patterns)
        
        return patterns
    
    def _generate_recommendations(self, winners: List[WinnerProfile], 
                                potential_winners: List[WinnerProfile],
                                exit_candidates: List[WinnerProfile],
                                scale_up_candidates: List[WinnerProfile],
                                patterns: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Exit recommendations (highest priority)
        for profile in exit_candidates:
            recommendations.append({
                'action': 'EXIT',
                'token': profile.token_address,
                'urgency': 'HIGH',
                'reason': ', '.join(profile.exit_signals),
                'current_pnl': f"{profile.unrealized_pnl_pct:.1%}",
                'position_size': profile.position_size
            })
        
        # Scale up recommendations
        for profile in scale_up_candidates:
            scale_factor = self._calculate_scale_factor(profile)
            recommendations.append({
                'action': 'SCALE_UP',
                'token': profile.token_address,
                'urgency': 'MEDIUM',
                'scale_factor': scale_factor,
                'reason': f"Strong momentum ({profile.momentum_score:.2f}) with {profile.unrealized_pnl_pct:.1%} gain",
                'additional_size': profile.position_size * (scale_factor - 1)
            })
        
        # New position recommendations based on patterns
        if patterns['super_winner_characteristics']:
            # Find tokens matching super winner patterns
            matching_tokens = self._find_pattern_matches(patterns['super_winner_characteristics'])
            for token in matching_tokens[:3]:  # Top 3 matches
                recommendations.append({
                    'action': 'ENTER',
                    'token': token['address'],
                    'urgency': 'LOW',
                    'reason': f"Matches super winner pattern with {token['confidence']:.1%} confidence",
                    'suggested_size': 'standard'
                })
        
        # Portfolio rebalancing
        if self._needs_winner_rebalancing(winners):
            recommendations.append({
                'action': 'REBALANCE',
                'urgency': 'LOW',
                'reason': 'Rebalance to maintain winner exposure',
                'details': self._get_rebalancing_details(winners)
            })
        
        return sorted(recommendations, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['urgency']])
    
    def _calculate_scale_factor(self, profile: WinnerProfile) -> float:
        """Calculate how much to scale up a winning position"""
        base_scale = self.winner_config.get('scale_factor', 1.5)
        max_scale = self.winner_config.get('max_scale', 3.0)
        
        # Adjust based on momentum
        momentum_multiplier = 1 + (profile.momentum_score - 0.5)
        
        # Adjust based on gain (less scaling for bigger winners)
        gain_