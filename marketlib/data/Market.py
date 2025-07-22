import pandas as pd
from typing import List, Optional, Union, Literal
from .Candle import Candle
from marketlib.indicators import Indicator
from marketlib.chart import PriceLayer
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

        self.layer = PriceLayer()
        self._dataframe_cache = None
        self.symbol = symbol
        self.timeframe = timeframe
        self.indicators: List[Indicator] = []

        df.columns = df.columns.str.lower()

        if "datetime" in df.columns:
            df.set_index("datetime", inplace=True)

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

    def get_layer(self) -> PriceLayer:
        """
        Returns the main price layer object.

        Returns:
            PriceLayer: The main chart layer object containing all mplfinance plot settings.
        """
        return self.layer

    def get_layer_parameters(
        self,
        with_lines=True,
        with_indicator_addplots: bool = True,
        with_addplots = True,
        start: int = 0,
        end: Optional[int] = None,
    ) -> dict:
        """
        Generate a dictionary of parameters ready to be passed to `mpf.plot()`.

        Args:
            with_indicator_addplots (bool): Whether to include addplot layers for indicators.
            with_lines (bool): Whether to include lines.
            with_addplots (bool): Whether to include handly added addplots.
            start (int): Start index for slicing the cached DataFrame.
            end (int): End index (exclusive). If None, uses end of DataFrame.

        Returns:
            dict: Dictionary with all relevant parameters including `data` and `addplot` if selected.

        Raises:
            ValueError: If slicing indices are out of range.
        """
        if end is None:
            end = len(self._dataframe_cache)

        param = self.layer.get_parameters(with_lines=with_lines)

        if with_indicator_addplots:
            param["addplot"] = [
                mpf.make_addplot(
                    **p.get_layer_parameters(with_data=True, start=start, end=end)
                )
                for p in self.indicators
            ]

        if with_addplots and len(self.addplot) != 0:
            if with_indicator_addplots:
                param["addplot"].extend(self.addplot)
            else: 
                param["addplot"] = self.addplot
            
            
        
        param["data"] = self._dataframe_cache[start:end]

        return param


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
