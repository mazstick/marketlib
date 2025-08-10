import pandas as pd
from typing import Literal, Union
from .base import Indicator 

class PriceStdDev(Indicator):
    """
    Price Standard Deviation Indicator.

    Calculates rolling standard deviation over a specified period.

    Parameters:
    - candles: pd.DataFrame containing OHLCV data
    - period: int, window length for standard deviation (default=20)
    - on_col: which column to use (open, high, low, close, volume)

    Returns:
    - pd.Series: standard deviation values
    """

    def __init__(
        self,
        candles: pd.DataFrame,
        period: int = 20,
        on_col: Union[Literal["open", "high", "low", "close", "volume"], str] = "close"
    ):
        super().__init__(candles)
        self.name = "PriceStdDev"
        self.period = period
        self.on_col = on_col
        self.result = None
        self.preset_layer()
        
    def preset_layer(self):
        self.layer.set_layer(label=self.name, panel=1, ylabel=self.name+" "+str(self.period))

    def calculate(self) -> pd.DataFrame:
        if self.on_col not in self.candles.columns:
            raise ValueError(f"'{self.on_col}' column not found in candles DataFrame.")

        std = self.candles[self.on_col].rolling(window=self.period, min_periods=1).std()
        col_name = f"std_{self.period}_{self.on_col}" if self.on_col != "close" else f"std_{self.period}"
        self.result = pd.DataFrame({col_name: std}, index=self.candles.index)
        return self.result.bfill()

    def merg_to_candles(self) -> pd.DataFrame:
        if self.result is None:
            self.calculate()
        return pd.concat([self.candles, self.result], axis=1)
