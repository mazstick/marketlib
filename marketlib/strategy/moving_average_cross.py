from .base import Strategy
import pandas as pd
from marketlib.indicators import SMA

class MovingAverageCrossStrategy(Strategy):
    def __init__(self, data: pd.DataFrame, short_window: int = 20, long_window: int = 50):
        super().__init__(data)
        self.short_window = short_window
        self.long_window = long_window
        
        short = SMA(self.data, self.short_window)
        long = SMA(self.data, self.long_window)
        
        self.indicators.append(short)
        self.indicators.append(long)

    def generate_signals(self) -> pd.Series:
        
        short_ma = self.indicators[0]().iloc[:, 0]
        long_ma = self.indicators[1]().iloc[:, 0]

        self.signals = pd.Series(self.signals, dtype='object')
        
        self.signals[(short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))] = 'buy'
        self.signals[(short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))] = 'sell'
        return self.signals
