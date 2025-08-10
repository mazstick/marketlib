import pandas as pd
from typing import Literal, Union
from .base import Indicator


class MACD(Indicator):
    """
    Moving Average Convergence Divergence (MACD) indicator.

    Calculates MACD line, Signal line, and Histogram based on selected price column.

    Parameters:
        candles (pd.DataFrame): DataFrame with OHLCV columns.
        fast_period (int): Fast EMA period (default: 12).
        slow_period (int): Slow EMA period (default: 26).
        signal_period (int): Signal EMA period (default: 9).
        on_col (str): Price column to calculate MACD on (default: "close").

    Raises:
        ValueError: If parameters are invalid or column is missing.
    """

    def __init__(
        self,
        candles: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        on_col: Union[Literal["open", "high", "low", "close", "volume"], str] = "close",
        hist_only: bool = False,
    ):
        super().__init__(candles)

        self.name = "MACD"
        self.result = None
        self.on_col = on_col
        self.hist_only = hist_only

        if self.on_col not in self.candles.columns:
            raise ValueError(
                f"Column '{self.on_col}' not found in input data. Available columns: {list(self.candles.columns)}"
            )

        if not all(
            isinstance(p, int) and p > 0
            for p in [fast_period, slow_period, signal_period]
        ):
            raise ValueError("All periods must be positive integers.")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

        self.preset_layer()

    def preset_layer(self):
        self.layer.set_layer(
            label=[
                self.name + " line",
                self.name + " signal",
                self.name + " histogram",
            ] if not self.hist_only else self.name,
            type="bar" if self.hist_only else "line",
            ylabel=f"{self.name} ({self.fast_period},{self.slow_period},{self.signal_period})",
            panel=1,
            width=.5 if self.hist_only else 1
        )

    def calculate(self) -> pd.DataFrame:
        """
        Calculates MACD line, Signal line, and Histogram.

        Returns:
            pd.DataFrame: DataFrame with columns ['macd', 'signal', 'histogram'].
        """
        price = self.candles[self.on_col]
        ema_fast = price.ewm(span=self.fast_period, adjust=False, min_periods=1).mean()
        ema_slow = price.ewm(span=self.slow_period, adjust=False, min_periods=1).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(
            span=self.signal_period, adjust=False, min_periods=1
        ).mean()
        histogram = macd_line - signal_line

        self.result = pd.DataFrame(
            {"macd": macd_line, "signal": signal_line, "histogram": histogram},
            index=self.candles.index,
        )

        if self.hist_only:
            return self.result["histogram"].to_frame()
        else:
            return self.result

    def merg_to_candles(self) -> pd.DataFrame:
        """
        Merge MACD results with original candles.

        Returns:
            pd.DataFrame: Merged DataFrame.

        Raises:
            RuntimeError: If calculation failed.
        """
        if self.result is None:
            self.calculate()
        if self.result is None or self.result.empty:
            raise RuntimeError("MACD calculation failed. Result is empty.")
        return pd.concat([self.candles, self.result], axis=1)

    def __repr__(self):
        return f"<{self.name} fast={self.fast_period} slow={self.slow_period} signal={self.signal_period} on={self.on_col}>"
