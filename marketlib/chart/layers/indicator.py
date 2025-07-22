import mplfinance as mpf
import pandas as pd
from typing import Literal, Union, Optional, List
from .line import LineLayer
class IndicatorLayer:

    def __init__(self):
        self.name = "Unknown Indicator"
        self.type = "line"
        self.label = None
        self.color = None
        self.ylabel = None
        self.panel = 1
        self.width = 0.5
        self.linestyle = '-'
        self.marker = None
        self.markersize = 4
        self.alpha = 1.0
        self.secondary_y = False
        self.ylim = None
        self.figsize: tuple = (15, 8)
        self.x_rotation: int = 45
        self.grid:bool = True
        self.xlabel: str = None
        

    def set_default(self):
        """
        Set layer to default parameters.
        """
        self.set_layer()

    def set_layer(
        self,
        type: str = "line",
        label: Union[str, List[str], None] = None,
        color: Union[str, List[str], dict, None] = None,
        ylabel: Optional[str] = None,
        panel: int = 1,
        width: Optional[float] = 1.0,
        linestyle: Union[str, List[str]] = "-",
        marker: Optional[str] = None,
        markersize: Optional[float] = 4,
        alpha: Optional[float] = 1.0,
        secondary_y: bool = False,
        ylim: Optional[tuple] = None,
        figsize: tuple = (15, 8),
        x_rotation: int = 45,
        grid:bool = True,
        xlabel: str = None
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

        self.type = type
        self.label = label
        self.color = color
        self.ylabel = ylabel
        self.panel = panel
        self.width = width
        self.linestyle = linestyle
        self.marker = marker
        self.markersize = markersize
        self.alpha = alpha
        self.secondary_y = secondary_y
        self.ylim = ylim
        self.figsize = figsize
        self.grid = grid
        self.xlabel = xlabel
        self.x_rotation = x_rotation


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
            "ylabel": self.ylabel,
            "label": self.label,
            "width": self.width,
            "linestyle": self.linestyle,
            "marker": self.marker,
            "markersize": self.markersize,
            "alpha": self.alpha,
            "secondary_y": self.secondary_y,
            "ylim": self.ylim
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
            "type", "color", "panel", "ylabel", "label",
            "width", "linestyle", "marker", "markersize",
            "alpha", "secondary_y", "ylim"
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
            "ylabel": self.ylabel,
            "label": self.label,
            "width": self.width,
            "linestyle": self.linestyle,
            "marker": self.marker,
            "markersize": self.markersize,
            "alpha": self.alpha,
            "secondary_y": self.secondary_y,
            "ylim": self.ylim,
        }

        return {k: v for k, v in params.items() if v is not None}
    
    
    
    def get_available_types(self):
        """
        Return a list of common style.

        Returns:
            list: A list of styles.
        """        
        
        return ["bar", "line", "scatter", "step"]

    
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
        
    def get_available_line_styles(self) -> dict:
        """
        Return a dictionary of valid line styles in matplotlib.

        Returns:
            dict: Style code to description.
        """
        return {
            '-': 'solid',
            '--': 'dashed',
            '-.': 'dash-dot',
            ':': 'dotted',
            'None': 'no line'
        }
        
    def get_named_color_palette(self) -> List[str]:
        """
        Return a list of named CSS4 colors supported by matplotlib.

        Returns:
            List[str]: List of color names.
        """
        import matplotlib.colors as mcolors
        return list(mcolors.CSS4_COLORS.keys())



