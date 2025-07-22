from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse

@dataclass
class Candle:
    """
    A Candle object represents a single candlestick in financial markets.
    It contains pricing and volume information for a specific time period.
    """

    timestamp: datetime  #: The date and time of the candle
    open: float          #: Opening price
    high: float          #: Highest price during the period
    low: float           #: Lowest price during the period
    close: float         #: Closing price
    volume: float = 0.0  #: Trading volume during the period
    
    
    def __post_init__(self):
            if not isinstance(self.timestamp, datetime):
                if isinstance(self.timestamp, str):
                    try:
                        self.timestamp = parse(self.timestamp)
                    except (ValueError, OverflowError) as e:
                        raise ValueError(f"Cannot parse timestamp string '{self.timestamp}': {e}")
                else:
                    raise TypeError(f"timestamp must be datetime or string, got {type(self.timestamp)}")

            prices = [self.open, self.high, self.low, self.close]
            if any(p < 0 for p in prices):
                raise ValueError("Prices must be non-negative")

            if not (self.low <= self.open <= self.high):
                raise ValueError(f"Open price {self.open} not between Low {self.low} and High {self.high}")

            if not (self.low <= self.close <= self.high):
                raise ValueError(f"Close price {self.close} not between Low {self.low} and High {self.high}")

            if self.low > self.high:
                raise ValueError(f"Low price {self.low} cannot be higher than High {self.high}")

            if self.volume < 0:
                raise ValueError(f"Volume cannot be negative, got {self.volume}")
            
            
    def is_bullish(self) -> bool:
        """
        Check if the candle is bullish.
        A bullish candle has a closing price higher than the opening price.
        """
        return self.close > self.open

    def is_bearish(self) -> bool:
        """
        Check if the candle is bearish.
        A bearish candle has a closing price lower than the opening price.
        """
        return self.open > self.close

    def body_size(self) -> float:
        """
        Return the size of the candle body.
        Calculated as the absolute difference between open and close.
        """
        return abs(self.close - self.open)

    def upper_shadow(self) -> float:
        """
        Return the length of the upper shadow (wick).
        Calculated as: high - max(open, close).
        """
        return self.high - max(self.open, self.close)

    def lower_shadow(self) -> float:
        """
        Return the length of the lower shadow (wick).
        Calculated as: min(open, close) - low.
        """
        return min(self.open, self.close) - self.low

    def total_range(self) -> float:
        """
        Return the total price range of the candle.
        Calculated as: high - low.
        """
        return self.high - self.low

    def typical_price(self) -> float:
        """
        Return the typical price of the candle.
        Formula: (high + low + close) / 3
        """
        return (self.high + self.low + self.close) / 3

    def median_price(self) -> float:
        """
        Return the median price of the candle.
        Formula: (high + low) / 2
        """
        return (self.high + self.low) / 2

    def weighted_close(self) -> float:
        """
        Return the weighted closing price.
        Formula: (high + low + 2 * close) / 4
        """
        return (self.high + self.low + 2 * self.close) / 4

    def price_change(self) -> float:
        """
        Return the absolute price change from open to close.
        Formula: close - open
        """
        return self.close - self.open

    def price_change_pct(self) -> float:
        """
        Return the percentage price change from open to close.
        Formula: (close - open) / open
        Returns 0 if open == 0 to avoid division by zero.
        """
        return (self.close - self.open) / self.open if self.open != 0 else 0.0

    def money_flow_multiplier(self) -> float:
        """
        Return the Money Flow Multiplier (MFM).
        Measures buying/selling pressure in the candle.

        Formula:
            ((close - low) - (high - close)) / (high - low)

        Returns 0.0 if high == low to prevent division by zero.
        """
        if self.high != self.low:
            return ((self.close - self.low) - (self.high - self.close)) / (self.high - self.low)
        return 0.0

    def money_flow_volume(self) -> float:
        """
        Return the Money Flow Volume (MFV).
        Calculated as: MFM * volume
        """
        if self.volume == 0:
            raise ValueError(f"Volume cannot be zero when calculating MFV")
        return self.money_flow_multiplier() * self.volume

    def is_doji(self, threshold: float = 0.1) -> bool:
        """
        Check if the candle is a Doji.
        A Doji has a very small body, indicating indecision in the market.

        Parameters:
        - threshold (float): Relative size of the body compared to total range. Default is 0.1 (10%).

        Returns:
        - True if the body is smaller than threshold × total_range
        """
        return self.body_size() <= threshold * self.total_range()

    def is_marubozu(self, threshold: float = 0.05) -> bool:
        """
        Check if the candle is a Marubozu.
        A Marubozu has no upper or lower shadows (pure body).

        Parameters:
        - threshold (float): Maximum allowed shadow as a percentage of total range.

        Returns:
        - True if both shadows are smaller than threshold × total_range
        """
        return self.upper_shadow() <= threshold * self.total_range() and self.lower_shadow() <= threshold * self.total_range()

    def is_hammer(self) -> bool:
        """
        Detect Hammer pattern.
        Has a small body near the top with a long lower shadow.
        Indicates potential bullish reversal.

        Returns:
        - True if lower shadow > 2 × body and upper shadow < body
        """
        return self.lower_shadow() > 2 * self.body_size() and self.upper_shadow() < self.body_size()

    def is_inverted_hammer(self) -> bool:
        """
        Detect Inverted Hammer pattern.
        Has a small body near the bottom with a long upper shadow.
        Indicates potential bearish reversal.

        Returns:
        - True if upper shadow > 2 × body and lower shadow < body
        """
        return self.upper_shadow() > 2 * self.body_size() and self.lower_shadow() < self.body_size()

    def hour(self) -> int:
        """
        Return the hour (0–23) of the candle's timestamp.
        Useful for intraday analysis.
        """
        return self.timestamp.hour

    def day_of_week(self) -> int:
        """
        Return the day of the week (0–6) of the candle's timestamp.
        Monday = 0, Sunday = 6.

        Useful for detecting weekly patterns.
        """
        return self.timestamp.weekday()
