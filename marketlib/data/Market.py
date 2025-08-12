import pandas as pd
from typing import List, Optional, Union, Literal
from .Candle import Candle
from marketlib.indicators import Indicator
import mplfinance as mpf


class Market:
    def __init__(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """
        Initialize the Market with raw candlestick data.

        Args:
            df (pd.DataFrame): DataFrame with at least columns
                ['datetime', 'open', 'high', 'low', 'close', 'volume'].
                The 'datetime' column should be timezone-aware or naive datetime.
            symbol (str): Trading symbol (e.g. 'BTCUSDT').
            timeframe (str): Timeframe string (e.g. '1h', '5m').

        This constructor converts the DataFrame into a list of Candle objects.
        """
        
        

        if df.empty:
            raise ValueError("Data Frame is empty.")

        df = df.copy()

        self._dataframe_cache = None
        self.symbol = symbol
        self.timeframe = timeframe
        self.indicators: List[Indicator] = []

        df.columns = df.columns.str.lower()

        if "datetime" in df.columns:
            df.set_index("datetime", inplace=True)
        elif 'time' in df.columns:
            df.set_index("time", inplace=True)
        elif 'date' in df.columns:
            df.set_index("date", inplace=True)
            
        df["close"] = df["close"].astype(float)
        df["low"] = df["low"].astype(float)
        df["high"] = df["high"].astype(float)
        df["open"] = df["open"].astype(float)


        df.index.name = df.index.name.lower()

        df.index = pd.to_datetime(df.index)

        df = df.reset_index()

        self.candles: List[Candle] = []
        for _, row in df.iterrows():
            candle = Candle(
                timestamp=row["datetime"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row.get("volume", 0.0),
            )
            self.candles.append(candle)

        self.addplot = []

    def get_candles(self):
        """
        Retrieve the list of Candle objects stored in the market.

        Returns:
            List[Candle]: A list of Candle instances representing market data.

        Raises:
            ValueError: If no candle data is available.
        """
        if not hasattr(self, "candles") or self.candles is None:
            raise ValueError("No candle data found. Make sure to load data first.")

        if len(self.candles) == 0:
            raise ValueError("Candle list is empty. Cannot return empty data.")

        return self.candles.copy()

    def summary(self) -> dict:
        """
        Returns a summary of market behavior over the loaded candles.

        Summary includes:
        - number of candles
        - time span (start and end datetime)
        - average volume
        - volatility measures (average candle range)
        - bullish/bearish candle counts and ratio
        - other useful stats

        Returns:
            dict: Summary statistics.
        """
        if not self.candles:
            return {}

        start = self.candles[0].timestamp
        end = self.candles[-1].timestamp
        count = len(self.candles)
        avg_volume = sum(c.volume for c in self.candles) / count
        avg_range = sum(c.total_range() for c in self.candles) / count

        bullish_count = sum(1 for c in self.candles if c.is_bullish())
        bearish_count = sum(1 for c in self.candles if c.is_bearish())
        bullish_ratio = bullish_count / count if count else 0

        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_datetime": start,
            "end_datetime": end,
            "number_of_candles": count,
            "average_volume": avg_volume,
            "average_range": avg_range,
            "bullish_candles": bullish_count,
            "bearish_candles": bearish_count,
            "bullish_ratio": bullish_ratio,
        }


    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the internal candle list back to a pandas DataFrame,
        formatted for use with indicator libraries or plotting.

        Returns:
            pd.DataFrame: DataFrame indexed by datetime with columns:
                ['open', 'high', 'low', 'close', 'volume']
        """
        if self._dataframe_cache is None:
            data = {
                "datetime": [c.timestamp for c in self.candles],
                "open": [c.open for c in self.candles],
                "high": [c.high for c in self.candles],
                "low": [c.low for c in self.candles],
                "close": [c.close for c in self.candles],
                "volume": [c.volume for c in self.candles],
            }
            df = pd.DataFrame(data)
            df.set_index("datetime", inplace=True)
            self._dataframe_cache = df
            return df
        else:
            return self._dataframe_cache

    def get_volatility(self) -> Optional[float]:
        """
        Calculate and return the average volatility as the mean total range of candles.

        Returns:
            float or None: Average candle range (high - low), or None if no data.
        """
        if not self.candles:
            return None
        return sum(c.total_range() for c in self.candles) / len(self.candles)

    def get_volume_stats(self) -> dict:
        """
        Return basic volume statistics.

        Returns:
            dict: Dictionary with 'total_volume', 'average_volume', and 'max_volume'.
        """
        if not self.candles:
            return {}
        volumes = [c.volume for c in self.candles]
        return {
            "total_volume": sum(volumes),
            "average_volume": sum(volumes) / len(volumes),
            "max_volume": max(volumes),
        }

    def get_closes(self):
        """
        Return close prices of candels.

        Returns:
            pd.Dataframe: with columns = {["datetime", "close"]}.
        """
        if self._dataframe_cache is None:
            df = self.to_dataframe()
        df = self._dataframe_cache
        return pd.DataFrame(df["close"])

    def get_opens(self):
        """
        Return open prices of candels.

        Returns:
            pd.Dataframe: with columns = {["datetime", "open"]}.
        """
        if self._dataframe_cache is None:
            df = self.to_dataframe()
        df = self._dataframe_cache
        return pd.DataFrame(df["open"])

    def get_highs(self):
        """
        Return high prices of candels.

        Returns:
            pd.Dataframe: with columns = {["datetime", "high"]}.
        """
        if self._dataframe_cache is None:
            df = self.to_dataframe()
        df = self._dataframe_cache
        return pd.DataFrame(df["high"])

    def get_lows(self):
        """
        Return low prices of candels.

        Returns:
            pd.Dataframe: with columns = {["datetime", "low"]}.
        """
        if self._dataframe_cache is None:
            df = self.to_dataframe()
        df = self._dataframe_cache
        return pd.DataFrame(df["low"])

    def get_volumes(self):
        """
        Return volumes prices of candels.

        Returns:
            pd.Dataframe: with columns = {["datetime", "volume"]}.
        """
        if self._dataframe_cache is None:
            df = self.to_dataframe()
        df = self._dataframe_cache
        return pd.DataFrame(df["volume"])

    def get_candle_counts(self) -> dict:
        """
        Return counts of bullish, bearish, doji, and marubozu candles.

        Returns:
            dict: Counts for candle types.
        """
        if not self.candles:
            return {}

        counts = {
            "bullish": 0,
            "bearish": 0,
            "doji": 0,
            "marubozu": 0,
        }

        for c in self.candles:
            if c.is_bullish():
                counts["bullish"] += 1
            elif c.is_bearish():
                counts["bearish"] += 1
            if c.is_doji():
                counts["doji"] += 1
            if c.is_marubozu():
                counts["marubozu"] += 1

        return counts
