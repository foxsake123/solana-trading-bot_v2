# monitoring/performance_tracker.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Track and analyze bot performance metrics"""
    
    def __init__(self, db):
        self.db = db
        self.current_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl_sol': 0.0,
            'win_rate': 0.0
        }
    
    async def update_metrics(self, position_data: Dict):
        """Update performance metrics with closed position data"""
        if position_data['pnl_sol'] > 0:
            self.current_metrics['winning_trades'] += 1
        else:
            self.current_metrics['losing_trades'] += 1
        
        self.current_metrics['total_trades'] += 1
        self.current_metrics['total_pnl_sol'] += position_data['pnl_sol']
        
        # Calculate win rate
        if self.current_metrics['total_trades'] > 0:
            self.current_metrics['win_rate'] = (
                self.current_metrics['winning_trades'] / 
                self.current_metrics['total_trades'] * 100
            )
        
        # Save to database
        await self._save_metrics()
    
    async def _save_metrics(self):
        """Save current metrics to database"""
        self.db.save_performance_metrics(self.current_metrics)