from .base import Strategy
import pandas as pd
from marketlib.indicators import MACD
from typing import List, Literal
from marketlib.chart import LineLayer
from scipy.signal import find_peaks


class MACDDivergence(Strategy):
    """
    Strategy for detecting MACD divergences (Regular and Hidden) and generating discrete signals.

    Purpose:
    - Detect price highs/lows and MACD peaks on the corresponding side of zero.
    - Map each price extremum to the nearest MACD extremum within a small window.
    - Scan mapped pairs in time-order for divergence patterns:
        - Regular divergence (RD): price makes a higher high (sell) or lower low (buy) while MACD makes a lower high / higher low.
        - Hidden divergence (HD): price makes a lower high (sell) or higher low (buy) while MACD does the opposite.
    - Validate each MACD trendline segment between two mapped MACD peaks so that the MACD curve does not “break” the segment beyond tolerance.
    - Produce a signal series aligned to data.index, with values in {"buy", "sell", None}.

    Notes:
    - self.signals is expected to be a pd.Series initialized in Strategy, aligned to self.data.index and defaulting to None.
    - Lines for visualization are pushed into self.lines using LineLayer (price panel and MACD panel).
    """

    def __init__(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        on_col: Literal["close", "low", "high", "open"] = "close",
        interspace: int = 3,          # bars to wait after the second extremum before tagging the signal (visual/operational offset)
        treshhold: int = 60,          # max bar distance allowed between two extrema to be considered a valid pair candidate
        price_deep = None,               # minimum directed price difference required between two extrema (filters weak divergences)
        macd_deep = None,                # minimum directed MACD difference required between two extrema
        tolerance: float = 0.1,       # base factor for MACD line validation (if None, computed dynamically from range/volatility)
        macd_distance = 15,           # min distance between MACD peaks (scipy find_peaks)
        macd_prominence = None,       # required prominence for MACD peaks (if None, scaled to MACD range)
        price_distance = 7,           # min distance between price peaks (scipy find_peaks)
        price_prominence = None,      # required prominence for price peaks (if None, scaled to price range)
        type: Literal["rd", "hd"] = None,   # filter divergence type: "rd" (regular), "hd" (hidden), or None for both
        side: Literal["sell", "buy"] = None # filter side: "sell", "buy", or None for both
    ):
        super().__init__(data)

        # MACD instance: only_macd_line=True implies we operate primarily on the MACD line.
        self.macd = MACD(
            data,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            on_col=on_col,
            only_macd_line=True,
        )

        self.interspace = interspace
        self.side = "" if side is None else side   # empty string means both sides
        self.type = "" if type is None else type   # empty string means both RD and HD
        self.indicators.append(self.macd)

        self.treshhold = treshhold

        # Dynamic tolerance ingredients (if tolerance is None).
        # macd_range: spread of |MACD|; volatility: average absolute diff of MACD (noise/roughness proxy).
        macd_range = self.macd()["macd"].abs().max() - self.macd()["macd"].abs().min()
        volatility = self.macd().diff().abs().mean()
        price_range = data["close"].max() - data["close"].min()

        if tolerance is None:
            tolerance = 0.1 * macd_range + 0.5 * volatility
        self.tolerance = tolerance

        # Default prominence thresholds if not explicitly provided (scale-aware).
        if macd_prominence is None:
            macd_prominence = macd_range * 0.01  # 1% of MACD range
        if price_prominence is None:
            price_prominence = price_range * 0.01  # 1% of price range
            
        if price_deep is None:
            price_deep = price_range * 0.01
        
        if macd_deep is None:
            macd_deep = macd_range * 0.01

        self.macd_deep = macd_deep
        self.price_deep = price_deep
        self.macd_distance = macd_distance
        self.macd_prominence = macd_prominence
        self.price_distance = price_distance
        self.price_prominence = price_prominence

    def _find_exterma(self, curve: pd.Series, distance: int = 7, prominence: int = 60):
        """
        Find local maxima (peaks) in a 1D series using scipy.signal.find_peaks.

        Parameters:
        - curve: pd.Series (if lows are needed, pass a negated series such as -low)
        - distance: min horizontal distance (in bars) between accepted peaks
        - prominence: min prominence threshold for peaks (scale-dependent)

        Returns:
        - A list of integer indices for detected peaks.
        """
        if isinstance(curve, pd.DataFrame):
            # If a DataFrame is accidentally passed, take the first column as Series.
            curve = pd.Series(curve.iloc[:, 0])
        if not isinstance(curve, pd.Series):
            raise ValueError(f"curve must be a pd.Series not {type(curve)}")

        peaks, _ = find_peaks(curve, distance=distance, prominence=prominence)
        return peaks.tolist()

    def _map_extrema(
        self, price_extrema: list[int], macd_extrema: list[int], max_distance: int = 6
    ):
        """
        Map each price extremum to the nearest MACD extremum within a maximum bar distance.

        Parameters:
        - price_extrema: indices of price highs (for sell) or lows (for buy)
        - macd_extrema: indices of MACD highs (for sell) or lows (for buy) on the correct side of zero
        - max_distance: maximum allowed bar distance between matched extrema

        Returns:
        - List of (price_index, macd_index) pairs.
        """
        mapping = {}
        for p_idx in price_extrema:
            candidates = [m_idx for m_idx in macd_extrema if abs(m_idx - p_idx) <= max_distance]
            if not candidates:
                continue
            # Choose the closest MACD extremum to the price extremum.
            closest = min(candidates, key=lambda m_idx: abs(m_idx - p_idx))
            mapping[p_idx] = closest
        return list(mapping.items())

    def _divergence_detector(
        self,
        nearest_peaks: list,                   # list of (price_idx, macd_idx) in ascending time order
        side: Literal["sell", "buy"],
        tresh: int = 100,                      # max bar distance between the two extrema to be considered a pair
        price_diff: int = 0,                   # min directed change in price between pair1 and pair2
        macd_diff: int = 0,                    # min directed change in MACD between pair1 and pair2
        type: Literal["rd", "hd"] = "",        # filter divergence type if set
    ):
        """
        Scan mapped extrema and detect RD/HD divergences for the given side.
        For each valid divergence, validate the MACD straight line between the two MACD indices.
        If valid, append line layers and tag a signal at (second_price_index + interspace).

        Side conventions:
        - side == "sell": use price highs matched with MACD highs (MACD > 0 zone)
        - side == "buy" : use price lows matched with MACD lows (MACD < 0 zone)
        """
        price_rd = []
        macd_rd = []
        price_hd = []
        macd_hd = []

        # Compare every pair (i, k) with i < k; break early if temporal distance exceeds threshold.
        for i in range(0, len(nearest_peaks) - 1):
            p1, m1 = nearest_peaks[i]
            for k in range(i + 1, len(nearest_peaks)):
                p2, m2 = nearest_peaks[k]
                if p2 - p1 > tresh:
                    break

                # For sell, compare highs; for buy, compare lows.
                price1 = self.data.iloc[p1]["high" if side == "sell" else "low"]
                price2 = self.data.iloc[p2]["high" if side == "sell" else "low"]

                macd1 = self.macd().iloc[m1]["macd"]
                macd2 = self.macd().iloc[m2]["macd"]

                # Case A: price increases while MACD decreases (classic RD sell, HD buy depending on side)
                if (price2 - price1) > price_diff and (macd2 - macd1) < -macd_diff:
                    if side == "sell":
                        # Regular bearish divergence: HH in price, LH in MACD
                        if self._validat_macd_line(m1, m2):
                            price_rd.append([int(p1), int(p2)])
                            macd_rd.append([int(m1), int(m2)])
                            if type != "hd":
                                # Note: ensure p2 + interspace is within bounds in your base Strategy implementation.
                                if p2 + self.interspace < len(self.signals):
                                    self.signals.iloc[p2 + self.interspace] = "sell"
                    else:
                        # Hidden bullish divergence: HL in price, LL in MACD
                        if self._validat_macd_line(m1, m2):
                            price_hd.append([int(p1), int(p2)])
                            macd_hd.append([int(m1), int(m2)])
                            if type != "rd":
                                if p2 + self.interspace < len(self.signals):    
                                    self.signals.iloc[p2 + self.interspace] = "buy"

                # Case B: price decreases while MACD increases (classic RD buy, HD sell depending on side)
                if (price2 - price1) < -price_diff and (macd2 - macd1) > macd_diff:
                    if side == "buy":
                        # Regular bullish divergence: LL in price, HL in MACD
                        if self._validat_macd_line(m1, m2):
                            price_rd.append([int(p1), int(p2)])
                            macd_rd.append([int(m1), int(m2)])
                            if type != "hd":
                                if p2 + self.interspace < len(self.signals):
                                    self.signals.iloc[p2 + self.interspace] = "buy"
                    else:
                        # Hidden bearish divergence: LH in price, HH in MACD
                        if self._validat_macd_line(m1, m2):
                            price_hd.append([int(p1), int(p2)])
                            macd_hd.append([int(m1), int(m2)])
                            if type != "rd":
                                if p2 + self.interspace < len(self.signals):
                                    self.signals.iloc[p2 + self.interspace] = "sell"

        # Draw RD (solid) lines on price and MACD panels.
        if len(price_rd) != 0:
            l_price_rd = LineLayer()
            l_price_rd.set_parameters(
                price_rd,
                type="tline",
                tline_use="high" if side == "sell" else "low",
                color="b" if side == "buy" else "r",
            )
            l_macd_rd = LineLayer()
            l_macd_rd.set_parameters(
                macd_rd,
                type="tline",
                tline_use=0,   # use indicator panel values
                panel=1,       # MACD panel
                color="b" if side == "buy" else "r",
            )
            self.lines.append(l_price_rd)
            self.lines.append(l_macd_rd)

        # Draw HD (dashed) lines on price and MACD panels.
        if len(price_hd) != 0:
            l_price_hd = LineLayer()
            l_price_hd.set_parameters(
                price_hd,
                type="tline",
                tline_use="high" if side == "sell" else "low",
                color="b" if side == "buy" else "r",
                linestyle="--",
            )
            l_macd_hd = LineLayer()
            l_macd_hd.set_parameters(
                macd_hd,
                type="tline",
                tline_use=0,
                panel=1,
                linestyle="--",
                color="b" if side == "buy" else "r",
            )
            self.lines.append(l_price_hd)
            self.lines.append(l_macd_hd)

    def _line_between_points(self, x1, x2, y1, y2):
        """
        Build a straight line y = m*x + b between two points (x1, y1) and (x2, y2).
        Returns a callable f(x) for interpolation.

        Edge cases:
        - If x1 == x2 (vertical), returns NaN marker (caller should handle).
        - If y1 or y2 is NaN, raises ValueError.

        Important:
        - The original check duplicates y1: `if pd.isna(y1) or pd.isna(y1)`. This looks like a typo and
          probably should be `if pd.isna(y1) or pd.isna(y2)`. The logic is kept unchanged here.
        """
        if pd.isna(y1) or pd.isna(y1):  # likely intended: (pd.isna(y1) or pd.isna(y2))
            raise ValueError(f"invalid point y1 = {y1} , y2 = {y2}")
        if x1 == x2:
            return float("nan")
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        return lambda x: m * x + b

    def _validat_macd_line(self, m1, m2):
        """
        Validate the straight line segment between MACD[m1] and MACD[m2].

        Idea:
        - Construct the straight line across (m1, MACD[m1]) → (m2, MACD[m2]).
        - For i in (m1+1 .. m2-1), if the MACD curve deviates beyond a tolerance, reject the divergence.
        - Tolerance is scaled by the max(|MACD|) in [m1, m2).

        Note:
        - Current criterion uses: abs(MACD[i]) - abs(line(i)) > tolerance_val.
          Depending on your definition of "line break", you may consider using
          abs(MACD[i] - line(i)) > tolerance_val instead (symmetrical distance).
        """
        macd = self.macd()["macd"]
        tolerance_val = self.tolerance * macd.iloc[m1:m2].abs().max()

        line = self._line_between_points(m1, m2, macd.iloc[m1], macd.iloc[m2])
        for i in range(m1 + 1, m2):
            # If vertical line (NaN callable) or invalid state, reject.
            if pd.isna(line(i)):
                return False
            # Reject if deviation surpasses the tolerance envelope.
            if abs(macd.iloc[i]) - abs(line(i)) > tolerance_val:
                return False
        return True

    def generate_signals(self) -> pd.Series:
        """
        Generate a discrete signal series aligned to self.data.index.

        Returns:
        - pd.Series with values in {"buy", "sell", None}, where:
          - "buy"/"sell" marks the bar at (second extremum index + interspace) for a validated divergence.
          - None elsewhere.

        Pipeline:
        1) Detect price highs and lows:
           - highs from self.data["high"] as-is,
           - lows by detecting peaks on -self.data["low"].
        2) Detect MACD peaks on |MACD| for robustness; then split indices by MACD sign:
           - macd_high_peaks: indices where MACD > 0 (for sell/highs)
           - macd_low_peaks : indices where MACD < 0 (for buy/lows)
        3) Map nearest MACD peaks to price highs/lows (within a small bar window).
        4) Run divergence detection for buy and/or sell depending on self.side and self.type.
        5) Append chart layers for visualization and write signals at p2 + interspace.

        Important:
        - Ensure your base Strategy initializes self.signals with None and proper length.
        - If p2 + interspace exceeds the available index range, you should handle the bound in Strategy.
        """
        # 1) Price extrema (peaks on highs; peaks on -lows == troughs on lows)
        high_peaks = self._find_exterma(
            self.data["high"],
            distance=self.price_distance,
            prominence=self.price_prominence
        )
        low_peaks = self._find_exterma(
            self.data["low"].mul(-1),
            distance=self.price_distance,
            prominence=self.price_prominence
        )

        # 2) MACD extrema from |MACD|, then split by sign
        macd_peaks = self._find_exterma(
            self.macd().abs(),
            distance=self.macd_distance,
            prominence=self.macd_prominence
        )
        macd_df = self.macd()
        macd_low_peaks = []   # MACD < 0 (lows area)
        macd_high_peaks = []  # MACD > 0 (highs area)
        for idx in macd_peaks:
            if macd_df.iloc[idx]["macd"] < 0:
                macd_low_peaks.append(idx)
            if macd_df.iloc[idx]["macd"] > 0:
                macd_high_peaks.append(idx)

        # 3) Price↔MACD nearest mapping (within 6 bars by default)
        nearest_high = self._map_extrema(high_peaks, macd_high_peaks, max_distance=6)
        nearest_low = self._map_extrema(low_peaks, macd_low_peaks, max_distance=6)

        # 4) Detect divergences per side and type; write signals and draw lines
        if self.side == "":
            # Both sides
            self._divergence_detector(
                nearest_low,
                side="buy",
                tresh=self.treshhold,
                price_diff=self.price_deep,
                macd_diff=self.macd_deep,
                type=self.type,
            )
            self._divergence_detector(
                nearest_high,
                side="sell",
                tresh=self.treshhold,
                price_diff=self.price_deep,
                macd_diff=self.macd_deep,
                type=self.type,
            )
        else:
            # Single side
            if self.side == "buy":
                self._divergence_detector(
                    nearest_low,
                    side=self.side,
                    tresh=self.treshhold,
                    price_diff=self.price_deep,
                    macd_diff=self.macd_deep,
                    type=self.type,
                )
            elif self.side == "sell":
                self._divergence_detector(
                    nearest_high,
                    side=self.side,
                    tresh=self.treshhold,
                    price_diff=self.price_deep,
                    macd_diff=self.macd_deep,
                    type=self.type,
                )

        # 5) Return discrete signal series ("buy"/"sell"/None) aligned to chart bars
        return self.signals
