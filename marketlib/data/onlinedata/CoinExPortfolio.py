from .CoinEx import CoinEx
from typing import Optional, List, Union, Literal
import pandas as pd
from tqdm import tqdm
import time
import warnings


class CoinexPortfolio:

    def __init__(
        self, access_id: Optional[str] = None, secret_key: Optional[str] = None
    ):
        """
        Initialize the client with access credentials.

        Args:
            access_id str: Your CoinEx API access ID.
            secret_key str: Your CoinEx API secret key.
        """

        self._isfetch = False
        self.access_id = access_id
        self.secret_key = secret_key
        if access_id and secret_key:
            self.coinex = CoinEx(access_id=access_id, secret_key=secret_key)
        else:
            self.coinex = CoinEx()
        self.futures_finished_positions: List[Position] = []
        self.market_status: List[MarketStatus] = []
        self._fetch_market_status()

    def get_market_status(self, market_name: str):
        for market in self.market_status:
            if market.market == market_name:
                return market

        raise ValueError(f"market name: {market_name} is not exist.")

    def _fetch_market_status(self):
        market_status_dataframe = pd.DataFrame(
            self.coinex.get_futures_market_status()["data"]
        )
        for i, row in market_status_dataframe.iterrows():
            self.market_status.append(MarketStatus(**row.to_dict()))

    def reload_market_status(self):
        self._fetch_market_status()

    def save(self, path: str):
        if self._isfetch:
            self.positions_dataframe().to_json(path)
        else:
            raise ValueError(
                "First you have to fetch data. to use this function first call load() or fetch()."
            )

    def load(self, path: str):
        df = pd.read_json(path)
        self.futures_finished_positions = self._fetch_from_dataframe(df)
        self._isfetch = True

    def fetch(self):
        if self.secret_key or self.access_id:
            raise ValueError(
                "you must give access id and secret key in constractor arguments."
            )

        self._fetch_account_data()
        self._isfetch = True

    def get_position_by_position_id(self, position_id):
        position_id = int(position_id)
        for pos in self.futures_finished_positions:
            if pos.position_id == position_id:
                return pos

        raise ValueError(f"position with position_id = {position_id} not in list.")

    def positions_dataframe(self):
        df = pd.DataFrame()
        for p in self.futures_finished_positions:
            df = pd.concat([df, p.dataframe()])

        df.reset_index(drop=True, inplace=True)

        return df

    def get_all_positions(self):
        return self.futures_finished_positions

    def _fetch_from_dataframe(self, df: pd.DataFrame) -> List["Position"]:
        positions = []
        for i, pos in df.iterrows():
            positions.append(Position(pos.to_dict()))

        return positions

    def _fetch_account_data(self):
        with tqdm(
            total=100,
            desc="📊 Fetching account data",
            dynamic_ncols=True,
            leave=True,
            bar_format="{l_bar}{bar}| {n:.2f}/{total} [elapsed: {elapsed}]",
            smoothing=0.01,
        ) as pbar:
            pbar.write("Getting user positions....")
            self._positions_dataframe = self._get_account_all_positions()
            pbar.update(25)
            pbar.write("Getting user transactions....")
            self._transactions_dataframe = self._get_account_all_transactions()
            pbar.update(25)
            pbar.write("Getting user positions funding rates....")
            self._funding_rate_dataframe = self._get_account_funding_rate()
            pbar.update(25)
            step = 40 / len(self._positions_dataframe)
            pbar.write("Matching positions....")
            market_status = pd.DataFrame(
                self.coinex.get_futures_market_status()["data"]
            )
            for i, pos in self._positions_dataframe.iterrows():
                market_status.loc[market_status["market"] == pos["market"]]
                p = Position(pos.to_dict())
                transactions = self._transactions_dataframe.loc[
                    self._transactions_dataframe["position_id"] == p.position_id
                ]

                funds = self._funding_rate_dataframe.loc[
                    self._funding_rate_dataframe["position_id"] == p.position_id
                ]

                for i, tx in transactions.iterrows():
                    p.add_transaction(Transaction(**tx.to_dict()))
                for i, fr in funds.iterrows():
                    p.add_funding_rate(Funding_Rate(**fr.to_dict()))

                self.futures_finished_positions.append(p)
                time.sleep(0.01)
                pbar.update(min(step, 100 - pbar.n))

        print(
            f"The number of positions : {len(self._positions_dataframe)}\nThe number of transactions : {len(self._transactions_dataframe)}\nThe number of funding rates : {len(self._funding_rate_dataframe)}"
        )

    def _get_account_funding_rate(self):
        limit = 1000
        page = 1
        response = self.coinex.get_futures_positions_funding_rate_history(limit=limit)
        funds = pd.DataFrame(response["data"])
        while response["pagination"]["has_next"]:
            page += 1
            response = self.coinex.get_futures_positions_funding_rate_history(
                limit=limit, page=page
            )
            funds = pd.concat([funds, pd.DataFrame(response["data"])])

        return funds

    def _get_account_all_positions(self):
        limit = 1000
        page = 1
        response = self.coinex.get_futures_historical_position(limit=limit)
        positions = pd.DataFrame(response["data"])
        while response["pagination"]["has_next"]:
            page += 1
            response = self.coinex.get_futures_historical_position(
                limit=limit, page=page
            )
            positions = pd.concat([positions, pd.DataFrame(response["data"])])

        return positions

    def _get_account_all_transactions(self):
        markets = self._positions_dataframe["market"].unique()
        limit = 1000
        page = 1

        transactions = pd.DataFrame()
        for market in markets:
            response = self.coinex.get_futures_user_transactions(
                market=market, limit=limit
            )
            transactions = pd.concat([transactions, pd.DataFrame(response["data"])])
            while response["pagination"]["has_next"]:
                page += 1
                response = self.coinex.get_futures_user_transactions(
                    market=market, limit=limit, page=page
                )
                transactions = pd.concat([transactions, pd.DataFrame(response["data"])])

            page = 0

        return transactions


