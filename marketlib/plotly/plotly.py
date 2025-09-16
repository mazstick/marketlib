from marketlib.indicators import Indicator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .layer.plotlyLayer import PlotlyLayer
import pandas as pd


class Plotly:

    def __init__(self):
        self.chart = None
        self.indicators_list: list[Indicator] = []
        self.layer = PlotlyLayer()

    def add_chart(self, df: pd.DataFrame, market, timeframe):
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.reindex("datetime")

        if not set(["open", "close", "high", "low", "volume"]).issubset(df.columns):
            raise ValueError(
                "chart data frame must have ['open', 'close', 'high', 'low', 'volume'] columns."
            )

        self.chart = df
        self.market = market
        self.timeframe = timeframe

    def add_indicators(self, indicator: Indicator):

        if not isinstance(indicator, Indicator):
            raise ValueError("indicator must be instance of Indicator class.")

        self.indicators_list.append(indicator)

    def plot(self, show_volume: bool = True, show_indicators: bool = True):
        row, col = self._subplots_calculator(show_volume, show_indicators)
        
        heights = self._panel_height_calculator(row)
        fig = make_subplots(
            row,
            col,
            shared_xaxes=True,
            vertical_spacing=0.01,
            row_heights=self._panel_height_calculator(row),
        )

        fig.add_trace(
            go.Candlestick(
                x=self.chart.index,
                open=self.chart["open"],
                high=self.chart["high"],
                low=self.chart["low"],
                close=self.chart["close"],
                name="Price",
                increasing=dict(
                    line=dict(color="rgba(0,255,0)", width=0.7),
                    fillcolor="rgba(0,255,0)",
                ),
                decreasing=dict(
                    line=dict(color="rgba(255,0,0)", width=0.7),
                    fillcolor="rgba(255,0,0)",
                ),
            ),
            row=1,
            col=1,
        )

        if show_volume:
            fig.add_trace(
                go.Bar(
                    x=self.chart.index,
                    y=self.chart["volume"],
                    name="Volume",
                    marker_color="#900",
                ),
                row=2,
                col=1,
            )

        if show_indicators:
            for indic in self.indicators_list:
                ind_df = indic.calculate()
                for i in range(0, len(ind_df.columns)):
                    print(i)
                    fig.add_trace(
                        go.Scatter(
                            x=ind_df.index,
                            y=ind_df.iloc[:, i],
                            line=go.scatter.Line(
                                color=indic.plotly_layer.colors[i],
                                width=indic.plotly_layer.width[i],
                            ),
                            opacity=indic.plotly_layer.opacity[i],
                            hovertemplate=indic.plotly_layer.hovertemplate,
                            name=indic.name,
                        ),
                        row=indic.plotly_layer.panel[i],
                        col=col,
                    )

        fig.update_layout(
            title=self.market + " " + self.timeframe,
            xaxis_title="Time",
            yaxis_title="Price",
            yaxis1=dict(tickformat=","),
            yaxis2=dict(tickformat=","),
            yaxis3=dict(tickformat=","),
            xaxis_rangeslider_visible=False,
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=40, r=40, t=40, b=40),
            width=1200,
            height=700,
        )

        return fig

    def _subplots_calculator(self, volume, indicator) -> tuple[int, int]:
        row = 1
        col = 1
        if volume:
            row += 1

        if indicator:
            panels = []
            if len(self.indicators_list) == 0:
                return (row, col)
            for i in self.indicators_list:
                panels.extend(i.plotly_layer.panel)

            row = max(row, max(panels))
            return (row, col)

        return (row, col)

    def _panel_height_calculator(self, panel_len):
        panel_heights = []
        for i in range(1, panel_len + 1):
            if i == 1:
                panel_heights.insert(i - 1, self.layer.height)
            elif i == 2:
                panel_heights.insert(i - 1, self.layer.volume_panel_hight)
            else:
                max_panel = []
                for ind in self.indicators_list:
                    for panel in ind.plotly_layer.panel:
                        if panel == i:
                            max_panel.append(ind.plotly_layer.panel_hight)
                panel_heights.insert(i - 1, max(max_panel))

        return panel_heights
