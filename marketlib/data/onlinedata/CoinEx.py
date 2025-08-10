import requests
from urllib.parse import urlparse, urlencode
from typing import Optional, Union, List, Literal, Dict, Any
import hmac, hashlib, time, json
from .CoinEx_utils import CoinEx_Definitions, Spot_HTTP, Asset_HTTP, Futures_HTTP


class CoinEx:
    """
    CoinEx API client (v2) for authenticated and public requests.

    Provides signed request capabilities via HMAC-SHA256, automatic header generation,
    and support for public/private GET operations. Built for secure, modular interaction
    with the CoinEx exchange.
    """

    BASE_URL = "https://api.coinex.com/v2"

    HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "X-COINEX-KEY": "",
        "X-COINEX-SIGN": "",
        "X-COINEX-TIMESTAMP": "",
    }

    def __init__(
        self,
        access_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        user_proxy: Optional[dict] = None,
    ):
        """
        Initialize the client with access credentials.

        Args:
            access_id (str, optional): Your CoinEx API access ID.
            secret_key (str, optional): Your CoinEx API secret key.
            user_proxy (dict, optional): Custom proxy configuration for routing HTTP requests.
            Example:
                {
                    "http": "http://your-proxy:port",
                    "https": "http://your-proxy:port"
                }
        """
        self.access_id = access_id
        self.secret_key = secret_key
        self.base_url = self.BASE_URL
        self._spot_markets_list_cache = None
        self._spot_market_status_cache = None
        self._futures_markets_list_cache = None
        self._futures_market_status_cache = None
        if user_proxy:
            self.proxy = user_proxy
        else:
            self.proxy = None

    # >>> UTILS Functions //////////////////////////////////////////////////////////////////////////////////////////////////////////////////// start

    def authentication(self, access_id: str, secret_key: str):
        self.access_id = access_id
        self.secret_key = secret_key

    def _need_authentication(self):
        if self.access_id is None or self.secret_key is None:
            raise UserWarning(
                "This action need Authentication please enter your 'access id' and 'secret key' by calling Coinex().authentication()"
            )
        else:
            pass

    def _gen_sign(self, method: str, request_path: str, body, timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for authenticated requests.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.).
            request_path (str): API path including query string.
            body: JSON string or empty string if no body.
            timestamp (str): Current timestamp in milliseconds.

        Returns:
            str: Lowercase hexadecimal signature string.
        """
        method = method.upper()
        prepared_str = f"{method}{request_path}{body}{timestamp}"

        signed_str = (
            hmac.new(
                bytes(self.secret_key, "latin-1"),
                msg=bytes(prepared_str, "latin-1"),
                digestmod=hashlib.sha256,
            )
            .hexdigest()
            .lower()
        )
        return signed_str

    def request(
        self,
        method: str,
        url: str,
        params: dict = None,
        body: dict = None,
        public_url: bool = False,
    ):
        """
        Send an HTTP request to the CoinEx API.

        Args:
            method (str): HTTP method (currently supports 'GET').
            url (str): Full or relative URL endpoint.
            params (dict, optional): Query parameters.
            body (dict, optional): Request body payload (currently unused).
            public_url (bool): Set to True to bypass authentication headers.

        Returns:
            dict: Parsed JSON response.

        Raises:
            RuntimeError: If request fails or API returns an error response.
        """
        if not public_url:
            self._need_authentication()

        if self.base_url not in url:
            url = self.base_url + url

        try:
            if method.upper() == "GET":
                if params:
                    params = {k: v for k, v in params.items() if v is not None}
                    path = urlparse(url).path + "?" + urlencode(params)
                else:
                    path = urlparse(url).path

                response = requests.get(
                    url,
                    params=params,
                    headers=(
                        None if public_url else self.headers(method, path, body=body)
                    ),
                    proxies=self.proxy if self.proxy else {},
                )

                response.raise_for_status()
                response_json = response.json()

                if response_json.get("code") != 0:
                    raise RuntimeError(f"API Error: {response_json.get('message')}")

                return response_json

        except requests.Timeout:
            raise RuntimeError("Request timed out.")
        except requests.ConnectionError:
            raise RuntimeError("Connection error.")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")

    def headers(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """
        Generate authenticated headers for API requests.

        Args:
            method (str): HTTP method used.
            path (str): Full API path including query string.
            body (dict, optional): Payload data.

        Returns:
            dict: Complete headers with API key, timestamp, and digital signature.
        """
        timestamp = str(int(time.time() * 1000))
        body_str = json.dumps(body) if body else ""

        signed_str = self._gen_sign(method, path, body_str, timestamp)

        headers = self.HEADERS.copy()
        headers["X-COINEX-KEY"] = self.access_id
        headers["X-COINEX-SIGN"] = signed_str
        headers["X-COINEX-TIMESTAMP"] = timestamp

        return headers

    def _ensure_spot_market_available(self, market_name: Union[str, List[str]]):
        """
        Check whether a market is available in the exchange. Raises if not.

        Args:
            market_name (str): Market to verify.

        Raises:
            ValueError: If the market is not available.
        """
        if self._spot_markets_list_cache is None:
            self._spot_markets_list_cache = self.get_spot_available_markets()

        if "," in market_name:
            market_name = market_name.split(",")

        if isinstance(market_name, list):
            for market in market_name:
                if market not in self._spot_markets_list_cache:
                    raise ValueError(
                        f"Market '{market}' not found in available markets. "
                        f"Call `.get_spot_available_markets()` to see the full list."
                    )

        elif isinstance(market_name, str):
            if market_name not in self._spot_markets_list_cache:
                raise ValueError(
                    f"Market '{market_name}' not found in available markets. "
                    f"Call `.get_spot_available_markets()` to see the full list."
                )

    # >>> UTILS Functions \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ end

    # >>> SPOT Tab ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ start

    def get_spot_available_markets(self) -> List[str]:
        """
        Retrieve the list of all available trading symbols (markets) on CoinEx.

        Returns:
            List[str]: A list of market symbols like ['BTCUSDT', 'ETHUSDT', ...].

        Raises:
            RuntimeError: If request fails or API response indicates an error.
        """

        data = self.get_spot_market_status()

        markets = [item["market"] for item in data["data"]]
        self._spot_markets_list_cache = markets
        return markets

        # >>> Spot >> Ticker menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_spot_market_information(
        self, market: Optional[Union[str, List[str]]] = None
    ):
        """
        Retrieve real-time price and volume information for spot markets.

        This method queries the `/spot/ticker` endpoint to fetch one-day statistics
        such as last price, daily high/low, opening/closing prices, volume, and trade value
        for specified markets or all available markets.

        Parameters
        ----------
        market : str or List[str], optional
            A market symbol or a list of market symbols (e.g., "BTCUSDT" or ["BTCUSDT","ETHUSDT"]).
            If omitted or an empty string is passed, data for all markets is returned.
            A maximum of 10 markets may be specified.

        Returns
        -------
        Dict[str, Any]
            Parsed JSON response containing a list of market entries.
            Each entry includes:
            - market : Market name (e.g., "BTCUSDT")
            - last : Latest traded price
            - open : Opening price for the period
            - close : Closing price for the period
            - high : Highest traded price
            - low : Lowest traded price
            - volume : Total traded volume
            - value : Total trade value in quote currency
            - volume_sell : Taker sell volume
            - volume_buy : Taker buy volume
            - period : Time window (fixed at 86400 = one day)
        """

        params = {}
        if market:
            self._ensure_spot_market_available(market_name=market)
            params["market"] = market

        return self.request(
            "GET",
            Spot_HTTP.Ticker.GET_MARKET_INFORMATION,
            params=params,
            public_url=True,
        )

    def get_spot_market_depth(
        self, market: str, limit: int = 20, interval: str = "0.01"
    ) -> dict:
        """
        Retrieve the order book depth data for a specified spot market.

        This method queries the `/spot/depth` endpoint to obtain detailed bid/ask levels,
        including prices, volumes, the latest trade price, and depth checksum validation data.

        Parameters
        ----------
        market : str
            Market symbol (e.g. "BTCUSDT"). Required.
        limit : int, optional
            Number of depth entries to return per side. Must be one of [5, 10, 20, 50].
            Default is 20.
        interval : str, optional
            Merge interval used to group price levels. Must be one of:
            ["0", "0.00000000001", "0.000000000001", "0.0000000001", "0.000000001", "0.00000001",
            "0.0000001", "0.000001", "0.00001", "0.0001", "0.001", "0.01", "0.1", "1", "10", "100", "1000"]
            Default is "0.01".

        Returns
        -------
        dict
            Parsed response containing depth snapshot and metadata:
            - market : str
            - is_full : bool
            - depth : dict
                - asks : List[List[str]] - Sell price and volume pairs
                - bids : List[List[str]] - Buy price and volume pairs
                - last : str - Last traded price
                - updated_at : int - Timestamp in milliseconds
                - checksum : int - CRC32 checksum for data integrity
        """
        if limit not in [5, 10, 20, 50]:
            raise ValueError(f"Invalid limit: {limit}. Must be one of [5, 10, 20, 50].")

        valid_intervals = [
            "0",
            "0.00000000001",
            "0.000000000001",
            "0.0000000001",
            "0.000000001",
            "0.00000001",
            "0.0000001",
            "0.000001",
            "0.00001",
            "0.0001",
            "0.001",
            "0.01",
            "0.1",
            "1",
            "10",
            "100",
            "1000",
        ]
        if interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {interval}. Must be one of {valid_intervals}."
            )

        self._ensure_spot_market_available(market_name=market)

        params = {"market": market, "limit": limit, "interval": interval}

        return self.request(
            "GET", Spot_HTTP.Ticker.GET_MARKET_DEPTH, params=params, public_url=True
        )

    def get_spot_market_status(
        self, market: Union[str, List[str]] = None, force_reload: bool = False
    ):
        """
        Retrieve market status and configuration for one or more spot markets.

        This method queries the `/spot/market` endpoint to fetch structural and fee-related
        parameters for specified spot markets. It returns key attributes such as maker/taker fee rates,
        precision levels, minimum tradable amount, and flags indicating feature availability.

        Parameters
        ----------
        market : str, optional
            Comma-separated list of market symbols (e.g., "BTCUSDT,ETHUSDT").
            Maximum of 10 market names allowed. If omitted or an empty string is passed,
            all available spot markets will be returned.
        force_reload : bool
            The function uses a caching approach for better performance.
            if force_reload been True, function download market status frome CoinEx api again.

        Returns
        -------
        Dict[str, Any]
            Parsed response from CoinEx API containing a list of market entries.
            Each entry may include:
            - market : Market name
            - maker_fee_rate : Maker transaction fee
            - taker_fee_rate : Taker transaction fee
            - min_amount : Minimum allowable trade volume
            - base_ccy : Base currency symbol
            - quote_ccy : Quote currency symbol
            - base_ccy_precision : Number of decimals for base currency
            - quote_ccy_precision : Number of decimals for quote currency
            - status : Current market status
            - is_amm_available : Flag for AMM feature availability
            - is_margin_available : Flag for margin trading support
            - is_pre_market_trading_available : Flag for pre-market support
            - is_api_trading_available : Indicates API-level trading support
        """

        params = {}
        if market:
            self._ensure_spot_market_available(market_name=market)
        elif self._spot_market_status_cache and not force_reload:
            return self._spot_market_status_cache

        if isinstance(market, list):
            params["market"] = ",".join(market)
        elif isinstance(market, str):
            params["market"] = market

        response = self.request(
            "GET", Spot_HTTP.Ticker.GET_MARKET_STATUS, params=params, public_url=True
        )

        self._spot_market_status_cache = response

        return response

    def get_spot_market_transactions(
        self, market: str, limit: Optional[int] = None, last_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve recent public transactions from CoinEx spot market.

        This method queries the `/spot/deals` endpoint to fetch recent executed trades
        on the specified market, including price, volume, side, and timestamp.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT"). Required.

        limit : int, optional
            Maximum number of records to retrieve (default: 100, max: 1000).

        last_id : int, optional
            Starting point deal ID. Pass 0 to fetch from the most recent transaction.

        Returns
        -------
        Dict[str, Any]
            List of transaction records:
            - deal_id : Unique transaction ID
            - created_at : Timestamp in milliseconds
            - side : "buy" or "sell"
            - price : Executed price
            - amount : Executed volume
        """

        if market:
            self._ensure_spot_market_available(market_name=market)

        params: Dict[str, Any] = {"market": market}

        if limit is not None:
            params["limit"] = limit
        if last_id is not None:
            params["last_id"] = last_id

        return self.request(
            method="GET",
            url=Spot_HTTP.Ticker.GET_MARKET_TRANSACTIONS,
            params=params,
            public_url=True,
        )

    def get_spot_market_candlesticks(
        self,
        market: str,
        period: str,
        limit: Optional[int] = None,
        price_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve candlestick data for the specified market and time period.

        Parameters
        ----------
        market : str
            Market symbol, e.g. "LATUSDT". Required.

        period : str
            Candlestick resolution period. One of:
            ["1min", "3min", "5min", "15min", "30min", "1hour", "2hour", "4hour",
            "6hour", "12hour", "1day", "3day", "1week"]. Required.

        limit : int, optional
            Number of candlesticks to retrieve (default: 100, max: 1000).

        price_type : str, optional
            Type of price for candles. Defaults to "latest_price".
            Note: "mark_price" is not available in spot markets.

        Returns
        -------
        Dict[str, Any]
            API response with candlestick data containing:
            - created_at : Timestamp in milliseconds
            - open, close, high, low : Price points
            - volume : Traded volume
            - value : Traded value
        """

        valid_periods = [
            "1min",
            "3min",
            "5min",
            "15min",
            "30min",
            "1hour",
            "2hour",
            "4hour",
            "6hour",
            "12hour",
            "1day",
            "3day",
            "1week",
        ]

        if market:
            self._ensure_spot_market_available(market)

        if price_type:
            if price_type not in CoinEx_Definitions.TriggerPriceType.get_values():
                raise ValueError(
                    f"Price type must be one of {CoinEx_Definitions.TriggerPriceType.get_values()}"
                )

        if period not in valid_periods:
            raise ValueError(f"period must be one of {valid_periods}.")

        params: Dict[str, Any] = {"market": market, "period": period}

        if limit is not None:
            params["limit"] = limit
        if price_type is not None:
            params["price_type"] = price_type

        return self.request(
            method="GET",
            url=Spot_HTTP.Ticker.GET_MARKET_CANDLESTICK,
            params=params,
            public_url=True,
        )

    def get_spot_market_index(self, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve index price data for a specific market or multiple markets.

        Parameters
        ----------
        market : str, optional
            Comma-separated list of market symbols (e.g., "BTCUSDT,ETHUSDT").
            Leave empty to fetch index prices for all available markets.
            A maximum of 10 markets can be queried at once.

        Returns
        -------
        Dict[str, Any]
            API response containing index details for each market:
            - market : Market name
            - created_at : Timestamp in milliseconds
            - price : Current index price
            - sources : List of source exchanges contributing to the index
                - exchange : Exchange name
                - created_at : Data timestamp
                - index_weight : Weighting factor
                - index_price : Price from this exchange

        """

        if market:
            self._ensure_spot_market_available(market_name=market)

        if isinstance(market, list):
            market = ",".join(market)

        params = {"market": market} if market else {}

        return self.request(
            method="GET",
            url=Spot_HTTP.Ticker.GET_MARKET_INDEX,
            params=params,
            public_url=True,
        )

        # <<< Spot << Ticker menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

        # >>> Spot >> Executions menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_spot_user_transaction(
        self,
        market: str,
        market_type: str = CoinEx_Definitions.MarketType.SPOT,
        side: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve user's transaction history in CoinEx Spot market.

        This method queries the `/spot/user-deals` endpoint to fetch executed deals,
        including order details, pricing, volume, fee, and role in transaction.

        Parameters
        ----------
        market : str
            Target market symbol (e.g., "BTCUSDT"). Required.

        market_type : str
            Market type; must be "SPOT" or "MARGIN" for this endpoint.

        side : str, optional
            Order direction filter. Use "buy", "sell", or None to include both sides.

        start_time : int, optional
            Start of query window in UNIX timestamp (milliseconds).

        end_time : int, optional
            End of query window in UNIX timestamp (milliseconds).

        page : int, optional
            Pagination page number. Default is 1.

        limit : int, optional
            Number of records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed response with list of user transactions:
            - deal_id : Unique transaction ID
            - created_at : Timestamp of execution
            - order_id : Linked order ID
            - market : Market name
            - margin_market : Margin market name or null
            - side : Order side ("buy"/"sell")
            - price : Execution price
            - amount : Filled quantity
            - role : Execution role ("taker"/"maker")
            - fee : Fee charged
            - fee_ccy : Currency of fee
        """

        if market:
            self._ensure_spot_market_available(market_name=market)

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {"market": market, "market_type": market_type}

        if side:
            params["side"] = side
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if page:
            params["page"] = page
        if limit:
            params["limit"] = limit

        return self.request(
            "GET",
            Spot_HTTP.Executions.GET_USER_TRANSACTION,
            params=params,
            public_url=False,
        )

    def get_spot_user_order_transaction(
        self,
        market: str,
        order_id: int,
        market_type: str = CoinEx_Definitions.MarketType.SPOT,
        page: Optional[int] = 1,
        limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve executed transaction details for a specific order.

        This method queries the `/spot/order-deals` endpoint to fetch order-level
        deal information, including price, amount, role, fee, and more.

        Parameters
        ----------
        market : str
            Market name (e.g., "BTCUSDT")
        market_type : str
            Market type: must be "SPOT" or "MARGIN"
        order_id : int
            Unique identifier for the user's order
        page : int, optional
            Pagination index, default is 1
        limit : int, optional
            Number of transactions per page, default is 10

        Returns
        -------
        Dict[str, Any]
            A dictionary containing transaction data and pagination metadata.
        """

        if market:
            self._ensure_spot_market_available(market_name=market)

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {
            "market": market,
            "market_type": market_type,
            "order_id": order_id,
            "page": page,
            "limit": limit,
        }

        return self.request(
            "GET",
            Spot_HTTP.Executions.GET_USER_ORDER_TRANSACTION,
            params=params,
            public_url=False,
        )

        # <<< Spot << Executions menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

    # <<< SPOT Tab --------------------------------------------------------------------------------------------------------------------- end

    # >>> ASSET Tab ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ start

    # >>> Asset >> Balance menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_spot_balance(self) -> Dict[str, Any]:
        """
        Retrieve current balance from CoinEx Spot Account.

        This method queries the `/assets/spot/balance` endpoint to fetch
        available and frozen balances for all currencies held in the Spot account.

        Returns:
            Dict[str, Any]
                Parsed JSON response from CoinEx Spot API.
                Each currency includes:
                - ccy : Currency name (e.g., 'USDT', 'BTC')
                - available : Balance available for trading
                - frozen : Assets locked due to orders, fees, etc.
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_BALANCE_IN_SPOT_ACCOUNT, public_url=False
        )

    def get_futures_balance(self) -> Dict[str, Any]:
        """
        Retrieve current balance from CoinEx Futures Account.

        This method queries the `/assets/futures/balance` endpoint to fetch
        margin-related details for each currency held in the Futures account.

        Returns:
        Dict[str, Any]
            Parsed JSON response from CoinEx Futures API.
            Each currency includes:
            - ccy : Currency name (e.g., 'USDT', 'BTC')
            - available : Balance available for margin/trading
            - frozen : Locked assets due to pending orders or fees
            - margin : Total margin used by current open positions
            - unrealized_pnl : PnL estimated on current mark/latest price
            - transferrable : Assets eligible for transfer out
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_BALANCE_IN_FUTURES_ACCOUNT, public_url=False
        )

    def get_credit_account_info(self) -> Dict[str, Any]:
        """
        Retrieve credit account information from CoinEx.

        Queries the `/assets/credit/info` endpoint to get status of the credit account,
        including total equity, repayment obligations, and withdrawal metrics.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing:
            - equity : Total asset value in the credit account
            - repaid : Amount pending repayment
            - risk_rate : Risk level of credit exposure (may be empty)
            - withdrawal_risk : Risk level affecting withdrawal permissions
            - withdrawal_value : Max withdrawable value based on margin constraints
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_INFO_IN_CREDIT_ACCOUNT, public_url=False
        )

    def get_amm_liquidity(self) -> Dict[str, Any]:
        """
        Retrieve AMM account liquidity from CoinEx.

        This method queries the `/assets/amm/liquidity` endpoint to fetch
        liquidity distribution across AMM pools in the user's account.

        Returns
        -------
        Dict[str, Any]
            Parsed JSON response from CoinEx AMM API.
            Each pool entry includes:
            - market : AMM market (e.g., 'CETUSDT')
            - base_ccy : Base currency symbol
            - quote_ccy : Quote currency symbol
            - base_ccy_amount : Liquidity amount in base currency
            - quote_ccy_amount : Liquidity amount in quote currency
            - liquidity_proportion : Pool share percentage (0–100)
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_AMM_ACCOUNT_LIQUIDITY, public_url=False
        )

    def get_spot_transaction_history(
        self,
        type: str = CoinEx_Definitions.TranscationType.TRADE,
        ccy: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve transaction history in CoinEx Spot Account.

        This method queries the `/assets/spot/transcation-history` endpoint to fetch
        historical asset changes, filtered by transaction type and optional time window.

        Parameters
        ----------
        type : str
            Transaction history type (e.g., "trade", "deposit", "withdraw").

        ccy : str, optional
            Currency symbol (e.g., "USDT"). If omitted, returns all currencies.

        start_time : int, optional
            Start time as UNIX timestamp in milliseconds.

        end_time : int, optional
            End time as UNIX timestamp in milliseconds.

        page : int, optional
            Page number for pagination. Default is 1.

        limit : int, optional
            Records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed JSON from CoinEx API including:
            - created_at : Time of transaction
            - ccy : Currency name
            - type : Type of transaction
            - change : Amount of asset change
            - balance : Final balance after transaction
        """
        if type not in CoinEx_Definitions.TranscationType.get_values():
            raise ValueError(
                f"transcation type must be one of {CoinEx_Definitions.TranscationType.get_values()}"
            )

        params = {"type": type}

        if ccy:
            params["ccy"] = ccy
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if page:
            params["page"] = page
        if limit:
            params["limit"] = limit

        return self.request(
            "GET",
            Asset_HTTP.Balance.GET_SPOT_TRANSACTION_HISTORY,
            params=params,
            public_url=False,
        )

    def get_credit_balance(self) -> List[Dict[str, Any]]:
        """
        Retrieve balance details of the user's credit account from CoinEx.

        Accesses the `/assets/credit/balance` endpoint to fetch the breakdown of
        repayment and interest obligations per currency.

        Returns
        -------
        List[Dict[str, Any]]
            A list of credit account balances for each borrowed currency:
            - ccy : Currency symbol (e.g., 'USDT')
            - repaid : Amount of borrowed currency pending repayment
            - interest : Accumulated interest to be repaid
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_BALANCE_IN_CREDIT_ACCOUNT, public_url=False
        )

    def get_financial_balance(self) -> Dict[str, Any]:
        """
        Retrieve current balance from CoinEx Financial Account.

        This method queries the `/assets/financial/balance` endpoint to fetch
        available and frozen balances for all currencies held in the Financial account.

        Returns
        -------
        Dict[str, Any]
            Parsed JSON response from CoinEx Financial API.
            Each currency includes:
            - ccy : Currency name (e.g., 'USDT', 'BTC')
            - available : Balance available for financial operations
            - frozen : Assets locked due to financial products or settlement
        """
        return self.request(
            "GET", Asset_HTTP.Balance.GET_BALANCE_IN_FINANCIAL_ACCOUNT, public_url=False
        )

    def get_margin_balance(self, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve current balance from CoinEx Margin Account.

        This method queries the `/assets/margin/balance` endpoint to fetch
        margin account details, including available funds, frozen assets,
        repayment requirements, and risk metrics.

        Parameters
        ----------
        market : str, optional
            Specific margin market name (e.g., "BTCUSDT").
            If omitted, returns balances for all margin accounts.

        Returns
        -------
        Dict[str, Any]
            Parsed JSON response from CoinEx Margin API.
            Each entry includes:
            - margin_account : Margin market name
            - base_ccy, quote_ccy : Currency pair components
            - available : Assets available for trading
            - frozen : Locked margin assets
            - repaid : Borrowed amounts pending repayment
            - interest : Accrued interest to be paid
            - risk_rate : Account risk exposure ("" if zero)
            - liq_price : Liquidation threshold ("" if none)
        """
        params = {}
        if market:
            self._ensure_spot_market_available(market_name=market)
            params["market"] = market

        return self.request(
            "GET",
            Asset_HTTP.Balance.GET_BALANCE_IN_MARGIN_ACCOUNT,
            params=params,
            public_url=False,
        )

        # <<< Asset << Balance menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

    # <<< ASSET Tab ---------------------------------------------------------------------------------------------------------- end

    # >>> FUTURES Tab ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ start

    def _ensure_futures_market_available(self, market_name: str):
        """
        Check whether a market is available in the exchange. Raises if not.

        Args:
            market_name (str): Market to verify.

        Raises:
            ValueError: If the market is not available.
        """
        if self._futures_markets_list_cache is None:
            self._futures_markets_list_cache = self.get_futures_available_markets()

        if "," in market_name:
            market_name = market_name.split(",")

        if isinstance(market_name, list):
            for market in market_name:
                if market not in self._futures_markets_list_cache:
                    raise ValueError(
                        f"Market '{market}' not found in available markets. "
                        f"Call `.get_futures_available_markets()` to see the full list."
                    )

        elif isinstance(market_name, str):
            if market_name not in self._futures_markets_list_cache:
                raise ValueError(
                    f"Market '{market_name}' not found in available markets. "
                    f"Call `.get_futures_available_markets()` to see the full list."
                )

    def get_futures_available_markets(self) -> List[str]:
        """
        Retrieve the list of all available trading symbols (markets) on CoinEx.

        Returns:
            List[str]: A list of market symbols like ['BTCUSDT', 'ETHUSDT', ...].

        Raises:
            RuntimeError: If request fails or API response indicates an error.
        """

        data = self.get_futures_market_status()

        markets = [item["market"] for item in data["data"]]
        self._spot_markets_list_cache = markets
        return markets

        # >>> FUTURES >> Ticker menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_futures_market_status(
        self, market: Optional[Union[str, List[str]]] = None, force_reload: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve status and metadata for one or more futures markets.

        This method queries the `/futures/market` endpoint to fetch
        contract details, fee rates, precision, leverage options,
        and availability status.

        Parameters
        ----------
        markets : str or List[str], optional
            List of market symbols (e.g., ["BTCUSDT", "ETHUSDT"]).
            If None or empty, returns all available markets.
            Max 10 markets per request.
        force_reload : bool
            The function uses a caching approach for better performance.
            if force_reload been True, function download market status frome CoinEx api again.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing market metadata:
            - market : Market name
            - contract_type : "linear" or other
            - maker_fee_rate / taker_fee_rate : Fee rates
            - min_amount : Minimum order size
            - base_ccy / quote_ccy : Currency pair
            - base_ccy_precision / quote_ccy_precision : Decimal precision
            - tick_size : Price increment
            - leverage : List of supported leverage levels
            - open_interest_volume : Total position size
            - is_market_available : Whether trading is enabled
            - is_copy_trading_available : Whether copy trading is supported
        """
        params: Dict[str, Any] = {}

        if market:
            self._ensure_futures_market_available(market)
            params["market"] = market
        elif self._futures_market_status_cache and not force_reload:
            return self._futures_market_status_cache

        if isinstance(market, list):
            params["market"] = ",".join(market)
        elif isinstance(market, str):
            params["market"] = market

        response = self.request(
            "GET", Futures_HTTP.Ticker.GET_MARKET_STATUS, params=params, public_url=True
        )

        self._futures_market_status_cache = response

        return response

    def get_futures_market_information(
        self, market: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve ticker-level market data for one or more futures markets.

        Parameters
        ----------
        markets : str or List[str], optional
            A market symbol or a list of market symbols (e.g., "BTCUSDT" or ["BTCUSDT", "ETHUSDT"]).
            If None or empty, queries all available markets.
            Maximum of 10 markets allowed.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing market data for each symbol:
            - market : Market name
            - last : Latest traded price
            - open : Opening price
            - close : Closing price
            - high : Daily high
            - low : Daily low
            - volume : Total filled volume
            - value : Total filled value
            - volume_sell : Taker sell volume
            - volume_buy : Taker buy volume
            - index_price : Index price
            - mark_price : Mark price
            - open_interest_volume : Total open interest
            - period : Fixed at 86400 (1 day)
        """

        if market:
            self._ensure_futures_market_available(market_name=market)

        if isinstance(market, list):
            market = ",".join(market)

        params = {}
        if market:
            params["market"] = market

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_INFORMATION,
            params=params,
            public_url=True,
        )

    def get_futures_market_candlesticks(
        self,
        market: str,
        period: str,
        limit: Optional[int] = None,
        price_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve candlestick (K-line) data for a specific futures market and time period.

        This method queries the `/futures/kline` endpoint to fetch OHLCV data
        for technical analysis or charting.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "LATUSDT"). Required.

        period : str
            Candlestick resolution. One of:
            ["1min", "3min", "5min", "15min", "30min", "1hour", "2hour", "4hour",
            "6hour", "12hour", "1day", "3day", "1week"]. Required.

        limit : int, optional
            Number of candlesticks to retrieve (default: 100, max: 1000).

        price_type : str, optional
            Price type for candles. Defaults to "latest_price".

        Returns
        -------
        Dict[str, Any]
            Parsed response containing candlestick data:
            - market : Market name
            - created_at : Timestamp in milliseconds
            - open : Opening price
            - close : Closing price
            - high : Highest price
            - low : Lowest price
            - volume : Traded volume
            - value : Traded value
        """

        if market:
            self._ensure_futures_market_available(market_name=market)

        valid_periods = [
            "1min",
            "3min",
            "5min",
            "15min",
            "30min",
            "1hour",
            "2hour",
            "4hour",
            "6hour",
            "12hour",
            "1day",
            "3day",
            "1week",
        ]

        if period not in valid_periods:
            raise ValueError(f"period must be one of {valid_periods}.")

        if price_type:
            if price_type not in CoinEx_Definitions.TriggerPriceType.get_values():
                raise ValueError(
                    f"Price type must be one of {CoinEx_Definitions.TriggerPriceType.get_values()}"
                )

        params: Dict[str, Any] = {"market": market, "period": period}

        if limit is not None:
            params["limit"] = limit
        if price_type is not None:
            params["price_type"] = price_type

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_CANDLESTICK,
            params=params,
            public_url=True,
        )

    def get_futures_market_depth(
        self, market: str, limit: int, interval: str
    ) -> Dict[str, Any]:
        """
        Retrieve order book depth for a given futures market.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").

        limit : int
            Number of depth levels to retrieve. Must be one of [5, 10, 20, 50].

        interval : str
            Merge interval for price levels. Must be one of:
            ["0", "0.00000000001", "0.000000000001", "0.0000000001", "0.000000001", "0.00000001",
            "0.0000001", "0.000001", "0.00001", "0.0001", "0.001", "0.01", "0.1", "1", "10", "100", "1000"]

        Returns
        -------
        Dict[str, Any]
            Depth data including:
            - asks : List of [price, size] for sell orders
            - bids : List of [price, size] for buy orders
            - last : Last traded price
            - updated_at : Timestamp in milliseconds
            - checksum : CRC32 checksum for data integrity
        """

        if limit not in [5, 10, 20, 50]:
            raise ValueError(f"Invalid limit: {limit}. Must be one of [5, 10, 20, 50].")

        valid_intervals = [
            "0",
            "0.00000000001",
            "0.000000000001",
            "0.0000000001",
            "0.000000001",
            "0.00000001",
            "0.0000001",
            "0.000001",
            "0.00001",
            "0.0001",
            "0.001",
            "0.01",
            "0.1",
            "1",
            "10",
            "100",
            "1000",
        ]
        if interval not in valid_intervals:
            raise ValueError(
                f"Invalid interval: {interval}. Must be one of {valid_intervals}."
            )

        self._ensure_futures_market_available(market_name=market)

        params = {"market": market, "limit": limit, "interval": interval}

        return self.request(
            "GET", Futures_HTTP.Ticker.GET_MARKET_DEPTH, params=params, public_url=True
        )

    def get_futures_market_index(
        self, market: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve index price and composition for one or more futures markets.

        This method queries the `/futures/index` endpoint to fetch the aggregated
        index price and its underlying exchange components.

        Parameters
        ----------
        market : str or List[str], optional
            Market name(s) to query (e.g., "BTCUSDT" or ["BTCUSDT", "ETHUSDT"]).
            Pass None or empty string to query all available markets.
            Maximum of 10 markets allowed.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing:
            - market : Market name
            - created_at : Timestamp in milliseconds
            - price : Aggregated index price
            - sources : List of index components with:
                - exchange : Exchange name
                - created_at : Data collection timestamp
                - index_weight : Weight in index calculation
        """

        if market:
            self._ensure_futures_market_available(market_name=market)

        if isinstance(market, list):
            market = ",".join(market)

        params = {}
        if market:
            params["market"] = market

        return self.request(
            "GET", Futures_HTTP.Ticker.GET_MARKET_INDEX, params=params, public_url=True
        )

    def get_futures_market_transactions(
        self, market: str, limit: Optional[int] = 100, last_id: Optional[int] = 0
    ) -> Dict[str, Any]:
        """
        Retrieve recent executed transactions for a given futures market.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").

        limit : int, optional
            Maximum number of records to retrieve (default: 100, max: 1000).

        last_id : int, optional
            Starting deal ID. Use 0 to fetch from the latest.

        Returns
        -------
        Dict[str, Any]
            List of transaction records:
            - deal_id : Unique transaction ID
            - created_at : Timestamp in milliseconds
            - side : "buy" or "sell" (taker side)
            - price : Executed price
            - amount : Executed volume
        """
        params = {"market": market, "limit": limit, "last_id": last_id}

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_TRANSACTIONS,
            params=params,
            public_url=True,
        )

    def get_futures_funding_rate(
        self, market: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve current and projected funding rates for one or more futures markets.

        Parameters
        ----------
        markets : str or List[str], optional
            Market symbol(s) (e.g., "BTCUSDT" or ["BTCUSDT", "ETHUSDT"]).
            If None or empty, returns funding data for all available markets.
            Maximum of 10 markets allowed.

        Returns
        -------
        Dict[str, Any]
            List of funding rate entries per market:
            - market : Market name
            - mark_price : Current mark price
            - latest_funding_rate : Current funding rate (paid/received)
            - next_funding_rate : Projected next funding rate
            - max_funding_rate : Maximum allowed funding rate
            - min_funding_rate : Minimum allowed funding rate
            - latest_funding_time : Timestamp of current rate calculation
            - next_funding_time : Timestamp of next rate calculation
        """
        if market:
            self._ensure_futures_market_available(market_name=market)

        if isinstance(market, list):
            market = ",".join(market)

        params = {}
        if market:
            params["market"] = market

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_FUNDING_RATE,
            params=params,
            public_url=True,
        )

    def get_futures_funding_rate_history(
        self,
        market: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve historical funding rates for a specific futures market.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").
        start_time : int, optional
            Start timestamp in milliseconds. If None, no lower bound.
        end_time : int, optional
            End timestamp in milliseconds. If None, no upper bound.
        page : int, default=1
            Page number for pagination.
        limit : int, default=10
            Number of records per page (max may vary by API).

        Returns
        -------
        Dict[str, Any]
            Historical funding rate entries:
            - market : Market name
            - funding_time : Timestamp of funding rate collection
            - theoretical_funding_rate : Calculated funding rate before settlement
            - actual_funding_rate : Final funding rate charged
        """

        if market:
            self._ensure_futures_market_available(market_name=market)

        params = {"market": market, "page": page, "limit": limit}

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_FUNDING_RATE_HISTORY,
            params=params,
            public_url=True,
        )

    def get_futures_premium_index_history(
        self,
        market: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve historical premium index data for a specific futures market.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").
        start_time : int, optional
            Start timestamp in milliseconds. Default is 8 hours ago.
            Max range: 1 day. Max lookback: 30 days.
        end_time : int, optional
            End timestamp in milliseconds. Default is now.
        page : int, default=1
            Page number for pagination.
        limit : int, default=10
            Number of records per page.

        Returns
        -------
        Dict[str, Any]
            Historical premium index entries:
            - market : Market name
            - created_at : Timestamp of data point
            - premium_index : Premium index value (used in funding rate calculation)
        """
        params = {"market": market, "page": page, "limit": limit}

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_PREMIUM_INDEX_HISTORY,
            params=params,
            public_url=True,
        )

    def get_position_levels(
        self, market: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve position level tiers for one or more futures markets.

        This method returns leverage brackets and margin requirements
        based on position size.

        Parameters
        ----------
        markets : str or List[str], optional
            Market symbol(s) (e.g., "BTCUSDT" or ["BTCUSDT", "ETHUSDT"]).
            If None or empty, returns data for all markets.
            Maximum of 10 markets allowed.

        Returns
        -------
        Dict[str, Any]
            List of position level entries per market:
            - market : Market name
            - level : List of tiers with:
                - amount : Position size upper bound
                - leverage : Max leverage allowed
                - maintenance_margin_rate : Maintenance margin requirement
                - min_initial_margin_rate : Minimum initial margin requirement
        """

        if market:
            self._ensure_futures_market_available(market_name=market)

        if isinstance(market, list):
            market = ",".join(market)

        params = {}
        if market:
            params["market"] = market

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_POSITION_LEVEL,
            params=params,
            public_url=True,
        )

    def get_futures_market_liquidation_history(
        self,
        market: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve historical liquidation events for a specific futures market.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").
        start_time : int, optional
            Start timestamp in milliseconds.
        end_time : int, optional
            End timestamp in milliseconds.
        page : int, default=1
            Page number for pagination.
        limit : int, default=10
            Number of records per page.

        Returns
        -------
        Dict[str, Any]
            List of liquidation events with:
            - market : Market name
            - side : "long" or "short"
            - liq_price : Liquidation price
            - liq_amount : Liquidated position size
            - bkr_price : Bankruptcy price
            - created_at : Timestamp of event
        """
        if market:
            self._ensure_futures_market_available(market_name=market)

        params = {"market": market, "page": page, "limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_LIQUIDATION_HISTORY,
            params=params,
            public_url=True,
        )

    def get_futures_market_basis_rate_history(
        self,
        market: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve historical basis rate data for a specific futures market.

        Basis rate reflects the premium or discount of the futures price
        relative to the spot price.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").
        start_time : int, optional
            Start timestamp in milliseconds.
            Defaults to 7 days ago if not provided.
        end_time : int, optional
            End timestamp in milliseconds.
            Defaults to now if not provided.

        Returns
        -------
        Dict[str, Any]
            List of basis rate entries with:
            - market : Market name
            - created_at : Timestamp of data point
            - basis_rate : Basis rate value
        """
        if market:
            self._ensure_futures_market_available(market_name=market)

        params = {"market": market}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.request(
            "GET",
            Futures_HTTP.Ticker.GET_MARKET_BASIS_RATE_HISTORY,
            params=params,
            public_url=True,
        )

        # <<< FUTURES << Ticker menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

        # >>> FUTURES >> Orders menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_futures_filled_order(
        self,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        market: Optional[str] = None,
        side: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve filled or partially filled orders from CoinEx.

        This method queries the `/futures/finished-order` endpoint to fetch
        completed order records, including filled amounts, fees, and timestamps.

        ⚠️ Note: Orders that were canceled without any fills are not stored
        and cannot be retrieved via this endpoint.

        Parameters
        ----------
        market_type : str
            Market type. Must be "FUTURES" for this endpoint.

        market : str, optional
            Market symbol (e.g., "CETUSDT"). If omitted, returns all markets.

        side : str, optional
            Order direction: "buy", "sell", or None for both.

        page : int, optional
            Pagination index. Default is 1.

        limit : int, optional
            Number of records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing filled order details:
            - order_id : Unique order ID
            - market : Market name
            - market_type : Market type
            - side : Buy or sell
            - type : Order type (e.g., "limit")
            - amount : Total order amount
            - price : Order price
            - unfilled_amount : Remaining amount
            - filled_amount : Executed amount
            - filled_value : Executed value
            - client_id : Custom client identifier
            - fee : Trading fee
            - fee_ccy : Fee currency
            - maker_fee_rate : Maker fee rate
            - taker_fee_rate : Taker fee rate
            - created_at : Order creation timestamp
            - updated_at : Last update timestamp
        """

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {
            "market_type": market_type,
            "page": page,
            "limit": limit,
        }

        if market:
            self._ensure_spot_market_available(market_name=market)
            params["market"] = market
        if side:
            params["side"] = side

        return self.request(
            "GET", Futures_HTTP.Orders.GET_FILLED_ORDER, params=params, public_url=False
        )

    def get_futures_unfilled_order(
        self,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        market: Optional[str] = None,
        side: Optional[str] = None,
        client_id: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve unfilled or partially filled futures orders from CoinEx.

        This method queries the `/futures/pending-order` endpoint to fetch
        active orders that are still open or partially executed.

        ⚠️ Note: If an order is canceled without any fills, it will not be
        stored or retrievable via this endpoint.

        Parameters
        ----------
        market_type : str
            Market type. Must be "FUTURES" for this endpoint.

        market : str, optional
            Market symbol (e.g., "CETUSDT"). If omitted, returns all markets.

        side : str, optional
            Order direction: "buy", "sell", or None for both.

        client_id : str, optional
            Custom client identifier used during order placement.

        page : int, optional
            Pagination index. Default is 1.

        limit : int, optional
            Number of records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing pending order details:
            - order_id : Unique order ID
            - market : Market name
            - market_type : Market type
            - side : Buy or sell
            - type : Order type (e.g., "limit")
            - amount : Total order amount
            - price : Order price
            - unfilled_amount : Remaining amount
            - filled_amount : Executed amount
            - filled_value : Executed value
            - client_id : Custom client identifier
            - fee : Trading fee
            - fee_ccy : Fee currency
            - maker_fee_rate : Maker fee rate
            - taker_fee_rate : Taker fee rate
            - last_filled_amount : Amount filled in last transaction
            - last_filled_price : Price of last fill
            - realized_pnl : Realized profit/loss
            - created_at : Order creation timestamp
            - updated_at : Last update timestamp
        """

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {
            "market_type": market_type,
            "page": page,
            "limit": limit,
        }

        if market:
            self._ensure_futures_market_available(market)
            params["market"] = market
        if side:
            params["side"] = side
        if client_id:
            params["client_id"] = client_id

        return self.request(
            "GET",
            Futures_HTTP.Orders.GET_UNFILLED_ORDER,
            params=params,
            public_url=False,
        )

        # <<< FUTURES << Orders menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

        # >>> FUTURES >> Executions menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_futures_user_transactions(
        self,
        market: str,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        side: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = None,
        limit: int = None,
    ) -> Dict[str, Any]:
        """
        Retrieve user transaction history (executed deals) from CoinEx futures.

        This method queries the `/futures/user-deals` endpoint to fetch
        historical trade executions, including price, volume, fees, and role.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").

        market_type : str
            Market type. Must be "FUTURES" for this endpoint.

        side : str, optional
            Order direction: "buy", "sell", or None for both.

        start_time : int, optional
            Start of time range (Unix timestamp in milliseconds).

        end_time : int, optional
            End of time range (Unix timestamp in milliseconds).

        page : int, optional
            Pagination index. Default is 1.

        limit : int, optional
            Number of records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing transaction details:
            - deal_id : Unique transaction ID
            - created_at : Timestamp of execution
            - market : Market name
            - side : Buy or sell
            - order_id : Associated order ID
            - position_id : Position ID
            - price : Execution price
            - amount : Executed volume
            - role : "maker" or "taker"
            - fee : Trading fee
            - fee_ccy : Fee currency
        """

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        if market:
            self._ensure_futures_market_available(market)

        params: Dict[str, Any] = {
            "market": market,
            "market_type": market_type,
        }

        if side:
            params["side"] = side
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if page:
            params["page"] = page
        if limit:
            params["limit"] = limit

        return self.request(
            "GET",
            Futures_HTTP.Executions.GET_USER_TRANSACTION,
            params=params,
            public_url=False,
        )

    def get_futures_order_transaction(
        self,
        market: str,
        order_id: int,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        page: Optional[int] = 1,
        limit: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Retrieve executed transaction details for a specific futures order.

        This method queries the `/futures/order-deals` endpoint to fetch
        trade-level execution data linked to a given order ID.

        Parameters
        ----------
        market : str
            Market symbol (e.g., "BTCUSDT").

        market_type : str
            Market type. Must be "FUTURES" for this endpoint.

        order_id : int
            Unique identifier of the order to query.

        page : int, optional
            Pagination index. Default is 1.

        limit : int, optional
            Number of records per page. Default is 10.

        Returns
        -------
        Dict[str, Any]
            Parsed response containing transaction details:
            - deal_id : Unique transaction ID
            - created_at : Timestamp in milliseconds
            - order_id : Order ID
            - position_id : Position ID
            - market : Market name
            - side : Buy or sell
            - price : Execution price
            - amount : Executed volume
            - role : "maker" or "taker"
            - fee : Trading fee
            - fee_ccy : Fee currency
        """
        if market:
            self._ensure_futures_market_available(market_name=market)

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {
            "market": market,
            "market_type": market_type,
            "order_id": order_id,
            "page": page,
            "limit": limit,
        }

        return self.request(
            "GET",
            Futures_HTTP.Executions.GET_USER_ORDER_TRANSACTION,
            params=params,
            public_url=False,
        )

        # <<< FUTURES << Executions menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

        # >>> FUTURES >> Position menu vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv start

    def get_futures_historical_position(
        self,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        market: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = None,
        limit: int = None,
    ) -> Dict[str, Any]:
        """
        Retrieve historical closed position data from CoinEx Futures.

        This function fetches historical positions that have been closed
        in the CoinEx Futures market. It's useful for tracking performance,
        calculating realized PnL, and performing backtesting on past trades.

        Parameters:
        ----------
        market_type : str
            Must be set to "FUTURES". Determines the market type.

        market : str, optional
            Specific market symbol (e.g., "BTCUSDT"). If not provided,
            data for all markets will be returned.

        start_time : int, optional
            Start of time range as Unix timestamp in milliseconds.

        end_time : int, optional
            End of time range as Unix timestamp in milliseconds.

        page : int, default=1
            Page number for pagination.

        limit : int, default=10
            Number of records to fetch per page.

        Returns:
        -------
        Dict[str, Any]
            Parsed JSON response from CoinEx containing historical position data.
            Each record includes:
            - position_id
            - deal_id
            - market
            - side
            - amount, price
            - fee
            - timestamps and additional trade metadata
        """

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        if market:
            self._ensure_spot_market_available(market_name=market)

        params = {
            "market_type": market_type,
        }
        if market:
            params["market"] = market
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if limit:
            params["limit"] = limit
        if page:
            params["page"] = page

        return self.request(
            "GET",
            Futures_HTTP.Position.GET_HISTORICAL_POSITION,
            params=params,
            public_url=False,
        )

    def get_futures_positions_funding_rate_history(
        self,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        market: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page: int = 1,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical funding rate and funding value records for futures positions.

        This includes settlement price, funding rate, funding value, and timestamps
        for each funding event associated with the authenticated account.

        Parameters
        ----------
        market_type : str, optional
            Market type. Must be "FUTURES" for futures funding history.
            Default is "FUTURES".
        market : str, optional
            Specific market symbol (e.g., "BTCUSDT"). If not provided,
            returns funding history across all markets.
        start_time : int, optional
            Start timestamp in milliseconds. If not provided, no time filtering is applied.
        end_time : int, optional
            End timestamp in milliseconds. If not provided, no time filtering is applied.
        page : int, optional
            Pagination index. Default is 1.
        limit : int, optional
            Number of records per page. Default is 100.

        Returns
        -------
        List[Dict[str, Any]]
            List of funding history entries with:
            - market : Market symbol
            - market_type : "FUTURES"
            - ccy : Settlement currency
            - position_id : Unique position ID
            - side : "long" or "short"
            - margin_mode : "cross" or "isolated"
            - open_interest : Position size
            - settle_price : Settlement price
            - funding_rate : Funding rate applied
            - funding_value : Funding fee charged
            - created_at : Timestamp of funding event
        """

        if market_type != CoinEx_Definitions.MarketType.FUTURES:
            raise ValueError(
                "Funding rate history is only available for FUTURES market type."
            )

        params: Dict[str, Any] = {
            "market_type": market_type,
            "page": page,
            "limit": limit,
        }

        if market:
            params["market"] = market
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return self.request(
            "GET",
            Futures_HTTP.Position.GET_POSITION_FUNDING_RATE_HISTORY,
            params=params,
            public_url=False,
        )

    def get_futures_current_positions(
        self,
        market_type: str = CoinEx_Definitions.MarketType.FUTURES,
        market: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve current pending futures positions for the authenticated account.

        This includes detailed position metrics such as unrealized PnL,
        entry price, leverage, liquidation price, and ADL level.

        Parameters
        ----------
        market_type : str, optional
            Type of market. Must be "FUTURES" for futures positions.
            Default is "FUTURES".
        market : str, optional
            Specific market symbol (e.g., "BTCUSDT"). If not provided,
            returns positions across all markets.
        page : int, optional
            Pagination index. Default is 1.
        limit : int, optional
            Number of positions per page. Default is 100.

        Returns
        -------
        List[Dict[str, Any]]
            List of structured position entries with:
            - position_id : Unique position identifier
            - market : Market symbol
            - side : "long" or "short"
            - margin_mode : "cross" or "isolated"
            - entry_price : Average entry price
            - unrealized_pnl : Current unrealized profit/loss
            - realized_pnl : Realized profit/loss
            - position_value : Cumulative position value
            - leverage : Leverage used
            - liq_price : Liquidation price
            - bkr_price : Bankruptcy price
            - adl_level : Auto-deleveraging risk level (1–5)
            - created_at : Timestamp of position creation
            - updated_at : Timestamp of last update
        """

        if market_type not in CoinEx_Definitions.MarketType.get_values():
            raise ValueError(
                f"market type must be one of {CoinEx_Definitions.MarketType.get_values()}"
            )

        params: Dict[str, Any] = {
            "market_type": market_type,
            "page": page,
            "limit": limit,
        }
        if market:
            params["market"] = market

        return self.request(
            "GET",
            Futures_HTTP.Position.GET_CURRENT_POSITION,
            params=params,
            public_url=False,
        )

        # <<< FUTURES << Position menu ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ end

    # <<< FUTURES Tab ---------------------------------------------------------------------------------------------------------- end