# Position class =====================================================================================================================================================================


class Position:
    """
    Represents a finished futures position from CoinEx.

    Attributes are parsed from the API response and support structured access,
    conversion to pandas objects, and serialization.
    """

    def __init__(self, data: dict):
        # Core identifiers
        self.position_id: int = int(data["position_id"])
        self.market: str = data["market"].strip()
        self.market_type: str = data["market_type"]
        self.side: str = data["side"]
        self.margin_mode: str = data["margin_mode"]
        self.finished_type: str = data["finished_type"]

        # Position metrics
        self.open_interest: float = float(data["open_interest"])
        self.close_avbl: float = float(data["close_avbl"])
        self.ath_position_amount: float = float(data["ath_position_amount"])
        self.unrealized_pnl: float = float(data["unrealized_pnl"])
        self.realized_pnl: float = float(data["realized_pnl"])
        self.avg_entry_price: float = float(data["avg_entry_price"])
        self.cml_position_value: float = float(data["cml_position_value"])
        self.max_position_value: float = float(data["max_position_value"])

        # TP/SL
        self.take_profit_price: str = data["take_profit_price"]
        self.stop_loss_price: str = data["stop_loss_price"]
        self.take_profit_type: str = data["take_profit_type"]
        self.stop_loss_type: str = data["stop_loss_type"]

        # Margin & leverage
        self.leverage: int = int(data["leverage"])
        self.margin_avbl: float = float(data["margin_avbl"])
        self.ath_margin_size: float = float(data["ath_margin_size"])
        self.position_margin_rate: float = float(data["position_margin_rate"])
        self.maintenance_margin_rate: float = float(data["maintenance_margin_rate"])
        self.maintenance_margin_value: float = float(data["maintenance_margin_value"])

        # Risk & settlement
        self.liq_price: float = float(data["liq_price"])
        self.bkr_price: float = float(data["bkr_price"])
        self.adl_level: int = int(data["adl_level"])
        self.settle_price: float = float(data["settle_price"])
        self.settle_value: float = float(data["settle_value"])

        # Timestamps
        self.created_at: pd.Timestamp = pd.to_datetime(data["created_at"], unit="ms")
        self.updated_at: pd.Timestamp = pd.to_datetime(data["updated_at"], unit="ms")

        # Tranactions
        self.transactions: List[Transaction] = []
        if "transactions" in data.keys():
            for tx in data["transactions"]:
                self.transactions.append(Transaction(**tx))

        # Funding Rates
        self.funding_rate: List[Funding_Rate] = []
        if "funding_rate" in data.keys():
            for fr in data["funding_rate"]:
                self.funding_rate.append(Funding_Rate(**fr))

        # Internal caches
        self._series_cache = None
        self._dataframe_cache = None
        self._realized_pnl_cache = None

    def add_funding_rate(self, fr: "Funding_Rate"):
        if fr.position_id != self.position_id:
            raise ValueError(
                f"Funding rate position_id {fr.position_id} does not match Position {self.position_id}"
            )
        self.funding_rate.append(fr)

    def series(self) -> pd.Series:
        """
        Return position data as a pandas Series.
        """
        if self._series_cache is None:
            public_attrs = {
                k: v for k, v in vars(self).items() if not k.startswith("_")
            }
            self._series_cache = pd.Series(public_attrs)
        return self._series_cache

    def add_transaction(self, tx: "Transaction"):
        """
        Add a transaction to this position.
        """
        if tx.position_id != self.position_id:
            raise ValueError(
                f"Transaction position_id {tx.position_id} does not match Position {self.position_id}"
            )
        self.transactions.append(tx)

    def sort_transactions_by_time(self, reverse: bool = False):
        """
        Sort transactions in-place by their creation time.
        """
        self.transactions.sort(key=lambda tx: tx.created_at, reverse=reverse)

    def transactions_as_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([t.series() for t in self.transactions])

    def total_fee(self) -> float:
        """
        Total fee paid across all transactions.
        """
        return sum(tx.fee for tx in self.transactions)
    
    def total_funding_rate(self) -> float:
        """
        Total funding rate paid.
        """
        return sum([fr.funding_value for fr in self.funding_rate]) if len(self.funding_rate) != 0 else 0.0

    def total_amount(self) -> float:
        """
        Total traded amount across all transactions.
        """
        return sum(tx.amount for tx in self.transactions)/2.0

    def realized_pnl_change(self):

        self.sort_transactions_by_time()
        pnl = self.transactions_as_dataframe()
        pnl.set_index("deal_id", inplace=True)

        pnl["realized_type"] = "fee"

        avg_entry_price = 0.0
        sum_amount = 0.0

        if self.side == "long":
            for tx in self.transactions:
                pnl.loc[tx.deal_id, "realized_pnl_change"] = tx.fee * -1
                if tx.side == "buy":
                    avg_entry_price = (
                        (avg_entry_price * sum_amount) + (tx.amount * tx.price)
                    ) / (sum_amount + tx.amount)
                    sum_amount += tx.amount
                elif tx.side == "sell":
                    pnl.loc[tx.deal_id, "realized_pnl_change"] += (
                        tx.price - avg_entry_price
                    ) * tx.amount
                    pnl.loc[tx.deal_id, "realized_type"] = "order"
                    sum_amount -= tx.amount
        elif self.side == "short":
            for tx in self.transactions:
                pnl.loc[tx.deal_id, "realized_pnl_change"] = tx.fee * -1
                if tx.side == "sell":
                    avg_entry_price = (
                        (avg_entry_price * sum_amount) + (tx.amount * tx.price)
                    ) / (sum_amount + tx.amount)
                    sum_amount += tx.amount
                elif tx.side == "buy":
                    pnl.loc[tx.deal_id, "realized_pnl_change"] += (
                        avg_entry_price - tx.price
                    ) * tx.amount
                    pnl.loc[tx.deal_id, "realized_type"] = "order"
                    sum_amount -= tx.amount

        # print(f"avg_entry_price = {avg_entry_price}, real = {self.avg_entry_price} --- sum realized change = {sum(pnl.values())} , real {self.realized_pnl}")

        pnl.reset_index(inplace=True)
        pnl = pnl[["created_at", "realized_pnl_change", "realized_type","side"]]

        if len(self.funding_rate) != 0:
            for fr in self.funding_rate:
                pnl = pd.concat(
                    [
                        pnl,
                        pd.Series(
                            {
                                "created_at": fr.created_at,
                                "realized_pnl_change": fr.funding_value,
                                "realized_type": "funding_rate",
                                "side": "funding"
                            }
                        )
                        .to_frame()
                        .T,
                    ]
                )

            pnl.sort_values("created_at", inplace=True)
            pnl.reset_index(drop=True, inplace=True)

        self._realized_pnl_cache = pnl

        accuracy = 100 * (
            1
            - (
                abs(pnl["realized_pnl_change"].sum() - self.realized_pnl)
                / abs(self.realized_pnl)
            )
        )

        if accuracy < 99.0:
            warnings.warn(
                f"Accuracy below 99% for position_id = #{self.position_id}. This result is considered invalid. Accuracy = {accuracy:.4f} %"
            )

        return pnl

    def average_price(self) -> float:
        """
        Weighted average price across all transactions.
        """
        total_value = sum(tx.price * tx.amount for tx in self.transactions)
        total_amount = self.total_amount()
        return total_value / total_amount if total_amount else 0.0

    def dataframe(self) -> pd.DataFrame:
        """
        Return position data as a single-row pandas DataFrame.
        """
        if self._dataframe_cache is None:
            self._dataframe_cache = pd.DataFrame([self.series()])
        return self._dataframe_cache

    def to_dict(self) -> dict:
        """
        Convert position to dictionary.
        """
        return self.series().to_dict()

    def to_json(self) -> str:
        """
        Convert position to JSON string.
        """
        return self.series().to_json(date_format="iso")

    def __eq__(self, other) -> bool:
        """
        Equality based on position_id.
        """
        return isinstance(other, Position) and self.position_id == other.position_id

    def __hash__(self) -> int:
        """
        Hash based on position_id.
        """
        return hash(self.position_id)

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """
        return (
            f"<Position #{self.position_id} {self.side.upper()} {self.open_interest} "
            f"@ {self.avg_entry_price} | PnL: {self.realized_pnl:.2f} | Market: {self.market} | {len(self.transactions)} transactions>"
        )

    def __str__(self) -> str:
        """
        User-friendly summary.
        """
        return (
            f"Position {self.position_id}: {self.side.upper()} {self.open_interest} {self.market} "
            f"@ {self.avg_entry_price} | Realized PnL: {self.realized_pnl:.2f} | Leverage: {self.leverage}x | {len(self.transactions)} transactions"
        )


# Order class =====================================================================================================================================================================


class Order:

    def __init__(self):
        pass


# Transaction class =====================================================================================================================================================================


class Transaction:
    """
    Represents a single executed transaction in a futures market.

    Attributes
    ----------
    deal_id : int
        Unique transaction ID.
    created_at : pd.Timestamp
        Timestamp of execution.
    order_id : int
        Associated order ID.
    position_id : int
        Position ID linked to the transaction.
    market : str
        Market symbol (e.g., "BTCUSDT").
    side : str
        Direction of trade ("buy" or "sell").
    price : float
        Execution price.
    amount : float
        Executed volume.
    role : str
        Execution role ("maker" or "taker").
    fee : float
        Fee charged for the transaction.
    fee_ccy : str
        Currency in which the fee was charged.
    """

    def __init__(
        self,
        deal_id: int,
        created_at: int,
        order_id: int,
        position_id: str,
        market: str,
        side: str,
        price: str,
        amount: str,
        role: str,
        fee: str,
        fee_ccy: str,
    ):
        self.deal_id: int = deal_id
        self.created_at: pd.Timestamp = pd.to_datetime(created_at, unit="ms")
        self.order_id: int = order_id
        self.position_id: int = position_id
        self.market: str = market
        self.side: str = side
        self.price: float = float(price)
        self.amount: float = float(amount)
        self.role: str = role
        self.fee: float = float(fee)
        self.fee_ccy: str = fee_ccy

        self._series_cache = None
        self._dataframe_cache = None

    def series(self) -> pd.Series:
        """
        Return transaction data as a pandas Series.
        Cached after first computation.
        """
        if self._series_cache is None:
            self._series_cache = pd.Series(
                {
                    "deal_id": self.deal_id,
                    "created_at": self.created_at,
                    "order_id": self.order_id,
                    "position_id": self.position_id,
                    "market": self.market,
                    "side": self.side,
                    "price": self.price,
                    "amount": self.amount,
                    "role": self.role,
                    "fee": self.fee,
                    "fee_ccy": self.fee_ccy,
                }
            )
        return self._series_cache

    def dataframe(self) -> pd.DataFrame:
        """
        Return transaction data as a single-row pandas DataFrame.
        Cached after first computation.
        """
        if self._dataframe_cache is None:
            self._dataframe_cache = pd.DataFrame([self.series()])
        return self._dataframe_cache

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary.
        """
        return self.series().to_dict()

    def to_json(self) -> str:
        """
        Convert transaction to JSON string.
        """
        return self.series().to_json(date_format="iso")

    def __eq__(self, other) -> bool:
        """
        Equality based on deal_id.
        """
        return isinstance(other, Transaction) and self.deal_id == other.deal_id

    def __hash__(self) -> int:
        """
        Hash based on deal_id.
        """
        return hash(self.deal_id)

    def __repr__(self) -> str:
        """
        Human-readable representation for debugging.
        """
        return (
            f"<Transaction #{self.deal_id} "
            f"{self.side.upper()} {self.amount} @ {self.price} "
            f"on {self.market} | Role: {self.role}, Fee: {self.fee} {self.fee_ccy}>"
        )

    def __str__(self) -> str:
        """
        User-friendly string representation of the transaction.
        """
        return (
            f"Transaction with deal_id = {self.deal_id}: {self.side.upper()} {self.amount} {self.market} "
            f"@ {self.price} | Fee: {self.fee} {self.fee_ccy} | Role: {self.role}"
        )


