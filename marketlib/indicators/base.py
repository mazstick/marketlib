from abc import ABC, abstractmethod
from typing import Union, Optional
import pandas as pd
from marketlib.chart import IndicatorLayer

import mplfinance as mpf
import matplotlib.pyplot as plt


class Indicator(ABC):
    """
    Abstract base class for all indicators.

    Accepts either a pandas DataFrame containing candlestick data.
    Provides a common interface for calculating indicator values.
    """

    def __init__(self, candles: Union[pd.DataFrame]):
        
        from marketlib.plotly import layer

        self.layer = IndicatorLayer()
        self.plotly_layer = layer.IndicatorPlotlyLayer()
        
        if isinstance(candles, pd.DataFrame):
            df = candles
        else:
            raise TypeError("candles must be a pandas DataFrame")

        df.columns = df.columns.str.lower()

        if "datetime" in df.columns:
            df.set_index("datetime", inplace=True)

        required_columns = {"open", "high", "low", "close", "volume"}
        if not required_columns.issubset(set(df.columns)):
            raise ValueError(
                f"Input DataFrame must contain columns: {required_columns}"
            )

        self.candles = df.copy()

    def get_layer(self) -> IndicatorLayer:
        return self.layer

    def get_layer_parameters(self, with_data=False, start=0, end=None) -> dict:
        data = self.calculate()
        if end is None:
            end = len(data)
        param = self.layer.get_parameters()
        if with_data:
            param["data"] = data[start:end]
        return param


    @abstractmethod
    def calculate(self) -> Union[pd.Series, pd.DataFrame]:
        """
        Calculate the indicator values.

        Returns:
            pd.Series or pd.DataFrame: Indicator results aligned with the candles.
        """
        pass
    
    @abstractmethod
    def preset_layer(self):
        """
        Pre set indicator layer.
        
        """

    def __call__(self) -> Union[pd.Series, pd.DataFrame]:
        return self.calculate()
