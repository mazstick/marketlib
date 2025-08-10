import pandas as pd
from typing import Union, Literal
from .base import Indicator

class BollingerBands(Indicator):
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
        candles: pd.DataFrame,
        period: int = 20,
        std_multiplier: float = 2.0,
        on_col: Union[Literal["open", "high", "low", "close", "volume"], str] = "close"
    ):
        super().__init__(candles)
        self.name = "BollingerBands"
        self.period = period
        self.std_multiplier = std_multiplier
        self.on_col = on_col
        self.result = None
        self.preset_layer()
        
    def preset_layer(self):
        self.layer.set_layer(label=["middle", "upper", "lower"], ylabel=self.name+" "+str(self.period), panel=0)

    def calculate(self) -> pd.DataFrame:
        if self.on_col not in self.candles.columns:
            raise ValueError(f"'{self.on_col}' column not found in candles DataFrame.")

        rolling = self.candles[self.on_col].rolling(window=self.period, min_periods=1)
        sma = rolling.mean()
        std = rolling.std()

        upper = sma + self.std_multiplier * std
        lower = sma - self.std_multiplier * std

        self.result = pd.DataFrame({
            "middle": sma,
            "upper": upper,
            "lower": lower
        }, index=self.candles.index)

        self.layer.label = list(self.result.columns)
        
        return self.result.bfill()

    def merg_to_candles(self) -> pd.DataFrame:
        if self.result is None:
            self.calculate()
        return pd.concat([self.candles, self.result], axis=1)
