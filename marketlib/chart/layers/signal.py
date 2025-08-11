import mplfinance as mpf
import pandas as pd
from typing import Literal, Union, Optional, List
import numpy as np

class SignalLayer:

    def __init__(self):
        self.data = None
        self.distance_mark: float = 0.001,
        self.position: Literal['sell', 'buy'] = 'buy'
        self.signal_use: Union[Literal["close", "high", "low","open"], int, str] = None
        self.type = "scatter"
        self.label = None
        self.color = None
        self.panel = 0
        self.marker = None
        self.markersize = 10
        self.alpha = 1.0
        self.grid:bool = True
        self.xlabel: str = None
        

    def set_default(self):
        """
        Set layer to default parameters.
        """
        self.set_layer()

    def set_layer(
        self,
        data: Union[pd.DataFrame, pd.Series],
        distance_mark: float = 0.001,
        position: Literal['sell', 'buy'] = 'buy',
        signal_use: Union[Literal["close", "high", "low","open"], int, str] = None,
        label: Union[str, List[str], None] = None,
        color: Union[str, List[str], dict, None] = None,
        panel: int = 0,
        marker: Optional[str] = None,
        markersize: Optional[float] = 10,
        alpha: Optional[float] = 1.0,
        grid:bool = True,
        xlabel: str = None
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
        
        if position == "buy":
            if signal_use is None:
                signal_use = "low"
            if color is None:
                color = 'g'
            if marker is None:
                marker = "^"
            if distance_mark > 0 :
                distance_mark = - distance_mark
        
        if position == "sell":
            if signal_use is None:
                signal_use = "high"
            if color is None:
                color = 'r'
            if marker is None:
                marker = "v"
                
        if signal_use not in ["close", "low", "high", "open"] and not isinstance(signal_use, (int, str)):
            raise ValueError("signal_use must be Literal['close', 'high', 'low','open'] or int number or str.")
        elif signal_use in ["close", "low", "high", "open"] and panel != 0:
            raise ValueError(f"signal_use = {signal_use} but panel is {panel} that means signal layer is not on main chart.")

        if position not in ["sell", "buy"]:
            raise ValueError("position must be 'sell' or 'buy' ")

        if not isinstance(panel, int) or panel < 0:
            raise ValueError("panel must be a non-negative integer.")

        if alpha is not None and not (0 <= alpha <= 1):
            raise ValueError("alpha must be between 0 and 1.")
        
        self.data = self._clean_data(data)
        self.distance_mark = distance_mark
        self.position = position
        self.signal_use = signal_use
        self.label = label
        self.color = color
        self.panel = panel
        self.marker = marker
        self.markersize = markersize
        self.alpha = alpha
        self.grid = grid
        self.xlabel = xlabel


    def _clean_data(self, data)-> pd.Series:
        if isinstance(data, pd.DataFrame):
            if len(data.columns) > 1:
                raise ValueError("Data has more than 1 columns. Signal data must be in 1 column.")
            else:
                data = pd.Series(data.iloc[:, 0])
                if isinstance(data.iloc[0], (bool, np.bool)):
                    data = ~ data
                elif isinstance(data.iloc[0], (int, float)):
                    data = data.astype(object)
                    data[data == 0] = False
                    data[data != 0] = True
                    data = ~ data
            if data is None:
                raise ValueError(f"data = {data} or it's not in correct form.")
        elif isinstance(data, pd.Series):
                if isinstance(data.iloc[0], (bool, np.bool)):
                    data = ~ data
                elif isinstance(data.iloc[0], (int, float)):
                    data = data.astype(object)
                    data[data == 0] = False
                    data[data != 0] = True
                    data = ~ data
                if data is None:
                    raise ValueError(f"data = {data} or it's not in correct form.")
        
        return data

                    
                    


    def get_parameters_as_dataframe(self) -> pd.DataFrame:
        """
        Return the layer's configuration parameters as a one-row pandas DataFrame.

        Useful for inspection, logging, or debugging.

        Returns:
            pd.DataFrame: A one-row DataFrame with parameter names and values.
        """

        params = {
            "type": self.type,
            "color": self.color,
            "panel": self.panel,
            "label": self.label,
            "marker": self.marker,
            "markersize": self.markersize,
            "alpha": self.alpha,
        }
        
        return pd.DataFrame([params])


    def set_parameters_as_dataframe(self, df: pd.DataFrame) -> None:
        """
        Set layer parameters from a one-row DataFrame.

        Args:
            df (pd.DataFrame): A DataFrame with one row, where column names correspond
                            to parameter names.

        Raises:
            ValueError: If the DataFrame has more than one row.
        """

        if df.shape[0] != 1:
            raise ValueError("DataFrame must have exactly one row.")

        row = df.iloc[0].to_dict()

        allowed_params = {
            "type", "color", "panel", "label", "marker", "markersize",
            "alpha"
        }

        for key, value in row.items():
            if key in allowed_params:
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown parameter: '{key}'")


    def get_parameters(self) -> dict:
        """
        Return a dictionary of parameters suitable for mplfinance.make_addplot.

        These can be passed directly as kwargs using: **get_addplot_params()

        Returns:
            dict: Parameters for mplfinance.make_addplot.
        """

        
        params = {
            "type": self.type,
            "color": self.color,
            "panel": self.panel,
            "label": self.label,
            "marker": self.marker,
            "markersize": self.markersize,
            "alpha": self.alpha,
        }

        return {k: v for k, v in params.items() if v is not None}
    
    
    
    def get_available_types(self):
        """
        Return a list of common style.

        Returns:
            list: A list of styles.
        """        
        
        return ["scatter"]

    
    def get_available_marker_styles(self) -> dict:
        """
        Return a dictionary of common matplotlib marker styles.

        Returns:
            dict: Marker code to description.
        """
        return {
            '.': 'point',
            ',': 'pixel',
            'o': 'circle',
            'v': 'triangle down',
            '^': 'triangle up',
            '<': 'triangle left',
            '>': 'triangle right',
            '1': 'tri down (tick)',
            '2': 'tri up (tick)',
            '3': 'tri left (tick)',
            '4': 'tri right (tick)',
            's': 'square',
            'p': 'pentagon',
            '*': 'star',
            'h': 'hexagon1',
            'H': 'hexagon2',
            '+': 'plus',
            'x': 'x',
            'D': 'diamond',
            'd': 'thin diamond',
            '|': 'vertical line',
            '_': 'horizontal line'
        }
        
        
    def get_named_color_palette(self) -> List[str]:
        """
        Return a list of named CSS4 colors supported by matplotlib.

        Returns:
            List[str]: List of color names.
        """
        import matplotlib.colors as mcolors
        return list(mcolors.CSS4_COLORS.keys())



