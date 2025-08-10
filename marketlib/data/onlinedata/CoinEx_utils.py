from typing import Type, List


# ——— Enum Definitions ———========================================================================================================================


class MarketType:
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class MarketStatus:
    BIDDING = "bidding"
    COUNTING_DOWN = "counting_down"
    ONLINE = "available"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class OrderSide:
    BUY = "buy"
    SELL = "sell"

    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class OrderType:
    LIMIT = "limit"
    MARKET = "market"
    MAKER_ONLY = "maker_only"
    IOC = "ioc"
    FOK = "fok"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class STPMode:
    CT = "ct" #cancel the remaining Taker orders immediately
    CM = "cm" #cancel remaining maker orders
    BOTH = "both" #cancel both taker and maker orders
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class OrderEvent:
    PUT = "put"
    UPDATE = "update"
    MODIFY = "modify"
    FINISH = "finish"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class StopOrderEvent:
    PUT = "put"
    ACTIVE = "active"
    CANCEL = "cancel"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class StopOrderStatus:
    PUT = "put"
    ACTIVE_SUCCESS = "active_success"
    ACTIVE_FAIL = "active_fail"
    CANCEL = "cancel"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class TriggerDirection:
    HIGHER = "higher"
    LOWER = "lower"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class PositionEvent:
    UPDATE = "update"
    CLOSE = "close"
    SYS_CLOSE = "sys_close"
    ADL = "adl"
    LIQ = "liq"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class Permissions:
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"
    AMM = "AMM"
    API = "API"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class TransferStatus:
    CREATED = "created"
    DEDUCTED = "deducted"
    FAILED = "failed"
    FINISHED = "finished"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class LoanStatus:
    LOAN = "loan"
    DEBT = "debt"
    LIQUIDATED = "liquidated"
    FINISH = "finish"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class DepositStatus:
    PROCESSING = "processing"
    CONFIRMING = "confirming"
    CANCELLED = "canceled"
    FINISHED = "finished"
    TOO_SMALL = "too_small"
    EXCEPTION = "exception"

    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class WithdrawStatus:
    CREATED = "created"
    AUDIT_REQUIRED = "aaudit_required"
    AUDITED = "audited"
    PROCESSING = "processing"
    CONFIRMING = "confirming"
    FINISHED = "finished"
    CANCELLED = "canceled"
    CANCELLATION_FAILED = "cancellation_failed"
    FAILED = "failed"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class OrderStatus:
    OPEN = "open"
    PART_FILLED = "part_filled"
    FILLED = "filled"
    PART_CANCELED = "part_canceled"
    CANCELED = "canceled"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class ContractType:
    LINEAR = "linear"
    INVERSE = "inverse"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class MarginMode:
    ISOLATED = "isolated"
    CROSS = "cross"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class TakeProfitType:
    LATEST_PRICE = "latest price"
    MARK_PRICE = "mark price"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class StopLossType:
    LATEST_PRICE = "latest_price"
    MARK_PRICE = "mark_price"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class PositionSide:
    LONG = "long"
    SHORT = "short"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class PositionFinishedType:
    LIQ = "liq"
    ADL = "adl"
    SYS = "sys"
    LIMIT = "limit"
    MARKET = "market"
    MARKET_CLOSE_ALL = "market_close_all"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class TriggerPriceType:
    LATEST_PRICE = "latest_price"
    MARK_PRICE = "mark_price"
    INDEX_PRICE = "index_price"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


class TranscationType:
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRADE = "trade"
    MAKER_CASH_BACK = "maker_cash_back"
    
    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals

class AMMType:
    INFINITE = "infinite"
    FINITE = "finite"

    def get_values(self)-> List[str]:
        vals = [v for k, v in self.__class__.__dict__.items()
                if not k.startswith("__") and isinstance(v, str)]
        return vals


# ——— Central Definitions Class ——=======================================================================================================================


