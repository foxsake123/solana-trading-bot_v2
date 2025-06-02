# position_manager.py

import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Position data structure with accurate tracking"""
    position_id: str
    contract_address: str
    symbol: str
    entry_time: datetime
    entry_price: float
    entry_amount_sol: float
    entry_amount_tokens: float
    current_price: float = 0.0
    current_value_sol: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    trailing_stop_active: bool = False
    highest_price: float = 0.0
    pnl_sol: float = 0.0
    pnl_percent: float = 0.0
    status: str = "open"  # open, closed, partially_closed
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    
    def update_current_price(self, price: float):
        """Update position with current price"""
        self.current_price = price
        self.highest_price = max(self.highest_price, price)
        
        # Calculate current value in SOL
        # current_value = tokens * current_price_per_token
        # We need to convert token price to SOL terms
        self.current_value_sol = self.entry_amount_tokens * (price / self.entry_price) * self.entry_amount_sol
        
        # Calculate PnL
        self.pnl_sol = self.current_value_sol - self.entry_amount_sol
        self.pnl_percent = (self.pnl_sol / self.entry_amount_sol) * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['entry_time'] = self.entry_time.isoformat()
        if self.exit_time:
            data['exit_time'] = self.exit_time.isoformat()
        return data


class PositionManager:
    """Manages all trading positions with accurate tracking"""
    
    def __init__(self, db, risk_manager):
        self.db = db
        self.risk_manager = risk_manager
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self._load_positions()
    
    def _load_positions(self):
        """Load existing positions from database"""
        try:
            # Load open positions
            open_positions = self.db.get_open_positions()
            for pos_data in open_positions:
                position = self._position_from_db(pos_data)
                self.positions[position.position_id] = position
            
            logger.info(f"Loaded {len(self.positions)} open positions")
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
    
    def _position_from_db(self, data: Dict) -> Position:
        """Create Position object from database data"""
        return Position(
            position_id=data['position_id'],
            contract_address=data['contract_address'],
            symbol=data.get('symbol', 'UNKNOWN'),
            entry_time=datetime.fromisoformat(data['entry_time']),
            entry_price=float(data['entry_price']),
            entry_amount_sol=float(data['entry_amount_sol']),
            entry_amount_tokens=float(data['entry_amount_tokens']),
            current_price=float(data.get('current_price', data['entry_price'])),
            stop_loss=float(data.get('stop_loss', 0)),
            take_profit=float(data.get('take_profit', 0)),
            trailing_stop_active=bool(data.get('trailing_stop_active', False)),
            highest_price=float(data.get('highest_price', data['entry_price'])),
            status=data.get('status', 'open')
        )
    
    def open_position(self, 
                     contract_address: str,
                     symbol: str,
                     amount_sol: float,
                     entry_price: float,
                     token_data: Dict) -> Optional[Position]:
        """Open a new position with proper tracking"""
        
        try:
            # Generate position ID
            position_id = f"{contract_address[:8]}_{int(datetime.now().timestamp())}"
            
            # Calculate token amount
            # If entry_price is in USD, we need SOL price to calculate tokens
            sol_price_usd = token_data.get('sol_price_usd', 170.0)  # Get current SOL price
            token_price_in_sol = entry_price / sol_price_usd
            entry_amount_tokens = amount_sol / token_price_in_sol
            
            # Calculate stop loss and take profit
            volatility = token_data.get('volatility_24h', 20.0)
            stop_loss = self.risk_manager.calculate_stop_loss(entry_price, volatility)
            take_profit = entry_price * (1 + self.risk_manager.params.take_profit_pct)
            
            # Create position
            position = Position(
                position_id=position_id,
                contract_address=contract_address,
                symbol=symbol,
                entry_time=datetime.now(timezone.utc),
                entry_price=entry_price,
                entry_amount_sol=amount_sol,
                entry_amount_tokens=entry_amount_tokens,
                current_price=entry_price,
                current_value_sol=amount_sol,
                stop_loss=stop_loss,
                take_profit=take_profit,
                highest_price=entry_price
            )
            
            # Store position
            self.positions[position_id] = position
            self._save_position_to_db(position)
            
            logger.info(f"Opened position {position_id}: {amount_sol} SOL @ ${entry_price} "
                       f"({entry_amount_tokens:.2f} {symbol})")
            
            return position
            
        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None
    
    def update_positions(self, market_data: Dict[str, Dict]):
        """Update all positions with current market data"""
        
        for position_id, position in list(self.positions.items()):
            if position.contract_address in market_data:
                token_data = market_data[position.contract_address]
                current_price = token_data.get('price_usd', 0)
                
                if current_price > 0:
                    # Update position
                    position.update_current_price(current_price)
                    
                    # Check for trailing stop update
                    if self.risk_manager.params.trailing_stop_enabled:
                        new_stop = self.risk_manager.update_trailing_stop(
                            position_id, current_price
                        )
                        if new_stop and new_stop > position.stop_loss:
                            position.stop_loss = new_stop
                            position.trailing_stop_active = True
                    
                    # Check exit conditions
                    exit_reason = self._check_exit_conditions(position)
                    if exit_reason:
                        self.close_position(position_id, current_price, exit_reason)
    
    def _check_exit_conditions(self, position: Position) -> Optional[str]:
        """Check if position should be closed"""
        
        # Stop loss
        if position.current_price <= position.stop_loss:
            return "stop_loss"
        
        # Take profit
        if position.current_price >= position.take_profit:
            return "take_profit"
        
        # Time-based exit
        hold_time = (datetime.now(timezone.utc) - position.entry_time).total_seconds() / 3600
        if hold_time > self.risk_manager.params.max_hold_time_hours:
            return "max_hold_time"
        
        return None
    
    def close_position(self, 
                      position_id: str, 
                      exit_price: float,
                      exit_reason: str) -> Optional[Position]:
        """Close a position"""
        
        if position_id not in self.positions:
            logger.error(f"Position {position_id} not found")
            return None
        
        position = self.positions[position_id]
        position.exit_time = datetime.now(timezone.utc)
        position.exit_price = exit_price
        position.exit_reason = exit_reason
        position.status = "closed"
        
        # Final PnL calculation
        position.update_current_price(exit_price)
        
        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[position_id]
        
        # Update database
        self._update_position_in_db(position)
        
        # Update risk manager
        if position.pnl_sol < 0:
            self.risk_manager.daily_loss += abs(position.pnl_sol)
        
        logger.info(f"Closed position {position_id}: {exit_reason} @ ${exit_price:.6f} "
                   f"PnL: {position.pnl_sol:.4f} SOL ({position.pnl_percent:.2f}%)")
        
        return position
    
    def get_position_summary(self) -> Dict:
        """Get summary of all positions"""
        
        open_value = sum(p.current_value_sol for p in self.positions.values())
        open_pnl = sum(p.pnl_sol for p in self.positions.values())
        
        closed_pnl = sum(p.pnl_sol for p in self.closed_positions)
        win_rate = 0
        if self.closed_positions:
            wins = sum(1 for p in self.closed_positions if p.pnl_sol > 0)
            win_rate = wins / len(self.closed_positions) * 100
        
        return {
            'open_positions': len(self.positions),
            'open_value_sol': open_value,
            'open_pnl_sol': open_pnl,
            'closed_positions': len(self.closed_positions),
            'closed_pnl_sol': closed_pnl,
            'total_pnl_sol': open_pnl + closed_pnl,
            'win_rate_pct': win_rate,
            'positions': [p.to_dict() for p in self.positions.values()]
        }
    
    def _save_position_to_db(self, position: Position):
        """Save position to database"""
        self.db.save_position(position.to_dict())
    
    def _update_position_in_db(self, position: Position):
        """Update position in database"""
        self.db.update_position(position.to_dict())


# Example usage in trading bot
class ImprovedTradingBot:
    """Improved trading bot with accurate position tracking"""
    
    def __init__(self, config, db, token_scanner, trader):
        self.config = config
        self.db = db
        self.token_scanner = token_scanner
        self.trader = trader
        
        # Initialize managers
        self.risk_manager = RiskManager(
            TradingParameters(**config), 
            config.get('starting_balance', 10.0)
        )
        self.position_manager = PositionManager(db, self.risk_manager)
        
    async def execute_buy(self, token_data: Dict, confidence: float):
        """Execute buy with proper position tracking"""
        
        # Get current balance
        balance_sol, _ = await self.trader.get_wallet_balance()
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            current_balance=balance_sol,
            token_volatility=token_data.get('volatility_24h', 20.0),
            confidence_score=confidence
        )
        
        # Execute trade
        tx_hash = await self.trader.buy_token(
            token_data['contract_address'], 
            position_size
        )
        
        if tx_hash:
            # Open position with accurate price
            position = self.position_manager.open_position(
                contract_address=token_data['contract_address'],
                symbol=token_data.get('symbol', 'UNKNOWN'),
                amount_sol=position_size,
                entry_price=token_data['price_usd'],  # Use actual USD price
                token_data=token_data
            )
            
            logger.info(f"Buy executed: {position_size} SOL of {token_data['symbol']} "
                       f"@ ${token_data['price_usd']:.8f}")
