import pandas as pd
from typing import Union, Literal
from .base import Indicator

class ATR(Indicator):
    """
    Average True Range (ATR) Indicator.

    Calculates ATR using either:
    - Simple Moving Average (SMA)
    - Wilder's Smoothing (loop-based or fast ewm-based)

    Parameters:
    - candles: pd.DataFrame with OHLC data
    - period: int, period for ATR (default=14)
    - method: 'sma' | 'wilder' (default='wilder')
    - fast_wilder: bool, use fast ewm approximation for Wilder method (default=False)
    """
    
    def preset_layer(self):
        self.layer.set_layer(width=1.5, panel=1, label=self.name, ylabel=self.name+" "+str(self.period))

    def __init__(
        self,
        candles: pd.DataFrame,
        period: int = 14,
        method: Literal["sma", "wilder"] = "wilder",
        fast_wilder: bool = False,
    ):
        super().__init__(candles)
        self.name = "ATR"
        self.period = period
        self.method = method.lower()
        self.fast_wilder = fast_wilder
        self.result = None
        self.preset_layer()

    def calculate(self) -> pd.DataFrame:
        high = self.candles["high"]
        low = self.candles["low"]
        close = self.candles["close"]

        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)

        if self.method == "sma":
            atr = tr.rolling(window=self.period, min_periods=1).mean()

        elif self.method == "wilder":
            if self.fast_wilder:
                alpha = 1 / self.period
                atr = tr.ewm(alpha=alpha, adjust=False).mean()
            else:
                atr = tr.copy()
                atr.iloc[0:self.period] = tr.iloc[0:self.period].mean()
                for i in range(self.period, len(tr)):
                    atr.iloc[i] = (atr.iloc[i - 1] * (self.period - 1) + tr.iloc[i]) / self.period
        else:
            raise ValueError("method must be either 'sma' or 'wilder'")

        self.result = pd.DataFrame({"atr": atr}, index=self.candles.index)
        return self.result

    def merg_to_candles(self) -> pd.DataFrame:
        if self.result is None:
            self.calculate()
        return pd.concat([self.candles, self.result], axis=1)
