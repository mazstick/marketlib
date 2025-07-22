import requests
import pandas as pd
from typing import Optional, Union, List, Literal
from datetime import datetime


class CoinEx:
    """
    A client to fetch market data from the CoinEx exchange API (v2).

    Attributes:
        base_url (str): Base URL for CoinEx API.
        timeout (int): Timeout for API requests (in seconds).
    """

    def __init__(self, base_url: str = "https://api.coinex.com/v2", timeout: int = 10):
        """
        Initialize the CoinEx API client.

        Args:
            base_url (str): Base URL of the CoinEx API.
            timeout (int): Timeout in seconds for HTTP requests.
        """
        self.base_url = base_url
        self.timeout = timeout
        self._symbols_cache = None
        self._market_info_cache = None

    def get_available_symbols(self) -> List[str]:
        """
        Retrieve the list of all available trading symbols (markets) on CoinEx.

        Returns:
            List[str]: A list of market symbols like ['BTCUSDT', 'ETHUSDT', ...].

        Raises:
            RuntimeError: If request fails or API response indicates an error.
        """
        url = f"{self.base_url}/spot/market"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                raise RuntimeError(f"CoinEx API Error: {data.get('message', 'Unknown error')}")

            self._market_info_cache = data["data"]
            markets = [item["market"] for item in data["data"]]
            self._symbols_cache = markets
            return markets

        except requests.Timeout:
            raise RuntimeError("Request timed out while fetching available symbols.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error while fetching available symbols.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed while fetching available symbols: {e}")
        except (KeyError, TypeError) as e:
            raise RuntimeError(f"Unexpected API response format: {e}")

    def symbol_info(self, symbol_name: str) -> pd.DataFrame:
        """
        Return detailed information for a specific market symbol.

        Args:
            symbol_name (str): The market symbol, e.g. 'BTCUSDT'.

        Returns:
            dict: Detailed market information.

        Raises:
            ValueError: If the symbol is not available.
            RuntimeError: If market info is not fetched properly.
        """
        self._ensure_symbol_available(symbol_name)
        try:
            symbol_info = pd.DataFrame(self._market_info_cache)
            return symbol_info[symbol_info['market'] == symbol_name]
        except Exception as e:
            raise RuntimeError(f"Failed to extract info for symbol '{symbol_name}': {e}")

    def get_data(
        self,
        market: str,
        interval: str = "1hour",
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV candlestick data for a specific market and interval.

        Args:
            market (str): Market symbol, e.g. 'BTCUSDT'.
            interval (str): Interval string, e.g. '1min', '5min', '1day'.
            limit (int): Number of data points to fetch (max 1000).

        Returns:
            pd.DataFrame: OHLCV data indexed by time.

        Raises:
            RuntimeError: If request fails or returns invalid data.
            ValueError: If the market symbol is not recognized.
        """
        self._ensure_symbol_available(market)

        url = f"{self.base_url}/spot/kline"
        params = {
            "market": market,
            "period": interval,
            "limit": limit
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                raise RuntimeError(f"CoinEx API Error: {data.get('message', 'Unknown error')}")

            klines = data.get("data", [])
            if not klines:
                raise RuntimeError("No kline data returned from API.")

            df = pd.DataFrame(klines, columns=["created_at", "open", "close", "high", "low", "volume", "value"])
            df["created_at"] = pd.to_datetime(df["created_at"], unit="ms")

            for col in ["open", "close", "high", "low", "volume", "value"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df.set_index("created_at", inplace=True)
            df.index.name = "datetime"
            return df

        except requests.Timeout:
            raise RuntimeError("Request timed out while fetching market data.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error while fetching market data.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed while fetching market data: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(f"Invalid response structure or data conversion error: {e}")


    def get_ticker(self, market: str) -> pd.DataFrame:
        """
        Get real-time ticker data for a given market.
        """
        self._ensure_symbol_available(market)
        url = f"{self.base_url}/spot/ticker"
        params = {"market": market}
        response = requests.get(url, params=params, timeout=self.timeout)
        data = response.json()
        if data.get("code") != 0:
            raise RuntimeError(f"CoinEx API Error: {data.get('message', 'Unknown error')}")
        return pd.DataFrame(data["data"])


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
