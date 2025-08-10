import pandas as pd
from typing import Union, Literal
from .base import Indicator


class PATR(Indicator):

    def preset_layer(self):
        self.layer.set_layer(
            width=1.5,
            panel=1,
            ylabel=self.name,
            label=self.name + " " + str(self.period),
        )

    def __init__(
        self,
        candles: pd.DataFrame,
        period: int = 14,
        on: Literal["close", "high", "low", "open"] = "close",
        invers: bool = False,
    ):
        super().__init__(candles)
        self.name = "WD_inv" if invers else "WD"
        self.period = period
        self.result = None
        self.invers = invers
        self.on = on
        self.preset_layer()

    def calculate(self) -> pd.DataFrame:
        high = self.candles["high"]
        low = self.candles["low"]
        close = self.candles["close"]
        open = self.candles["open"]

        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
        ).max(axis=1)
        
        tr = tr.rolling(window=self.period, min_periods=1).sum()
        tr_frame = tr.to_frame().reset_index()
        

        self.result = pd.Series()
        for i in range(len(tr_frame)):
            if i < self.period:
                self.result[tr_frame.iloc[i,0]] = float("nan")
            else:
                sum_tr = tr_frame.iloc[i-self.period:i].iloc[:,1].sum()
                delta_p = self.candles.iloc[i][self.on] - self.candles.iloc[i-self.period][self.on]
                wd = sum_tr / delta_p if delta_p != 0 else 0
                if self.invers:
                    self.result[tr_frame.iloc[i,0]] = (1.0/ wd) if wd != 0 else 0
                else:
                    self.result[tr_frame.iloc[i,0]] = wd

                    
        self.result.name = "PATR"
        return self.result
        # return pd.concat([self.result, ])

    def merg_to_candles(self) -> pd.DataFrame:
        if self.result is None:
            self.calculate()
        return pd.concat([self.candles, self.result], axis=1)
