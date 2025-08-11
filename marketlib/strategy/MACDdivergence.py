from .base import Strategy
import pandas as pd
from marketlib.indicators import MACD
from typing import List, Literal
from marketlib.chart import LineLayer
from scipy.signal import find_peaks


class MACDDivergence(Strategy):
    def __init__(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        on_col: Literal["close", "low", "high", "open"] = "close",
        interspace: int = 3,
        type: Literal["rd", "hd"] = None,
        side: Literal["sell", "buy"] = None,
    ):
        super().__init__(data)
        self.macd = MACD(
            data,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            on_col=on_col,
            only_macd_line=True,
        )
        self.interspace = interspace
        self.side = "" if side is None else side
        self.type = "" if type is None else type
        self.indicators.append(self.macd)

    def _find_exterma(self, curve: pd.Series, distance: int = 7, prominence: int = 60):

        if isinstance(curve, pd.DataFrame):
            curve = pd.Series(curve.iloc[:, 0])
        if not isinstance(curve, pd.Series):
            raise ValueError(f"curve must be a pd.Series not {type(curve)}")

        peaks, _ = find_peaks(curve, distance=distance, prominence=prominence)
        return peaks.tolist()

    def _map_extrema(
        self, price_extrema: list[int], macd_extrema: list[int], max_distance: int = 6
    ):
        mapping = {}
        for p_idx in price_extrema:
            candidates = [
                m_idx for m_idx in macd_extrema if abs(m_idx - p_idx) <= max_distance
            ]
            if not candidates:
                continue
            else:
                closest = min(candidates, key=lambda m_idx: abs(m_idx - p_idx))
                mapping[p_idx] = closest
        return list(mapping.items())

    def _divergence_detector(
        self,
        nearest_peaks: list,
        side: Literal["sell", "buy"],
        tresh: int = 100,
        price_diff: int = 0,
        macd_diff: int = 0,
        type: Literal["rd", "hd"] = "",
    ):
        price_rd = []
        macd_rd = []
        price_hd = []
        macd_hd = []

        for i in range(0, len(nearest_peaks)):
            p1, m1 = nearest_peaks[i]
            for k in range(i, len(nearest_peaks)):
                p2, m2 = nearest_peaks[k]
                if p2 - p1 > tresh:
                    break

                price1 = self.data.iloc[p1]["high" if side == "sell" else "low"]
                price2 = self.data.iloc[p2]["high" if side == "sell" else "low"]

                macd1 = self.macd().iloc[m1]["macd"]
                macd2 = self.macd().iloc[m2]["macd"]

                if price2 - price1 > price_diff and macd2 - macd1 < macd_diff:
                    if side == "sell":
                        price_rd.append([int(p1), int(p2)])
                        macd_rd.append([int(m1), int(m2)])
                        if type != "hd":
                            self.signals.iloc[p2 + self.interspace] = side
                    else:
                        price_hd.append([int(p1), int(p2)])
                        macd_hd.append([int(m1), int(m2)])
                        if type != "rd":
                            self.signals.iloc[p2 + self.interspace] = side

                if price2 - price1 < price_diff and macd2 - macd1 > macd_diff:
                    if side == "buy":
                        price_rd.append([int(p1), int(p2)])
                        macd_rd.append([int(m1), int(m2)])
                        if type != "hd":
                            self.signals.iloc[p2 + self.interspace] = side
                    else:
                        price_hd.append([int(p1), int(p2)])
                        macd_hd.append([int(m1), int(m2)])
                        if type != "rd":
                            self.signals.iloc[p2 + self.interspace] = side

        if len(price_rd) != 0:
            l_price_rd = LineLayer()
            l_price_rd.set_parameters(
                price_rd,
                type="tline",
                tline_use="low",
                color="b" if side == "buy" else "r",
            )
            l_macd_rd = LineLayer()
            l_macd_rd.set_parameters(
                macd_rd,
                type="tline",
                tline_use=0,
                panel=1,
                color="b" if side == "buy" else "r",
            )
            self.lines.append(l_price_rd)
            self.lines.append(l_macd_rd)
        if len(price_hd) != 0:
            l_price_hd = LineLayer()
            l_price_hd.set_parameters(
                price_rd,
                type="tline",
                tline_use="low",
                color="b" if side == "buy" else "r",
                linestyle="--",
            )
            l_macd_hd = LineLayer()
            l_macd_hd.set_parameters(
                macd_rd,
                type="tline",
                tline_use=0,
                panel=1,
                linestyle="--",
                color="b" if side == "buy" else "r",
            )
            self.lines.append(l_price_hd)
            self.lines.append(l_macd_hd)

    def generate_signals(self) -> pd.Series:

        high_peaks = self._find_exterma(self.data["high"], distance=7, prominence=60)
        low_peaks = self._find_exterma(
            self.data["low"].mul(-1), distance=7, prominence=60
        )

        macd_high_peaks = self._find_exterma(
            self.macd().loc[self.macd()["macd"] >= 0], distance=15, prominence=0
        )
        macd_low_peaks = self._find_exterma(
            self.macd().loc[self.macd()["macd"] < 0], distance=15, prominence=0
        )

        nearest_high = self._map_extrema(high_peaks, macd_high_peaks, max_distance=6)
        nearest_low = self._map_extrema(low_peaks, macd_low_peaks, max_distance=6)

        if self.side == "":
            self._divergence_detector(
                nearest_high,
                side="buy",
                tresh=100,
                price_diff=0,
                macd_diff=0,
                type=self.type,
            )
            self._divergence_detector(
                nearest_low,
                side="sell",
                tresh=100,
                price_diff=0,
                macd_diff=0,
                type=self.type,
            )
        else:
            if self.side == "buy":
                self._divergence_detector(
                    nearest_high,
                    side=self.side,
                    tresh=100,
                    price_diff=0,
                    macd_diff=0,
                    type=self.type,
                )
            elif self.side == "sell":
                self._divergence_detector(
                    nearest_low,
                    side=self.side,
                    tresh=100,
                    price_diff=0,
                    macd_diff=0,
                    type=self.type,
                )

        return self.signals
