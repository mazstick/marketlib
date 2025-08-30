import pandas as pd
from .Position import Position

class Portfolio():
    
    def __init__(self, asset:int, asset_ccy:str = "USDT"):
        self.asset = asset
        self.asset_ccy = asset_ccy
        self.unrealized_history = []
        self.realized_history = []
        self.positions:list[Position] = []
        
    def open_position(self,market, side, size, entry_price,entry_time,entry_order_type=None, stop=None, tp=None, contract_value=None, fee_in=None, risk_amount=None):
        
        d = dict(market=market,side=side,entry_order_type=entry_order_type, size=size,entry_price=entry_price, entry_time=entry_time, stop=stop, tp=tp, contract_value=contract_value, fee_in=fee_in, risk_amount=risk_amount)
        
        d = {k:v for k , v in d.items() if v is not None}
        p = Position(**d)
        self.positions.append(p)
        
    
        
    
        
        
        