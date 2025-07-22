import pandas as pd
from typing import Union, Tuple, Optional, List, Dict, Literal
import numpy as np


class FillBetweenLayer:

    def __init__(self):
        self.y1: Union[int, float, pd.Series, pd.DataFrame, np.ndarray] = None
        self.y2: Union[int, float, pd.Series, pd.DataFrame, np.ndarray] = None
        self.where: Union[np.ndarray, pd.Series, pd.DataFrame] = None
        self.color: str = None
        self.panel: int = 0
        self.alpha: float = 0.7
        self.interpolate: bool = True

    def set_layer(
        self,
        y1: Union[int, float, pd.Series, pd.DataFrame] = None,
        y2: Union[int, float, pd.Series, pd.DataFrame] = None,
        where: Union[np.ndarray, pd.Series, pd.DataFrame] = None,
        color: str = None,
        panel: int = 0,
        alpha: float = 0.7,
        interpolate: bool = True,
    ):
        """
        Adds a filled layer to the plot between y1 and y2, optionally controlled by a logical condition.

        Parameters
        ----------
        y1 : int | float | pd.Series | pd.DataFrame | np.ndarray
            The lower boundary of the fill. Can be a scalar or a Series. Default is 0.
        y2 : int | float | pd.Series | pd.DataFrame | np.ndarray
            The upper boundary of the fill. If None, it defaults to the same as y1.
        where : pd.Series | pd.DataFrame | np.ndarray of bool, optional
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

        if isinstance(y1, pd.Series):
            y1 = y1.values
        elif isinstance(y1, pd.DataFrame):
            y1 = y1.iloc[:, 0].values

        if isinstance(y2, pd.Series):
            y2 = y2.values
        elif isinstance(y2, pd.DataFrame):
            y2 = y2.iloc[:, 0].values

        if isinstance(where, pd.Series):
            where = where.values
        elif isinstance(where, pd.DataFrame):
            where = where.iloc[:, 0].values
        

        if not (0 <= alpha <= 1):
            raise ValueError("'alpha' must be between 0 and 1.")

        self.y1 = y1
        self.y2 = y2
        self.where = where
        self.panel = panel
        self.alpha = alpha
        self.color = color
        self.interpolate = interpolate

    def get_parameters(self) -> dict:
        """
        Return a dictionary of parameters suitable for mplfinance.plot.

        These can be passed directly as kwargs using: **get_()

        Returns:
            dict: Parameters for mplfinance.plot(..., fillbetween=get_parameters()).
        """

        params = {
            "y1": self.y1,
            "y2": self.y2,
            "where": self.where,
            "color": self.color,
            "panel": self.panel,
            "alpha": self.alpha,
            "interpolate": self.interpolate,
        }

        return {k: v for k, v in params.items() if v is not None}