class CoinEx_Definitions:
    """
    Central registry of all enumerations used in CoinEx API schema.
    """

    MarketType = MarketType()
    MarketStatus = MarketStatus()
    OrderSide = OrderSide()
    OrderType = OrderType()
    STPMode = STPMode()
    OrderEvent = OrderEvent()
    StopOrderEvent = StopOrderEvent()
    StopOrderStatus = StopOrderStatus()
    TriggerDirection = TriggerDirection()
    PositionEvent = PositionEvent()
    Permissions = Permissions()
    TransferStatus = TransferStatus()
    LoanStatus = LoanStatus()
    DepositStatus = DepositStatus()
    WithdrawStatus = WithdrawStatus()
    OrderStatus = OrderStatus()
    ContractType = ContractType()
    MarginMode = MarginMode()
    TakeProfitType = TakeProfitType()
    StopLossType = StopLossType()
    PositionSide = PositionSide()
    PositionFinishedType = PositionFinishedType()
    TriggerPriceType = TriggerPriceType()
    TranscationType = TranscationType()
    AMMType = AMMType()

    locales: List[str] = [
        "de-DE",
        "en-US",
        "es-AR",
        "es-ES",
        "es-MX",
        "fr-FR",
        "kk-KZ",
        "id-ID",
        "uk-UA",
        "ja-JP",
        "ru-RU",
        "th-TH",
        "pt-BR",
        "tr-TR",
        "vi-VN",
        "zh-TW",
        "ar-SA",
        "hi-IN",
        "fil-PH",
    ]


# ——— Enum Futures HTTP request ———============================================================================================================================
class Futures_Ticker:
    GET_MARKET_STATUS = "/futures/market"
    GET_MARKET_INFORMATION = "/futures/ticker"
    GET_MARKET_DEPTH = "/futures/depth"
    GET_MARKET_TRANSACTIONS = "/futures/deals"
    GET_MARKET_CANDLESTICK = "/futures/kline"
    GET_MARKET_FUNDING_RATE = "/futures/funding-rate"
    GET_MARKET_FUNDING_RATE_HISTORY = "/futures/funding-rate-history"
    GET_MARKET_PREMIUM_INDEX_HISTORY = "/futures/premium-index-history"
    GET_MARKET_POSITION_LEVEL = "/futures/position-level"
    GET_MARKET_LIQUIDATION_HISTORY = "/futures/liquidation-history"
    GET_MARKET_BASIS_RATE_HISTORY = "/futures/basis-history"
    GET_MARKET_INDEX = "/futures/index"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Future_Orders:
    PLACE_ORDER = "/futures/order"
    PLACE_STOP_ORDER = "/futures/stop-order"
    BATCH_PLACE_ORDERS = "/futures/batch-order"
    BATCH_PLACE_STOP_ORDERS = "/futures/batch-stop-order"
    ORDER_STATUS_QUERY = "/futures/order-status"
    BATCH_QUERY_ORDER_STATUS = "/futures/batch-order-status"
    GET_FILLED_ORDER = "/futures/finished-order"
    GET_UNFILLED_STOP_ORDER = "/futures/pending-stop-order"
    GET_FILLED_STOP_ORDER = "/futures/finished-stop-order"
    MODIFY_ORDER = "/futures/modify-order"
    MODIFY_STOP_ORDER = "/futures/modify-stop-order"
    CANCEL_ALL_ORDERS = "/futures/cancel-all-order"
    CANCEL_ORDER = "/futures/cancel-order"
    CANCEL_STOP_ORDER = "/futures/cancel-stop-order"
    BATCH_CANCEL_ORDERS = "/futures/cancel-batch-order"
    BATCH_CANCEL_STOP_ORDERS = "/futures/cancel-batch-stop-order"
    CANCEL_ORDER_BY_CLIENT_ID = "/futures/cancel-order-by-client-id"
    CANCEL_STOP_ORDER_BY_CLIENT_ID = "/futures/cancel-stop-order-by-client-id"
    GET_UNFILLED_ORDER = "/futures/pending-order"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Futures_Executions:
    GET_USER_TRANSACTION = "/futures/user-deals"
    GET_USER_ORDER_TRANSACTION = "/futures/order-deals"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Futures_Position:
    CLOSE_POSITION = "/futures/close-position"
    ADJUST_POSITION_MARGIN = "/futures/adjust-position-margin"
    ADJUST_POSITION_LEVERAGE = "/futures/adjust-position-leverage"
    GET_CURRENT_POSITION = "/futures/pending-position"
    GET_HISTORICAL_POSITION = "/futures/finished-position"
    SET_POSITION_STOP_LOSS = "/futures/set-position-stop-loss"
    SET_POSITION_TAKE_PROFIT = "/futures/set-position-take-profit"
    GET_POSITION_MARGIN_CHANGE_HISTORY = "/futures/position-margin-history"
    GET_POSITION_FUNDING_RATE_HISTORY = "/futures/position-funding-history"
    GET_POSITION_AUTO_DELEVERAGE_HISTORY = "/futures/position-adl-history"
    GET_POSITION_AUTO_SETTLEMENT_HISTORY = "/futures/position-settle-history"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


