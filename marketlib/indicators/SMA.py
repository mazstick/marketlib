import pandas as pd
from typing import Union, List, Literal
from .base import Indicator

class SMA(Indicator):
    """
    Simple Moving Average (SMA) indicator.

    Calculates the moving average of the selected price column over one or more periods.

    Parameters:
        candles (pd.DataFrame): DataFrame with columns like ['open', 'high', 'low', 'close', 'volume'].
        periods (int or list of int): Moving average period(s).
        on_col (str): The price column to calculate SMA on. Default is "close".

    Raises:
        ValueError: If the provided periods are invalid or the column does not exist.
    """

    def __init__(
        self,
        candles: pd.DataFrame,
        periods: Union[int, List[int]] = 14,
        on_col: Union[Literal["open", "high", "low", "close", "volume"], str] = "close"
    ):
        super().__init__(candles)

        self.name = "SMA"
        self.result = None
        self.on_col = on_col

        if self.on_col not in self.candles.columns:
            raise ValueError(f"Column '{self.on_col}' not found in input data. Available columns: {list(self.candles.columns)}")

        if isinstance(periods, int):
            if periods <= 0:
                raise ValueError("Period must be a positive integer.")
            self.periods = [periods]
        elif isinstance(periods, list) and all(isinstance(p, int) and p > 0 for p in periods):
            self.periods = periods
        else:
            raise ValueError("periods must be a positive int or a list of positive ints.")
        
        self.preset()

    def calculate(self) -> pd.DataFrame:
        """
        Calculates the SMA(s) based on the given periods and selected price column.

        Returns:
            pd.DataFrame: DataFrame with SMA column(s), indexed same as input.
        """
        result = {}
        for period in self.periods:
            sma = self.candles[self.on_col].rolling(window=period, min_periods=1).mean()
            if self.on_col != "close":
                result[f"sma_{period}_{self.on_col}"] = sma
            else:
                result[f"sma_{period}"] = sma

        self.result = pd.DataFrame(result, index=self.candles.index)
        return self.result



    def preset(self):
        self.layer.panel = 0
        
        
    def merg_to_candles(self) -> pd.DataFrame:
        """
        Merge the calculated SMA(s) with the original candle data.

        Returns:
            pd.DataFrame: Merged DataFrame with original and SMA columns.

        Raises:
            RuntimeError: If SMA calculation fails or result is not available.
        """
        if self.result is None:
            self.calculate()
        if self.result is None or self.result.empty:
            raise RuntimeError("SMA calculation failed. Result is empty.")
        merged_df = pd.concat([self.candles, self.result], axis=1)
        return merged_df
