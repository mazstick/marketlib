import pandas as pd
from typing import Union, Tuple, Optional, List, Dict, Literal

class LineLayer:
    """
    A configuration class to store overlay line parameters for mplfinance charts.
    
    Supports line types:
        - 'vline': Vertical line(s) at given datetime(s)
        - 'hline': Horizontal line(s) at given y-value(s)
        - 'aline': Angled line(s) from point A to B (needs two index/y-value pairs)
        - 'tline': Time line(s) from close (low, high or open) in that time to an other.

    This class does not plot the line itself, but is intended to pass parameters
    upward to a plot manager or charting engine.
    """

    def __init__(self):
        self.type: Optional[Literal["vline", "hline", "aline", "tline"]] = None
        self.data: Optional[Union[List, Tuple]] = None
        self.linestyle: Literal["-", "--", "-.", ":"] = "-"
        self.color: str = "b"
        self.linewidth: float = 1.0
        self.alpha: float = 0.5
        self.panel: int = 0 
        self.tline_use: Union[Literal["open", "close", "high", "low"], str, int] = "close"

    def get_available_tline_use(self):
        return ["open", "close", "high", "low"]

    def set_parameters(
        self,
        data: Union[List, Tuple, float, int],
        type: Literal["vline", "hline", "aline", "tline"],
        linestyle: str = "-",
        color: Union[str, list] = "b",
        linewidth: float = 1.0,
        alpha: float = 0.5,
        panel: int = 0,
        tline_use: Union[Literal["open", "close", "high", "low"], str, int] = None,
    ):
        """
        Set the overlay parameters.

        Args:
            type: The type of overlay ('vline', 'hline', 'aline', 'tline').
            data: Coordinates or values needed for the overlay.
            linestyle: Style of the line ('-', '--', '-.', ':').
            color: Color of the line.
            linewidth: Width of the line.
            alpha: Transparency of the line (0 = transparent, 1 = opaque).
            panel: Index of the panel where the overlay should be applied.
        """
        valid_types = {"vline", "hline", "aline", "tline"}
        valid_linestyles = {"-", "--", "-.", ":"}

        if type not in valid_types:
            raise ValueError(f"Invalid type '{type}'. Must be one of: {valid_types}")

        if linestyle not in valid_linestyles:
            raise ValueError(f"Invalid linestyle '{linestyle}'. Must be one of: {valid_linestyles}")

        if not isinstance(color, (str, list)):
            raise TypeError("Color must be a string or list.")

        if not isinstance(linewidth, (int, float)) or linewidth <= 0:
            raise ValueError("Linewidth must be a positive number.")

        if not isinstance(alpha, (int, float)) or not (0 <= alpha <= 1):
            raise ValueError("Alpha must be between 0 and 1.")

        if not isinstance(panel, int) or panel < 0:
            raise ValueError("Panel must be a non-negative integer.")
        
                
        self.type = type
        self.data = data
        self.linestyle = linestyle
        self.color = color
        self.linewidth = linewidth
        self.alpha = alpha
        self.panel = panel
        
        if type != "tline" and (tline_use is not None):
            raise ValueError("tline_use can set when line type is 'tline'.")
        elif type == "tline":
            if tline_use is not None:
                if not isinstance(tline_use, (str, int)):
                    raise ValueError(f"tline_use must be one of {self.get_available_tline_use()} or an non negative integer or an indicator dataframe column name.")
                else:
                    self.tline_use = tline_use

            
            

    def get_layer_parameters(self) -> Dict:
        """
        Returns a dictionary of all current settings for this overlay layer.

        Returns:
            dict: Configuration for this overlay.
        """
        
        params = {
            "type": self.type,
            "data": self.data,
            "linestyle": self.linestyle,
            "color": self.color,
            "linewidth": self.linewidth,
            "alpha": self.alpha,
            "panel": self.panel,
        }
        if self.type == "tline":
            params["tline_use"] = self.tline_use
            params["tline_method"] = self.tline_method
            
        return params