# ——— Central Futures HTTP request Class ———=======================================================================================================


class Futures_HTTP:
    Ticker = Futures_Ticker()
    Orders = Future_Orders()
    Position = Futures_Position()
    Executions = Futures_Executions()

    def __str__(self):
        parts = []
        for name, value in self.__class__.__dict__.items():
            if not name.startswith("__") and hasattr(value, "__str__"):
                parts.append(f"{name}:\n{value.__str__()}")
        return f"{self.__class__.__name__}\n\n" + "\n----------------\n".join(parts)


# ——— Enum Spot HTTP request ———============================================================================================================================


class Spot_Ticker:
    GET_MARKET_STATUS = "/spot/market"
    GET_MARKET_INFORMATION = "/spot/ticker"
    GET_MARKET_DEPTH = "/spot/depth"
    GET_MARKET_TRANSACTIONS = "/spot/deals"
    GET_MARKET_CANDLESTICK = "/spot/kline"
    GET_MARKET_INDEX = "/spot/index"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Spot_Orders:

    PLACE_ORDER = "/spot/order"
    PLACE_STOP_ORDER = "/spot/stop-order"
    BATCH_PLACE_ORDERS = "/spot/batch-stop-order"
    BATCH_PLACE_STOP_ORDERS = "/spot/batch-stop-order"
    QUERY_ORDER_STATUS = "/spot/order-status"
    BATCH_QUERY_ORDER_STATUS = "/spot/batch-order-status"
    GET_UNFILLED_ORDER = "/spot/pending-order"
    GET_FILLED_ORDER = "/spot/finished-order"
    GET_UNFILLED_STOP_ORDER = "/spot/pending-stop-order"
    GET_FILLED_STOP_ORDER = "/spot/finished-stop-order"
    MODIFY_ORDER = "/spot/modify-order"
    MODIFY_STOP_ORDER = "/spot/modify-stop-order"
    CANCEL_ALL_ORDERS = "/spot/cancel-all-order"
    CANCEL_ORDER = "/spot/cancel-order"
    CANCEL_STOP_ORDER = "/spot/cancel-stop-order"
    BATCH_CANCEL_ORDERS = "/spot/cancel-batch-order"
    BATCH_CANCEL_STOP_ORDERS = "/spot/cancel-batch-stop-order"
    CANCEL_ORDER_BY_CLIENT_ID = "/spot/cancel-order-by-client-id"
    CANCEL_STOP_ORDER_BY_CLIENT_ID = "/spot/cancel-stop-order-by-client-id"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Spot_Executions:

    GET_USER_TRANSACTION = "/spot/user-deals"
    GET_USER_ORDER_TRANSACTION = "/spot/order-deals"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


# ——— Central Spot HTTP request Class ———=======================================================================================================


