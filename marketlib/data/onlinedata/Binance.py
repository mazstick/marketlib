import requests
import pandas as pd
from typing import List, Optional, Union
from datetime import datetime


class Binance:
    """
    Client for Binance public REST API (spot market).

    Attributes:
        base_url (str): Base URL for Binance API.
        timeout (int): Timeout for HTTP requests in seconds.
    """

    def __init__(self, base_url: str = "https://api.binance.com/api/v3", timeout: int = 10):
        """
        Initialize Binance API client.

        Args:
            base_url (str): Binance API base URL.
            timeout (int): HTTP request timeout in seconds.
        """
        self.base_url = base_url
        self.timeout = timeout
        self._symbols_cache = None
        self._exchange_info_cache = None

    def get_available_symbols(self) -> List[str]:
        """
        Get list of all active trading symbols on Binance spot market.

        Returns:
            List[str]: List of symbols (e.g. ['BTCUSDT', 'ETHUSDT', ...])

        Raises:
            RuntimeError: On request failure or API error.
        """
        url = f"{self.base_url}/exchangeInfo"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            symbols_data = data.get("symbols")
            if symbols_data is None:
                raise RuntimeError("Malformed API response: 'symbols' field missing.")

            symbols = [s["symbol"] for s in symbols_data if s.get("status") == "TRADING"]

            self._symbols_cache = symbols
            self._exchange_info_cache = symbols_data
            return symbols

        except requests.Timeout:
            raise RuntimeError("Request timed out while fetching available symbols.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error while fetching available symbols.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed while fetching available symbols: {e}")
        except (KeyError, TypeError) as e:
            raise RuntimeError(f"Unexpected API response format: {e}")

    def symbol_info(self, symbol_name: str) -> dict:
        """
        Get detailed info for a specific trading symbol.

        Args:
            symbol_name (str): Symbol name (e.g. 'BTCUSDT')

        Returns:
            dict: Symbol information from Binance exchangeInfo.

        Raises:
            ValueError: If symbol not found.
            RuntimeError: If exchange info not loaded or malformed.
        """
        if self._exchange_info_cache is None:
            self.get_available_symbols()

        for symbol in self._exchange_info_cache:
            if symbol.get("symbol") == symbol_name:
                return symbol

        raise ValueError(f"Symbol '{symbol_name}' not found in Binance exchange info.")

    def get_data(
        self,
        market: str,
        interval: str = "1h",
        start_time: Optional[Union[int, datetime]] = None,
        end_time: Optional[Union[int, datetime]] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get historical candlestick (kline) data.

        Args:
            market (str): Trading pair symbol (e.g. 'BTCUSDT').
            interval (str): Kline interval (e.g. '1m', '5m', '1h', '1d', etc.).
            start_time (int or datetime, optional): Start time in ms or datetime.
            end_time (int or datetime, optional): End time in ms or datetime.
            limit (int): Number of data points to retrieve (max 1000).

        Returns:
            pd.DataFrame: DataFrame with columns:
                ['open_time', 'open', 'high', 'low', 'close', 'volume',
                 'close_time', 'quote_asset_volume', 'number_of_trades',
                 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
                Index is datetime based on 'open_time'.

        Raises:
            RuntimeError: On request failure or invalid data.
            ValueError: If the market symbol is not recognized.
        """
        self._ensure_symbol_available(market)

        url = f"{self.base_url}/klines"
        params = {
            "symbol": market,
            "interval": interval,
            "limit": limit
        }
        
        start_time = pd.Timestamp(start_time).tz_localize("UTC")
        end_time = pd.Timestamp(end_time).tz_localize("UTC")

        def to_milliseconds(t):
            if isinstance(t, datetime):
                return int(t.timestamp() * 1000)
            elif isinstance(t, int):
                return t
            else:
                raise ValueError("start_time/end_time must be int (ms) or datetime object")

        if start_time is not None:
            params["startTime"] = to_milliseconds(start_time)
        if end_time is not None:
            params["endTime"] = to_milliseconds(end_time)

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise RuntimeError(f"Unexpected response data format: {data}")

            columns = [
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "number_of_trades",
                "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
            ]
            df = pd.DataFrame(data, columns=columns)
            df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
            df.set_index("open_time", inplace=True)

            numeric_cols = columns[1:-1]
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

            return df

        except requests.Timeout:
            raise RuntimeError("Request timed out while fetching market data.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error while fetching market data.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed while fetching market data: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(f"Invalid response or data conversion error: {e}")

    def get_current_price(self, market: str) -> str:
        """
        Get current price ticker for a symbol.

        Args:
            market (str): Trading pair symbol (e.g. 'BTCUSDT').

        Returns:
            str: Latest price as string.

        Raises:
            RuntimeError: On request failure or API error.
        """
        url = f"{self.base_url}/ticker/price"
        params = {"symbol": market}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            price = data.get("price")
            if price is None:
                raise RuntimeError(f"API response missing price for symbol {market}.")

            return price

        except requests.Timeout:
            raise RuntimeError("Request timed out while fetching current price.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error while fetching current price.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed while fetching current price: {e}")




    def _ensure_symbol_available(self, symbol_name: str):
        """
        Check whether a symbol is available in the exchange. Raises if not.

        Args:
            symbol_name (str): Symbol to verify.

        Raises:
            ValueError: If the symbol is not available.
        """
        if self._symbols_cache is None:
            self._symbols_cache = self.get_available_symbols()

        if symbol_name not in self._symbols_cache:
            raise ValueError(
                f"Symbol '{symbol_name}' not found in available markets. "
                f"Call `.get_available_symbols()` to see the full list."
            )
