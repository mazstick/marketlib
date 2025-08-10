import pandas as pd
from typing import Union, Literal
from .base import Indicator
from .BollingerBands import BollingerBands
from .SMA import SMA
from .ATR import ATR
from .EMA import EMA
class Custom(Indicator):
    """
    Bollinger Bands Indicator.

    Calculates upper, middle, and lower bands using SMA and standard deviation.

    Parameters:
    - candles: pd.DataFrame with OHLCV data
    - period: int, period for SMA and STD (default=20)
    - std_multiplier: float, how many std deviations from mean (default=2)
    - on_col: str, which price column to use (e.g. "close")

    Returns:
    - pd.DataFrame: with columns ['bb_upper', 'bb_middle', 'bb_lower']
    """

    def __init__(
        self,
        candles: pd.DataFrame
    ):
        super().__init__(candles)
        self.name = "open - close / volume"
        self.result = None
        
    def preset_layer(self):
        return super().preset_layer()

    def calculate(self) -> pd.DataFrame:

        self.result =  pow(ATR(self.candles, 8).calculate().iloc[:, 0], 2) * ( EMA(self.candles, on_col="volume", periods=8).calculate().iloc[:, 0] / abs(self.candles["high"] - self.candles["low"]))
        
        
        
        # bb = BollingerBands(self.candles)
        # x = 1 / (bb()["upper"] - bb()["lower"])
        
        # self.result = self.result * x
        
        # sma = self.candles["close"].rolling(20).mean()
        
        # self.result = self.result * (self.candles["close"] - sma)
        
        self.result = pd.DataFrame({
            "custom": self.result,
        }, index=self.candles.index)

        self.layer.label = list(self.result.columns)
        
        return self.result.bfill()

    def merg_to_candles(self) -> pd.DataFrame:
        if self.result is None:
            self.calculate()
        return pd.concat([self.candles, self.result], axis=1)
