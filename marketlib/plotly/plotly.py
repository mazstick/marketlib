from marketlib.indicators import Indicator
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .layer.plotlyLayer import PlotlyLayer
import pandas as pd

class Plotly():
    
    def __init__(self):
        self.chart = None
        self.indicators_list:list[Indicator] = []
    
    def add_chart(self, df:pd.DataFrame, market, timeframe):
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df["datetime"])
            df.reindex('datetime')
        
        if not set(['open', 'close', 'high', 'low', 'volume']).issubset(df.columns):
            raise ValueError("chart data frame must have ['open', 'close', 'high', 'low', 'volume'] columns.")
        
        self.chart = df
        self.market = market
        self.timeframe = timeframe
        
    def add_indicators(self, indicator:Indicator):
        
        if not isinstance(indicator, Indicator):
            raise ValueError("indicator must be instance of Indicator class.")
        
        self.indicators_list.append(indicator)
        
    
    def plot(self, show_volume:bool=True, show_indicators:bool=True):
        row , col = self._subplots_calculator(show_volume, show_indicators)
        fig = make_subplots(row, col, shared_xaxes=True, vertical_spacing=0.01)
        
        fig.add_trace(go.Candlestick(
            x=self.chart.index,
            open=self.chart['open'],
            high=self.chart['high'],
            low=self.chart['low'],
            close=self.chart['close'],
            name='Price',
            increasing=dict(line=dict(color='rgba(0,255,0)', width=0.7), fillcolor='rgba(0,255,0)'),
            decreasing=dict(line=dict(color='rgba(255,0,0)', width=0.7), fillcolor='rgba(255,0,0)')
        ), row=1, col=1)
        
        if show_volume:
            fig.add_trace(go.Bar(
                x=self.chart.index,
                y=self.chart['volume'],
                name='Volume',
                marker_color="#900",
            ), row=2, col=1)
            
        if show_indicators:
            for indic in self.indicators_list:
                ind_df = indic.calculate()
                fig.add_trace(go.Scatter(x=ind_df.index, y=ind_df.values, line=go.scatter.Line(color=indic.layer.color, width=indic.layer.width), opacity=indic.layer.alpha), name=indic.name, row=indic.layer.panel+1 , col=col)
        
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
            width=1900,
            height=900
        )
        
        return fig
        
    
    def _subplots_calculator(self, volume, indicator) -> tuple[int, int]:
        row = 1
        col = 1
        if volume :
            row+= 1
            
        if indicator:
            panels = []
            if len(self.indicators_list) == 0:
                return (row, col)
            for i in self.indicators_list:
                panels.append(i.layer.panel)
                
            row = max(row, max(panels) + 1)
            return (row, col)
        
        return (row, col) 
        
        