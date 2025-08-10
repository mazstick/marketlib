from abc import ABC, abstractmethod
import pandas as pd
from marketlib.indicators.base import Indicator


class Strategy(ABC):
    def __init__(self, data: pd.DataFrame):
        """
        Base strategy class.

        Args:
            data (pd.DataFrame): OHLCV market data.
        """
        self.data = data.copy()
        self.signals = pd.Series(index=data.index) 
        self.indicators = []

    @abstractmethod
    def generate_signals(self) -> pd.Series:
        """
        Generate trading signals.
        Must return a Series with 'buy'/'sell'/None.
        """
        pass

    def get_signals(self) -> pd.Series:
        if self.signals.isnull().all():
            self.signals = self.generate_signals()
        return self.signals
