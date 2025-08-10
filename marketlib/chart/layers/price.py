import mplfinance as mpf
import pandas as pd
from typing import Union, Tuple, Optional, List, Dict, Literal
import mplfinance as mpf


class PriceLayer:

    def __init__(self):
        self.type = "candle"
        self.style = "yahoo"
        self.figsize = (10, 6)
        self.figratio: tuple = None
        self.figscale: float = None
        self.ylim: tuple = None
        self.xlim: tuple = None
        self.title = None
        self.ylabel = "Price"
        self.axisoff = False
        self.ylabel_lower = None
        self.tight_layout = False
        self.scale_padding = 1
        self.linecolor = "blue"
        self.volume = False
        self.mav = None
        self.datetime_format = None
        self.xrotation = 15
        self.show_nontrading = False
        self.panel_ratios = None
        self.update_width_config = None
        self.savefig = None
        self.warn_too_much_data = 1000

    def set_default(self):
        """
        Set layer to default parameters.
        """
        self.set_layer()

    def set_layer(
        self,
        type: Literal["candle", "ohlc", "line", "renko", "pnf", "hollow"] = "candle",
        style: str = "yahoo",
        figsize: Tuple[int, int] = None,
        title: Optional[str] = None,
        ylabel: Optional[str] = "Price",
        figratio: tuple = None,
        figscale: float = None,
        ylim: tuple = None,
        xlim: tuple = None,
        ylabel_lower: Optional[str] = None,
        tight_layout: bool = False,
        scale_padding: float = 1,
        linecolor: str = "blue",
        volume: bool = False,
        axisoff:bool = False,
        mav: Optional[Union[int, List[int]]] = None,
        datetime_format: Optional[str] = None,
        xrotation: int = 15,
        show_nontrading: bool = False,
        panel_ratios: Optional[Tuple[int, ...]] = None,
        update_width_config: Optional[Dict[str, float]] = None,
        savefig: Optional[str] = None,
        warn_too_much_data: int = 1000,
    ):
        """
        Configure the main price chart layer for use with mplfinance.plot().

        Args:
            type (str): Type of plot to draw. Common values:
                        'candle', 'ohlc', 'line', 'renko', 'pnf'.
                        Default is 'candle'.

            style (str): The name of a predefined mplfinance style
                        (e.g., 'classic', 'charles', 'yahoo', 'blueskies') or a custom style object.
                        Default is 'classic'.

            figsize (tuple): A tuple (width, height) in inches for the figure size.
                            Default is (10, 6).
                            
            figscale (float): Overall scaling factor applied to the entire figure. Optional.

            figratio (tuple): Ratio of figure width to height. Optional.
            
            axisoff (bool): Removes axes, ticks, labels, and gridlines for a clean minimalist plot.
            
            ylim (tuple): Y-axis value range.
                        Manually sets the vertical axis limits, typically used to focus on a specific price range or value window.
                        Format is (ymin, ymax), and values must match the expected data scale.

            xlim (tuple): X-axis value range.
                        Manually sets the horizontal axis limits, typically used to focus on a specific price range or value window.
                        Format is (xmin, xmax), and values must match the expected data scale.

            title (str): Title to display at the top of the plot. Optional.

            ylabel (str): Label for the Y-axis of the main panel. Default is 'Price'.

            ylabel_lower (str): Label for the Y-axis of the lower panel (volume or indicators). Optional.

            tight_layout (bool): Whether to use matplotlib's tight layout.
                                Default is True.

            scale_padding (float): Padding between data and chart border, as a fraction of the data range.
                                Default is 0.1 (10%).

            linecolor (str): Color for line plots (if `type="line"`). Default is "blue".

            volume (bool): Whether to include volume subplot. Default is False.

            mav (int or list of int): Moving average(s) to plot. For example, [10, 20, 50].

            datetime_format (str): Custom format string for datetime axis labels, e.g. '%Y-%m-%d'. Optional.

            xrotation (int): Angle (in degrees) to rotate x-axis tick labels. Default is 15.

            show_nontrading (bool): Whether to display gaps for non-trading days/hours. Default is False.

            panel_ratios (tuple of int): Ratios for sizing main/volume/indicator panels.
                                        Example: (3, 1) makes main panel 3x taller than volume panel.

            update_width_config (dict): Dictionary with keys like 'candle_linewidth', 'candle_width',
                                        'volume_linewidth', etc., to override default widths. Optional.

            savefig (str): If provided, path to save the resulting figure as an image file (e.g. 'chart.png').

            warn_too_much_data (int): If the number of data rows exceeds this value, show a warning.
                                    Set to 0 to disable. Default is 1000.

        Raises:
            ValueError: If any provided argument has an invalid value or format.
        """

        valid_types = {"candle", "ohlc", "line", "renko", "pnf", "hollow"}
        if type not in valid_types:
            raise ValueError(f"'type' must be one of {valid_types}, not '{type}'")

        # if not isinstance(figsize, tuple) or len(figsize) != 2:
        #     raise ValueError("figsize must be a tuple of (width, height)")

        if scale_padding < 0 or scale_padding > 1:
            raise ValueError("scale_padding must be between 0 and 1.")

        if update_width_config is not None and not isinstance(
            update_width_config, dict
        ):
            raise ValueError("update_width_config must be a dict")

        if panel_ratios is not None and not isinstance(panel_ratios, tuple):
            raise ValueError("panel_ratios must be a tuple")

        self.type = type
        self.style = style
        self.figsize = figsize
        self.figratio = figratio
        self.figscale = figscale
        self.ylim = ylim
        self.xlim = xlim
        self.axisoff = axisoff
        self.title = title
        self.ylabel = ylabel
        self.ylabel_lower = ylabel_lower
        self.tight_layout = tight_layout
        self.scale_padding = scale_padding
        self.linecolor = linecolor
        self.volume = volume
        self.mav = mav
        self.datetime_format = datetime_format
        self.xrotation = xrotation
        self.show_nontrading = show_nontrading
        self.panel_ratios = panel_ratios
        self.update_width_config = update_width_config
        self.savefig = savefig
        self.warn_too_much_data = warn_too_much_data

    def get_parameters_as_dataframe(self) -> pd.DataFrame:
        """
        Return all price layer parameters as a one-row DataFrame.
        """
        params = {
            "type": self.type,
            "style": self.style,
            "figsize": self.figsize,
            "figratio": self.figratio,
            "figscale": self.figscale,
            "ylim": self.ylim,
            "xlim": self.xlim,
            "title": self.title,
            "ylabel": self.ylabel,
            "ylabel_lower": self.ylabel_lower,
            "tight_layout": self.tight_layout,
            "scale_padding": self.scale_padding,
            "linecolor": self.linecolor,
            "volume": self.volume,
            "axisoff": self.axisoff,
            "mav": self.mav,
            "datetime_format": self.datetime_format,
            "xrotation": self.xrotation,
            "show_nontrading": self.show_nontrading,
            "panel_ratios": self.panel_ratios,
            "update_width_config": self.update_width_config,
            "savefig": self.savefig,
            "warn_too_much_data": self.warn_too_much_data,
        }

        return pd.DataFrame([params])

    def set_parameters_as_dataframe(self, df: pd.DataFrame) -> None:
        """
        Set parameters from a one-row DataFrame.

        Raises:
            ValueError: If the DataFrame is not valid.
        """
        if df.shape[0] != 1:
            raise ValueError("DataFrame must have exactly one row.")

        row = df.iloc[0].to_dict()

        allowed_params = {
            "type",
            "style",
            "figsize",
            "figratio",
            'figscale',
            'ylim',
            'xlim',
            "title",
            "axisoff",
            "ylabel",
            "ylabel_lower",
            "tight_layout",
            "scale_padding",
            "linecolor",
            "volume",
            "mav",
            "datetime_format",
            "xrotation",
            "show_nontrading",
            "panel_ratios",
            "update_width_config",
            "savefig",
            "warn_too_much_data",
        }

        for key, value in row.items():
            if key in allowed_params:
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown parameter: '{key}'")

    def get_parameters(self) -> dict:
        """
        Get the plot parameters as a dictionary usable with `mpf.plot(df, **params)`.

        Args:
            with_lines (bool): Whether to get overlay lines.
                            Default is True.
        """
        params = {
            "type": self.type,
            "style": self.style,
            "figsize": self.figsize,
            "figratio": self.figratio,
            "figscale": self.figscale,
            "ylim": self.ylim,
            "xlim":self.xlim,
            "title": self.title,
            "ylabel": self.ylabel,
            "axisoff": self.axisoff,
            "ylabel_lower": self.ylabel_lower,
            "tight_layout": self.tight_layout,
            "scale_padding": self.scale_padding,
            "linecolor": self.linecolor,
            "volume": self.volume,
            "mav": self.mav,
            "datetime_format": self.datetime_format,
            "xrotation": self.xrotation,
            "show_nontrading": self.show_nontrading,
            "panel_ratios": self.panel_ratios,
            "update_width_config": self.update_width_config,
            "savefig": self.savefig,
            "warn_too_much_data": self.warn_too_much_data,
        }

        return {k: v for k, v in params.items() if v is not None}

    def get_available_types(self) -> List[str]:
        """
        Return the list of valid chart types supported by mplfinance.

        Returns:
            List[str]: Available types such as 'candle', 'line', 'ohlc', etc.
        """
        return ["candle", "ohlc", "line", "renko", "pnf", "hollow"]

    def get_available_styles(self) -> List[str]:
        """
        Return a list of available built-in mplfinance styles.

        Returns:
            List[str]: All built-in style names like 'classic', 'charles', 'yahoo', etc.
        """
        return list(mpf.available_styles())

    def get_datetime_format_examples(self) -> Dict[str, str]:
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