class Spot_HTTP:
    Ticker = Spot_Ticker()
    Orders = Spot_Orders()
    Executions = Spot_Executions()

    def __str__(self):
        parts = []
        for name, value in self.__class__.__dict__.items():
            if not name.startswith("__") and hasattr(value, "__str__"):
                parts.append(f"{name}:\n{value.__str__()}")
        return f"{self.__class__.__name__}\n\n" + "\n----------------\n".join(parts)


# ——— Enum Asset HTTP request ———============================================================================================================================


class Asset_Balance:

    GET_BALANCE_IN_SPOT_ACCOUNT = "/assets/spot/balance"
    GET_BALANCE_IN_FUTURES_ACCOUNT = "/assets/futures/balance"
    GET_BALANCE_IN_MARGIN_ACCOUNT = "/assets/margin/balance"
    GET_BALANCE_IN_FINANCIAL_ACCOUNT = "/assets/financial/balance"
    GET_AMM_ACCOUNT_LIQUIDITY = "/assets/amm/liquidity"
    GET_INFO_IN_CREDIT_ACCOUNT = "/assets/credit/info"
    GET_BALANCE_IN_CREDIT_ACCOUNT = "/assets/credit/balance"
    GET_SPOT_TRANSACTION_HISTORY = "/assets/spot/transcation-history"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Asset_Loan_And_Repayment:
    
    MARGIN_LOAN = "/assets/margin/borrow"
    MARGIN_REPAYMENT = "/assets/margin/repay"
    GET_BORROWING_RECORD_IN_MARGIN_ACCOUNT = "/assets/margin/borrow-history"
    GET_BORROWING_LIMIT = "/assets/margin/interest-limit"

    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())
    
    
class Asset_Deposit_And_Withdrawal():
    GET_DEPOSIT_ADDRESS="/assets/deposit-address"
    UPDATE_DEPOSIT_ADDRESS="/assets/renewal-deposit-address"
    GET_DEPOSIT_RECORD="/assets/deposit-history"
    SUBMIT_WITHDRAWAL_REQUEST="/assets/withdraw"
    CANCEL_WITHDRAWAL_REQUEST="/assets/cancel-withdraw"
    GET_WITHDRAWAL_RECORD="/assets/withdraw"
    GET_DEPOSIT_AND_WITHDRAWAL_CONFIGURATION="/assets/deposit-withdraw-config"
    GET_ALL_DEPOSIT_AND_WITHDRAWAL_CONFIGURATION="/assets/all-deposit-withdraw-config"
    GET_COIN_INFO="/assets/info"


    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())


class Asset_Transfer():
    TRANSFER="/assets/transfer"
    GET_ASSET_TRANSFER_RECORD="/assets/transfer-history"
    
    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())
    
    
class Asset_AMM():
    ADD_AMM_ACCOUNT_LIQUIDITY="/assets/amm/add-liquidity"
    REDUCE_AMM_ACCOUNT_LIQUIDITY="/assets/amm/remove-liquidity"
    GET_AMM_LIQUIDITY_POOL="/assets/amm/liquidity-pool"
    GET_AMM_INCOME_HISTORY="/assets/amm/income-history"
    
    def __str__(self):
        attrs = {
            k: v
            for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        }
        return "\n".join(f"{k}: {v}" for k, v in attrs.items())
    
    
# ——— Central Asset HTTP request Class ———=======================================================================================================

class Asset_HTTP():
    Balance = Asset_Balance()
    Loan_and_Repayment = Asset_Loan_And_Repayment()
    Deposit_and_Withdrawal = Asset_Deposit_And_Withdrawal()
    Transfer = Asset_Transfer()
    AMM = Asset_AMM()
    
    
    def __str__(self):
        parts = []
        for name, value in self.__class__.__dict__.items():
            if not name.startswith("__") and hasattr(value, "__str__"):
                parts.append(f"{name}:\n{value.__str__()}")
        return f"{self.__class__.__name__}\n\n" + "\n----------------\n".join(parts)