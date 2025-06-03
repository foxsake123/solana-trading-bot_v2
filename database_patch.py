#!/usr/bin/env python3
"""
Runtime patch to make database.record_trade accept is_simulation parameter
Add this to your startup script
"""
import types

def patch_database_record_trade(db):
    """Patch the database to accept is_simulation parameter"""
    
    # Save original method
    original_record_trade = db.record_trade
    
    # Create new method that accepts and ignores is_simulation
    def record_trade_with_simulation(self, contract_address, action, amount, price, 
                                    tx_hash=None, gain_loss_sol=0.0, 
                                    percentage_change=0.0, price_multiple=1.0, 
                                    is_simulation=None, **kwargs):
        """Modified record_trade that accepts is_simulation parameter"""
        # Just ignore is_simulation and call original method
        return original_record_trade(
            contract_address, action, amount, price, tx_hash,
            gain_loss_sol, percentage_change, price_multiple
        )
    
    # Replace method
    db.record_trade = types.MethodType(record_trade_with_simulation, db)
    print("✅ Patched database.record_trade to accept is_simulation parameter")

# Usage: 
# from database_patch import patch_database_record_trade
# patch_database_record_trade(db)
