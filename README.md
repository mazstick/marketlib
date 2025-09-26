

# MarketLib 📊

MarketLib is a modular Python library for **financial data analysis, backtesting, and visualization**.  
It provides tools to fetch market data, implement indicators, design trading strategies, run backtests, and plot results with Plotly.

---

## Features
- Fetch OHLCV data from exchanges (Binance, CoinEx) or CSV files  
- Built-in technical indicators (SMA, EMA, MACD, ATR, Bollinger Bands) + custom indicators  
- Strategy framework (e.g., Moving Average Cross, MACD Divergence)  
- Backtesting engine with portfolio, orders, and reporting  
- Interactive charts with Plotly (price, indicators, signals)

---

## Quick Start
```python
from marketlib.data import Market
from marketlib.indicators import SMA
from marketlib.chart.chart_builder import Chart
import pandas as pd

df = pd.read_csv("BTCUSDT15m.csv")
market = Market(df, "BTCUSDT", "15m")

sma = SMA(market.df, column="close", periods=20)
chart = Chart(market)
chart.add_indicators(sma)
chart.plot()
```
## Project Structure

marketlib/

├── data/         # Market data & exchange APIs

├── indicators/   # Technical indicators

├── strategy/     # Trading strategies

├── backtest/     # Backtesting engine

└── chart/        # Visualization with Plotly & mplfinance
