from marketlib.chart import LineLayer
from marketlib.chart import FillBetweenLayer
from marketlib.chart import SignalLayer
from marketlib.chart import PriceLayer
from marketlib.strategy import Strategy
from typing import List, Literal, Union, Optional, Dict
import os
from marketlib.data import Market
from marketlib import indicators
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from datetime import datetime
from dateutil.parser import parse


class Chart:

    def __init__(self):
        self.chart: pd.DataFrame = None
        self.layer: PriceLayer = PriceLayer() 
        self.indicator_list: List[indicators.Indicator] = []
        self.line_list: List[LineLayer] = []
        self.addplot_list: List = []
        self.fillbetween_list: List[FillBetweenLayer] = []
        self.signal_list: List[SignalLayer] = []
        self.strategy_list: List[Strategy] = []

    def delete_lines(self):
        self.line_list = []

    def delete_indicators(self):
        self.indicator_list = []

    def delete_addplots(self):
        self.addplot_list = []

    def delete_fillbetweens(self):
        self.fillbetween_list = []

    def delete_signals(self):
        self.signal_list = []

    def delete_strategys(self):
        self.strategy_list = []

    def reset(self):
        self.line_list = []
        self.strategy_list = []
        self.signal_list = []
        self.addplot_list = []
        self.fillbetween_list = []
        self.indicator_list = []







    def add_signal(
        self,
        data: Union[pd.DataFrame, pd.Series],
        distance_mark: float = 0.001,
        position: Literal["sell", "buy"] = "buy",
        signal_use: Union[Literal["close", "high", "low", "open"], int, str] = None,
        label: Union[str, List[str], None] = None,
        color: Union[str, List[str], dict, None] = None,
        panel: int = 0,
        marker: Optional[str] = None,
        markersize: Optional[float] = 10,
        alpha: Optional[float] = 1.0,
        grid: bool = True,
        xlabel: str = None,
    ):
        """
        Configure the visualization layer to be used with mplfinance's addplot.

        Args:
            data: (pd.Series or pd.DataFrame) signal data to plot.
            distance_mark: (float) distance of marker from signal point.
            signal_use: (Literal["close", "high", "low","open"] or int or str) use whiche value to set the marker location for set on indicator use int number or column name.
            position: ("sell" or "buy") the position of your signal.
            label: (str or list) Label(s) to display in the legend.
            color: (str or list or dict) Color(s) for the series.
            panel: (int) Panel index. 0 = main chart, 1+ = additional panels.
            marker: (str) Marker symbol for scatter plot (e.g. 'o', '^', '*').
            markersize: (float) Size of marker points in scatter.
            alpha: (float) Transparency value (0 = transparent, 1 = opaque).

        Raises:
            ValueError: If any input is invalid.
        """
        s = SignalLayer()
        s.set_layer(
            data=data,
            distance_mark=distance_mark,
            label=label,
            signal_use=signal_use,
            color=color,
            position=position,
            panel=panel,
            marker=marker,
            markersize=markersize,
            alpha=alpha,
            grid=grid,
            xlabel=xlabel,
        )
        self.signal_list.append(s)

    def add_fiilbetween(
        self,
        y1: Union[int, float, pd.Series] = 0,
        y2: Union[int, float, pd.Series] = None,
        where: pd.Series = None,
        color: str = None,
        panel: int = 0,
        alpha: float = 0.7,
        interpolate: bool = True,
    ):
        """
        Adds a filled layer to the plot between y1 and y2, optionally controlled by a logical condition.

        Parameters
        ----------
        y1 : int | float | pd.Series
            The lower boundary of the fill. Can be a scalar or a Series. Default is 0.
        y2 : int | float | pd.Series
            The upper boundary of the fill. If None, it defaults to the same as y1.
        where : pd.Series of bool, optional
            Boolean mask to determine where to apply the fill.
        color : str, optional
            Fill color (hex code or color name). If None, a default gray will be used.
        panel : int, default=0
            Panel number (useful for subplots or multi-panel charts).
        alpha : float, default=0.7
            Transparency level of the fill (0 = transparent, 1 = opaque).
        interpolate : bool, default=True
            Whether to interpolate the intersection points between y1 and y2 when `where` changes.

        Raises
        ------
        TypeError
            If `y1`, `y2`, or `where` are not valid types.
        ValueError
            If the lengths of y1, y2, and where do not match.
        """

        f = FillBetweenLayer()
        f.set_layer(
            y1=y1,
            y2=y2,
            where=where,
            panel=panel,
            color=color,
            alpha=alpha,
            interpolate=interpolate,
        )
        self.fillbetween_list.append(f)

    def add_chart(self, chart: pd.DataFrame, symbol:str, timeframe:str):
        chart = chart.copy()
        if isinstance(chart, pd.DataFrame):
            if not set({'open', 'high', 'low', 'close', 'volume'}).issubset(set(chart.columns)) or type(chart.index) != datetime:
                self.timeframe = timeframe
                self.symbol = symbol
                self.chart = chart
            else:
                self.chart = chart
        else:
            raise ValueError(f"chart must be instance of pd.Dataframe not {type(chart)}")

    def add_indicator(self, indicator: indicators.Indicator):
        if isinstance(indicator, indicators.Indicator):
            self.indicator_list.append(indicator)
        else:
            raise ValueError(f"indicator must be instance of Indicator not {type(indicator)}")

    def add_strategy(self, strategy: Strategy):
        if self.chart is None:
            raise ValueError("chart is None please add chart:(pd.Dataframe) first.")

        self.strategy_list.append(strategy)

    def add_line(
        self,
        data: Union[List, int, float, str],
        type: Literal["vline", "hline", "aline", "tline"],
        linestyle: str = "-",
        color: Union[str, list] = "b",
        linewidth: float = 1.0,
        alpha: float = 0.5,
        panel: int = 0,
        tline_use: Union[
            Literal[
                "open",
                "close",
                "high",
                "low",
            ],
            int,
        ] = None,
    ) -> None:
        """
        Set the Line parameters.

        Args:
            type: The type of line ('vline', 'hline', 'aline', 'tline').
            data: Coordinates or values needed for the line.
            linestyle: Style of the line ('-', '--', '-.', ':').
            color: Color of the line.
            panel: Which panel the line shown in it.
            linewidth: Width of the line.
            alpha: Transparency of the line (0 = transparent, 1 = opaque).
        """

        l = LineLayer()
        l.set_parameters(
            type=type,
            data=data,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            alpha=alpha,
            panel=panel,
            tline_use=tline_use,
        )
        self.line_list.append(l)

    def add_plot(
        self,
        data,
        type: str = "line",
        label: Union[str, List[str], None] = None,
        color: Union[str, List[str], dict, None] = "b",
        ylabel: Optional[str] = None,
        panel: int = 1,
        width: Optional[float] = 1.0,
        linestyle: Union[str, List[str]] = "-",
        marker: Optional[str] = None,
        markersize: Optional[float] = 4,
        alpha: Optional[float] = 1.0,
        secondary_y: bool = False,
        ylim: Optional[tuple] = None,
    ):
        """
        Configure the visualization layer to be used with mplfinance's addplot.

        Args:
            type (str): Plot type. Options: 'line', 'scatter', 'step', or 'bar'. Default is 'line'.
            label (str or list): Label(s) to display in the legend.
            color (str or list or dict): Color(s) for the series.
            ylabel (str): Y-axis label for this panel.
            panel (int): Panel index. 0 = main chart, 1+ = additional panels.
            width (float): Line or bar width. Must be positive.
            linestyle (str or list): Line style ('-', '--', ':', etc.).
            marker (str): Marker symbol for scatter plot (e.g. 'o', '^', '*').
            markersize (float): Size of marker points in scatter.
            alpha (float): Transparency value (0 = transparent, 1 = opaque).
            secondary_y (bool): Whether to use a secondary y-axis on the same panel.
            ylim (tuple): Y-axis range as a tuple (min, max).

        Raises:
            ValueError: If any input is invalid.
        """

        valid_types = {"line", "scatter", "bar", "step"}
        if type not in valid_types:
            raise ValueError(f"'type' must be one of {valid_types}, not '{type}'")

        if not isinstance(panel, int) or panel < 0:
            raise ValueError("panel must be a non-negative integer.")

        if alpha is not None and not (0 <= alpha <= 1):
            raise ValueError("alpha must be between 0 and 1.")

        if width is not None and (not isinstance(width, (int, float)) or width <= 0):
            raise ValueError("width must be a positive number.")

        if ylim is not None and (not isinstance(ylim, tuple) or len(ylim) != 2):
            raise ValueError("ylim must be a tuple of (min, max)")

        r = dict(
            data=data,
            type=type,
            alpha=alpha,
            panel=panel,
            width=width,
            color=color,
            linestyle=linestyle,
            secondary_y=secondary_y,
        )

        if label is not None:
            r["label"] = label
        if ylim is not None:
            r["ylim"] = ylim
        if ylabel is not None:
            r["ylabel"] = ylabel
        if marker is not None:
            r["marker"] = marker
            r["markersize"] = markersize

        self.addplot_list.append(mpf.make_addplot(**r))

    def save_fig(
        self,
        path: str,
        start: int = 0,
        end: Optional[int] = None,
        with_indicator: bool = True,
        with_lines: bool = True,
        with_addplots: bool = True,
        with_fillbetweens: bool = True,
        with_signals: bool = True,
        with_strategy: bool = True,
        savefig_kwargs: Optional[Dict[str, Union[str, int, float, bool]]] = None
    ):
        """
        Save the chart with full control over matplotlib's savefig() parameters.

        Parameters:
        ----------
        path : str
            Full output path for the saved chart (e.g., 'charts/myplot.png').

        savefig_kwargs : dict, optional
            Dictionary of parameters passed to matplotlib.pyplot.savefig():
            - dpi : Resolution of the image (e.g., 300)
            - format : File format ('png', 'pdf', 'svg', etc.)
            - bbox_inches : Bounding box setting ('tight' to remove margins)
            - pad_inches : Padding around the figure
            - transparent : Set True for transparent background
            - metadata : Dictionary with metadata to embed
            - facecolor, edgecolor : Colors for background and border
            ... and any other valid savefig() parameter

        Example:
        --------
        savefig_kwargs = {
            'dpi': 400,
            'format': 'png',
            'transparent': True,
            'bbox_inches': 'tight',
            'pad_inches': 0.1
        }
        """

        save_config = {'fname': path}
        if isinstance(savefig_kwargs, dict):
            save_config.update(savefig_kwargs)

        try:
            self.plot(
                start=start,
                end=end,
                with_indicator=with_indicator,
                with_lines=with_lines,
                with_addplots=with_addplots,
                with_fillbetweens=with_fillbetweens,
                with_signals=with_signals,
                with_strategy=with_strategy,
                savefig=save_config
            )
        except Exception as e:
            raise RuntimeError(f"Error while saving chart: {e}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Chart saving failed — file not found at: '{path}'")

        print(f"Chart successfully saved to:\n{path}")


    def plot(
        self,
        start: int = 0,
        end: Optional[int] = None,
        with_indicator: bool = True,
        with_lines: bool = True,
        with_addplots: bool = True,
        with_fillbetweens: bool = True,
        with_signals: bool = True,
        with_strategy: bool = True,
        return_fig: bool = False,
        **kwargs,
    ):
        """
        Plot the full chart using mplfinance.

        Combines the main price layer and all indicator layers, sliced by given index range.

        Args:
            with_indicator_addplots (bool): Whether to include addplot layers for indicators.
            with_lines (bool): Whether to include line layers.
            with_addplots (bool): Whether to include addplot layers.
            start (int): Start index of the data to plot.
            end (int): End index (exclusive) of the data to plot.

        Returns:
            None
        """

        if self.chart is None:
            for indics in self.indicator_list:
                plt.figure(figsize=indics.layer.figsize)
                plt.plot(
                    indics.calculate().index,
                    indics.calculate().values,
                    label=indics().columns,
                    color=(
                        indics.layer.color
                        if isinstance(indics.layer.color, str)
                        else "blue"
                    ),
                    linestyle=indics.layer.linestyle,
                    alpha=indics.layer.alpha,
                )

                plt.xticks(rotation=indics.layer.x_rotation)
                plt.title(indics.name)
                plt.xlabel(indics.layer.xlabel)
                plt.ylabel(indics.layer.ylabel or "Indicator")
                plt.grid(indics.layer.grid)
                plt.legend()
                plt.tight_layout()
                plt.show()

            return

        if end is None:
            if self.chart is not None:
                end = len(self.chart)
            elif len(self.indicator_list):
                end = len(self.indicator_list[0].calculate())

        plots = []

        if with_strategy:
            for strategy in self.strategy_list:
                signals = strategy.generate_signals()
                temp_signal_layer = SignalLayer()
                temp_signal_layer.set_layer(
                    data=signals == "buy", position="buy", markersize=20
                )
                self.signal_list.append(temp_signal_layer)
                temp_signal_layer = SignalLayer()
                temp_signal_layer.set_layer(
                    data=signals == "sell", position="sell", markersize=20
                )
                self.signal_list.append(temp_signal_layer)

                self.indicator_list.extend(strategy.indicators)
                self.line_list.extend(strategy.lines)


        if with_indicator and len(self.indicator_list) != 0:
            for indics in self.indicator_list:
                ap = mpf.make_addplot(
                    data=indics.calculate()[start:end],
                    **indics.layer.get_parameters(),
                )
                plots.append(ap)

        if with_signals and len(self.signal_list) != 0:
            for signal in self.signal_list:
                if signal.data[start:end].all() == True:
                    continue
                plots.append(
                    mpf.make_addplot(
                        data=self._clean_signal_data(signal)[start:end],
                        **signal.get_parameters(),
                    )
                )

        if with_addplots and len(self.addplot_list) != 0:
            plots.extend(self.addplot_list)

        params = {}
        if len(plots) != 0:
            params["addplot"] = plots

        if with_fillbetweens and len(self.fillbetween_list) != 0:
            fl_list = []
            for fl in self.fillbetween_list:
                fl_list.append(fl.get_parameters())
            params["fill_between"] = fl_list
            
        
            
        if self.layer.title == None:
            self.layer.title = f"{self.symbol} {self.timeframe}"

        fig, axes = mpf.plot(
            data=self.chart[start:end],
            **self.layer.get_parameters(),
            **params,
            returnfig=True,
            **kwargs,
        )

        if with_lines:
            self.make_line_collection(self.line_list, axes, start=start)
            plt.show()
            
        
        if return_fig:    
            return fig, axes
        else:
            return

    def _clean_signal_data(self, signal: SignalLayer) -> pd.Series:

        data = signal.data
        use = signal.signal_use
        if use in ["close", "high", "low", "open"]:
            data = self.chart[use].mask(data) * (
                1 + signal.distance_mark
            )
            return data

        same_indicator_panel = 0
        if isinstance(use, int):
            for i in self.indicator_list:
                if signal.panel == i.layer.panel:
                    same_indicator_panel += 1
                    if use < len(i.calculate().columns):
                        data = i.calculate().mask(data).iloc[:, use] * (
                            1 + signal.distance_mark
                        )
                        return data
                    else:
                        use = use - len(i.calculate().columns)

            if same_indicator_panel == 0:
                raise ValueError(f"No indicator is in panel = {signal.panel}.")

            raise ValueError(f"the signal_use = {signal.signal_use} is out of bounds.")

        if isinstance(use, str):
            for i in self.indicator_list:
                if signal.panel == i.layer.panel:
                    same_indicator_panel += 1
                    if use in i.calculate().columns:
                        data = i.calculate()[use].mask(data)
                        return data

            if same_indicator_panel == 0:
                raise ValueError(f"No indicator is in panel = {signal.panel}.")

            raise ValueError(
                f"the signal_use = {signal.signal_use} is not in indicators columns name."
            )

    def _clean_line_data(self, line: LineLayer, ax, start:int) -> list[list[tuple]]:
        if line.type == "hline":
            if isinstance(line.data, (int, float)):
                return [[(0, line.data), (len(self.chart), line.data)]]
            elif isinstance(line.data, list):
                if len(line.data) == 1:
                    return [
                        [
                            (0, line.data[0]),
                            (len(self.chart), line.data[0]),
                        ]
                    ]
                else:
                    d = []
                    for i in line.data:
                        d.append([(0, i), (len(self.chart), i)])
                    return d
        elif line.type == "vline":
            if isinstance(line.data, list):
                d = []
                for l in line.data:
                    y_min, y_max = ax[line.panel * 2].get_ylim()
                    x = self._correct_x_linedata(l)
                    d.append([(x, y_min), (x, y_max)])
                return d
            else:
                x = self._correct_x_linedata(line.data)
                y_min, y_max = ax[line.panel * 2].get_ylim()
                return [[(x, y_min), (x, y_max)]]
        elif line.type == "aline":
            if isinstance(line.data, list):
                new_data = []
                tops = []
                for l in line.data:
                    if isinstance(l, tuple):
                        i, _ = l
                        i = self._correct_x_linedata(i)
                        tops.append((i, _))
                    elif isinstance(l, list):
                        temp = []
                        for h in l:
                            if isinstance(h, tuple):
                                i, _ = h
                                i = self._correct_x_linedata(i)
                                temp.append((i, _))
                        new_data.append(temp)

                if len(tops) != 0:
                    new_data.append(tops)

                return new_data

        elif line.type == "tline":
            if isinstance(line.data, list):
                new_data = []
                alone_point = []
                for l in line.data:
                    if isinstance(l, list):
                        temp = []
                        for h in l:
                            x = self._correct_x_linedata(h)
                            y = self._find_tline_y_point(x, line)
                            x = x - start
                            if x < 0:
                                continue
                            temp.append((x, y))

                        if len(temp) != 0:
                            new_data.append(temp)
                    else:
                        x = self._correct_x_linedata(l)
                        y = self._find_tline_y_point(x, line)
                        x = x - start
                        if x < 0:
                            continue
                        alone_point.append((x, y))

                if len(alone_point) != 0:
                    new_data.append(alone_point)

                return new_data

    def _find_tline_y_point(self, x: int, line: LineLayer):
        if line.tline_use in line.get_available_tline_use():
            y = self.chart.iloc[x].loc[line.tline_use]
            return y

        same_indicator_panel = 0
        use = line.tline_use
        if isinstance(use, int):
            for i in self.indicator_list:
                if line.panel == i.layer.panel:
                    same_indicator_panel += 1
                    if use < len(i.calculate().columns):
                        y = i.calculate().iloc[x, use]
                        return y
                    else:
                        use = use - len(i.calculate().columns)

            if same_indicator_panel == 0:
                raise ValueError(f"No indicator is in panel = {line.panel}.")

            raise ValueError(f"the tline_use = {line.tline_use} is out of bounds.")

        if isinstance(use, str):
            for i in self.indicator_list:
                if line.panel == i.layer.panel:
                    same_indicator_panel += 1
                    if use in i.calculate().columns:
                        y = i.calculate().iloc[x].loc[use]
                        return y
            if same_indicator_panel == 0:
                raise ValueError(f"No indicator is in panel = {line.panel}.")

            raise ValueError(
                f"the tline_use = {line.tline_use} is not in indicators columns name."
            )

    def _correct_x_linedata(self, data: Union[int, str, datetime]):
        if isinstance(data, int):
            return data
        elif isinstance(data, str):
            t = parse(data)
            return self.chart.index.get_loc(t)
        elif isinstance(data, datetime):
            return self.chart.index.get_loc(data)

    def make_line_collection(
        self, line_list: List[LineLayer], ax, start:int = 0,
    ) -> List[LineCollection]:
        for line in line_list:
            d = self._clean_line_data(line, ax, start)
            l = LineCollection(
                d,
                linestyle=line.linestyle,
                linewidth=line.linewidth,
                alpha=line.alpha,
                color=line.color,
            )
            ax[line.panel * 2].add_collection(l)

    def color_palette_help(self) -> List[str]:
        """
        Return a list of named CSS4 colors supported by matplotlib.

        Returns:
            List[str]: List of color names.
        """
        import matplotlib.colors as mcolors

        return list(mcolors.CSS4_COLORS.keys())

    def marker_styles_help(self) -> dict:
        """
        Return a dictionary of common matplotlib marker styles.

        Returns:
            dict: Marker code to description.
        """
        return {
            ".": "point",
            ",": "pixel",
            "o": "circle",
            "v": "triangle down",
            "^": "triangle up",
            "<": "triangle left",
            ">": "triangle right",
            "1": "tri down (tick)",
            "2": "tri up (tick)",
            "3": "tri left (tick)",
            "4": "tri right (tick)",
            "s": "square",
            "p": "pentagon",
            "*": "star",
            "h": "hexagon1",
            "H": "hexagon2",
            "+": "plus",
            "x": "x",
            "D": "diamond",
            "d": "thin diamond",
            "|": "vertical line",
            "_": "horizontal line",
        }

    def market_chart_types_help(self) -> List[str]:
        """
        Return the list of valid chart types supported by mplfinance.

        Returns:
            List[str]: Available types such as 'candle', 'line', 'ohlc', etc.
        """
        return ["candle", "ohlc", "line", "renko", "pnf", "hollow"]

    def market_chart_styles_help(self) -> List[str]:
        """
        Return a list of available built-in mplfinance styles.

        Returns:
            List[str]: All built-in style names like 'classic', 'charles', 'yahoo', etc.
        """
        return list(mpf.available_styles())

    def datetime_format_help(self) -> dict:
        """
        Return a dictionary of common datetime format examples.

        Returns:
            Dict[str, str]: Mapping of format codes to example meanings.
        """
        return {
            "%Y-%m-%d": "2025-07-14",
            "%d-%m-%Y": "14-07-2025",
            "%m/%d/%Y": "07/14/2025",
            "%b %d, %Y": "Jul 14, 2025",
            "%d %b %Y": "14 Jul 2025",
            "%H:%M": "14:30",
            "%Y-%m-%d %H:%M": "2025-07-14 14:30",
        }