# Funding rate class =====================================================================================================================================================================


class Funding_Rate:
    """
    Represents a single funding rate event for a futures position.

    Attributes
    ----------
    created_at : pd.Timestamp
        Timestamp of the funding event.
    margin_mode : str
        Margin mode ("cross" or "isolated").
    position_id : int
        Unique position ID.
    market : str
        Market symbol (e.g., "BTCUSDT").
    market_type : str
        Market type, typically "FUTURES".
    side : str
        Position side ("long" or "short").
    open_interest : float
        Position size at the time of funding.
    settle_price : float
        Settlement price used for funding calculation.
    funding_value : float
        Funding fee charged or received.
    funding_rate : float
        Funding rate applied.
    ccy : str
        Settlement currency (e.g., "USDT").
    """

    def __init__(
        self,
        created_at: int,
        margin_mode: str,
        position_id: int,
        market: str,
        market_type: str,
        side: str,
        open_interest: str,
        settle_price: str,
        funding_value: str,
        funding_rate: str,
        ccy: str,
    ):
        self.created_at: pd.Timestamp = pd.to_datetime(created_at, unit="ms")
        self.margin_mode: str = margin_mode
        self.position_id: int = position_id
        self.market: str = market
        self.market_type: str = market_type
        self.side: str = side
        self.open_interest: float = float(open_interest)
        self.settle_price: float = float(settle_price)
        self.funding_value: float = float(funding_value)
        self.funding_rate: float = float(funding_rate)
        self.ccy: str = ccy

        self._series_cache: Optional[pd.Series] = None
        self._dataframe_cache: Optional[pd.DataFrame] = None

    def series(self) -> pd.Series:
        """Return funding event as a pandas Series."""
        if self._series_cache is None:
            self._series_cache = pd.Series(
                {
                    "created_at": self.created_at,
                    "margin_mode": self.margin_mode,
                    "position_id": self.position_id,
                    "market": self.market,
                    "market_type": self.market_type,
                    "side": self.side,
                    "open_interest": self.open_interest,
                    "settle_price": self.settle_price,
                    "funding_value": self.funding_value,
                    "funding_rate": self.funding_rate,
                    "ccy": self.ccy,
                }
            )
        return self._series_cache

    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary.
        """
        return self.series().to_dict()

    def dataframe(self) -> pd.DataFrame:
        """Return funding event as a single-row pandas DataFrame."""
        if self._dataframe_cache is None:
            self._dataframe_cache = self.series().to_frame().T
        return self._dataframe_cache

    def __str__(self) -> str:
        """
        User-friendly string representation of the transaction.
        """
        return (
            f"[{self.market}] {self.side.upper()} | "
            f"Funding Rate: {self.funding_rate:.6f} | "
            f"Value: {self.funding_value:.4f} {self.ccy} | "
            f"Time: {self.created_at.isoformat()}"
        )

    def __repr__(self) -> str:
        """
        Human-readable representation for debugging.
        """
        return (
            f"[{self.market}] {self.side.upper()} | "
            f"Funding Rate: {self.funding_rate:.6f} | "
            f"Value: {self.funding_value:.4f} {self.ccy} | "
            f"Time: {self.created_at.isoformat()}"
        )


# Market Status class =====================================================================================================================================================================


class MarketStatus:
    """
    Represents the status and metadata of a futures market on CoinEx.

    Attributes
    ----------
    market : str
        Market symbol (e.g., "BTCUSDT").
    contract_type : str
        Contract type ("linear", "inverse", etc.).
    maker_fee_rate : float
        Maker fee rate.
    taker_fee_rate : float
        Taker fee rate.
    min_amount : float
        Minimum transaction volume.
    base_ccy : str
        Base currency (e.g., "BTC").
    quote_ccy : str
        Quote currency (e.g., "USDT").
    base_ccy_precision : int
        Decimal precision for base currency.
    quote_ccy_precision : int
        Decimal precision for quote currency.
    tick_size : float
        Minimum price increment.
    leverage : List[int]
        Supported leverage levels.
    open_interest_volume : float
        Total open interest volume.
    is_market_available : bool
        Whether the market is currently open.
    is_copy_trading_available : bool
        Whether copy trading is enabled.
    """

    def __init__(
        self,
        market: str,
        contract_type: str,
        maker_fee_rate: str,
        taker_fee_rate: str,
        min_amount: str,
        base_ccy: str,
        quote_ccy: str,
        base_ccy_precision: int,
        quote_ccy_precision: int,
        status: str,
        tick_size: str,
        leverage: List[str],
        open_interest_volume: str,
        is_market_available: bool,
        is_copy_trading_available: bool,
    ):
        self.market: str = market
        self.contract_type: str = contract_type
        self.maker_fee_rate: float = float(maker_fee_rate)
        self.taker_fee_rate: float = float(taker_fee_rate)
        self.min_amount: float = float(min_amount)
        self.base_ccy: str = base_ccy
        self.quote_ccy: str = quote_ccy
        self.base_ccy_precision: int = base_ccy_precision
        self.quote_ccy_precision: int = quote_ccy_precision
        self.tick_size: float = float(tick_size)
        self.leverage: List[int] = [int(lv) for lv in leverage]
        self.open_interest_volume: float = float(open_interest_volume)
        self.is_market_available: bool = is_market_available
        self.is_copy_trading_available: bool = is_copy_trading_available
        self.status: str = status

        self._series_cache: Optional[pd.Series] = None
        self._dataframe_cache: Optional[pd.DataFrame] = None

    def series(self) -> pd.Series:
        """Return market status as a pandas Series."""
        if self._series_cache is None:
            self._series_cache = pd.Series(
                {
                    "market": self.market,
                    "contract_type": self.contract_type,
                    "maker_fee_rate": self.maker_fee_rate,
                    "taker_fee_rate": self.taker_fee_rate,
                    "min_amount": self.min_amount,
                    "base_ccy": self.base_ccy,
                    "quote_ccy": self.quote_ccy,
                    "base_ccy_precision": self.base_ccy_precision,
                    "quote_ccy_precision": self.quote_ccy_precision,
                    "status": self.status,
                    "tick_size": self.tick_size,
                    "leverage": self.leverage,
                    "open_interest_volume": self.open_interest_volume,
                    "is_market_available": self.is_market_available,
                    "is_copy_trading_available": self.is_copy_trading_available,
                }
            )
        return self._series_cache

    def dataframe(self) -> pd.DataFrame:
        """Return market status as a single-row pandas DataFrame."""
        if self._dataframe_cache is None:
            self._dataframe_cache = pd.DataFrame([self.series()])
        return self._dataframe_cache

    def to_dict(self) -> dict:
        """Convert market status to dictionary."""
        return self.series().to_dict()

    def to_json(self) -> str:
        """Convert market status to JSON string."""
        return self.series().to_json()

    def __eq__(self, other) -> bool:
        """Equality based on market name."""
        return isinstance(other, MarketStatus) and self.market == other.market

    def __hash__(self) -> int:
        """Hash based on market name."""
        return hash(self.market)

    def __repr__(self) -> str:
        """Debug-friendly representation."""
        return (
            f"<MarketStatus {self.market} | Type: {self.contract_type} | "
            f"Fees: M={self.maker_fee_rate}, T={self.taker_fee_rate} | "
            f"Available: {self.is_market_available}>"
        )

    def __str__(self) -> str:
        """User-friendly string representation."""
        return (
            f"{self.market} ({self.contract_type}) | "
            f"Maker Fee: {self.maker_fee_rate:.4f}, Taker Fee: {self.taker_fee_rate:.4f} | "
            f"Leverage: {self.leverage} | Open Interest: {self.open_interest_volume} | "
            f"Available: {'✅' if self.is_market_available else '❌'}"
        )
