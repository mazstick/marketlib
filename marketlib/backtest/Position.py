from typing import Optional, Literal, Dict, List, Tuple
from dataclasses import dataclass, field
import pandas as pd
from .Order import Order 
import random


@dataclass
class TargetPlan:
    """
    Optional multi-target plan for partial exits.
    - price: target price to exit at
    - ratio: fraction of current size to exit when target is hit (0..1)
    - label: optional tag for the target (e.g., 'T1', 'T2')
    - filled: internal flag to avoid double-exiting the same target
    """
    price: float
    ratio: float
    label: str = ""
    filled: bool = False


class Position:
    """
    Represents a single open trading position (long or short) with:
    - Order linkage (all orders that created/modified/closed this position)
    - Scale-in/scale-out handling with VWAP entry price updates on adds
    - Per-bar unrealized PnL history (with timestamps) for later analysis
    - SL/TP management, ATR/homegrown trailing, and breakeven logic
    - Intrabar stop/target hit checks with priority
    - MFE/MAE tracked both in R and currency
    """

    def __init__(
        self,
        market:str,
        side: Literal["long", "short"],
        size: float,
        entry_price: float,
        entry_time: pd.Timestamp,
        entry_order_type: Literal["limit", "market"] = "market",
        stop: Optional[float] = None,
        tp: Optional[float] = None,
        contract_value: float = 1.0,
        fee_in: float = 0.0,
        risk_amount: Optional[float] = None,    # equity * risk_pct at entry (optional)
    ):
        # Core identity and economics
        self.market = market
        self.side = side
        self.dir = 1 if side == "long" else -1             # +1 long, -1 short
        self.size = float(size)                             # current size (positive)
        self.entry_price = float(entry_price)               # VWAP of active position
        self.entry_time = entry_time
        self.contract_value = float(contract_value)

        # Risk controls
        self.stop = stop                                    # SL price (optional)
        self.tp = tp                                        # TP price (optional)
        self.risk_amount = risk_amount                      # for R-based metrics (optional)

        # Extremes since entry (for trailing and excursion analytics)
        self.highest = entry_price
        self.lowest = entry_price

        # Costs and realized PnL
        self.fee_in = float(fee_in)                         # entry fee
        self.fee_out_cum = 0.0                              # cumulative exit fees
        self.realized_pnl = -self.fee_in                    # apply entry fee immediately

        # Lifecycle
        self.closed = False
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[pd.Timestamp] = None
        self.exit_reason: Optional[str] = None

        # Excursions
        self.mfe_R = 0.0
        self.mae_R = 0.0
        self.mfe_cur = 0.0                                  # in currency
        self.mae_cur = 0.0

        # Orders linked to this position (audit trail)
        self.orders: List[Order] = []
        init_order = Order(side="buy" if side == "long" else "sell",price=entry_price, amount=size, timestamp=entry_time, order_type=entry_order_type)
        init_order.fill(size, entry_price,fee_in, entry_time, reason="init position order")
        init_order.link_to_position(self.position_id_generator())
        self.orders.append(init_order)
        
        # Optional multi-target plan (filled progressively)
        self.targets: List[TargetPlan] = []

        # Full per-bar unrealized PnL history for later analysis
        # Each item: dict(time, close, unrealized, size, stop, tp, highest, lowest, mfe_R, mae_R)
        self.unrealized_pnl_history: List[Dict] = []

    # -------------- Properties --------------

    @property
    def is_open(self) -> bool:
        """True if position is active (not closed and size > 0)."""
        return (not self.closed) and self.size > 0.0

    @property
    def risk_per_unit(self) -> Optional[float]:
        """Absolute distance from entry to stop times contract value (None if no stop)."""
        if self.stop is None:
            return None
        return abs(self.entry_price - self.stop) * self.contract_value

    # -------------- Orders linkage --------------

    def add_order(self, order: Order) -> None:
        """Attach an Order object to this position (for audit/reporting)."""
        self.orders.append(order)

    def position_id_generator(self):
        return str(int((self.entry_price * self.entry_time.timestamp() * self.size) + 123456))

    def apply_fill(
        self,
        order: Order,
        quantity: float,
        fill_price: float,
        fee: float = 0.0,
        fill_time: Optional[pd.Timestamp] = None,
    ) -> None:
        """
        Apply a fill into this position via an Order:
        - If the order side increases exposure in the same direction → scale-in (VWAP update).
        - If the order side is opposite → reduce (partial close).
        Side mapping: long position → 'buy' adds, 'sell' reduces. Short is inverse.
        """
        self.add_order(order)
        # Call order.fill if available (your Order class has fill())
        if hasattr(order, "fill"):
            order.fill(quantity=quantity, fill_price=fill_price, fee=fee)

        # Determine effect on position
        adds_exposure = (self.side == "long" and getattr(order, "side", None) == "buy") or \
                        (self.side == "short" and getattr(order, "side", None) == "sell")

        if adds_exposure:
            self._scale_in(quantity, fill_price, fee)
        else:
            # Reduce exposure (partial exit) using the same mechanics as reduce()
            # Use fill_time if provided, otherwise entry_time as placeholder.
            self.reduce(
                exit_size=quantity,
                exit_price=fill_price,
                exit_time=fill_time or self.entry_time,
                fee_out=fee,
                reason="order_reduce",
            )

    def _scale_in(self, add_size: float, add_price: float, fee: float = 0.0) -> None:
        """
        Increase position size and recompute VWAP entry price:
            new_entry = (old_entry * old_size + add_price * add_size) / (old_size + add_size)
        Also accumulate fee into realized PnL (as cost).
        """
        if add_size <= 0:
            return
        old_notional = self.entry_price * self.size
        add_notional = add_price * add_size
        new_size = self.size + add_size
        if new_size <= 0:
            return
        self.entry_price = (old_notional + add_notional) / new_size
        self.size = new_size
        self.realized_pnl -= fee  # treat add fee as a realized cost

        # Update extremes to include the new reference if needed
        self.highest = max(self.highest, add_price)
        self.lowest = min(self.lowest, add_price)

    # -------------- Bar updates & analytics --------------

    def update_bar(self, ts: pd.Timestamp, high: float, low: float, close: float) -> None:
        """
        Update this position for a new bar:
        - Refresh highest/lowest since entry
        - Update MFE/MAE (both R and currency)
        - Append unrealized PnL snapshot (with timestamp) to history
        """
        if not self.is_open:
            return

        # Extremes
        self.highest = max(self.highest, high)
        self.lowest = min(self.lowest, low)

        # Excursions in currency
        favorable_cur = (high - self.entry_price) * self.dir * self.size * self.contract_value
        adverse_cur = (low  - self.entry_price) * self.dir * self.size * self.contract_value
        self.mfe_cur = max(self.mfe_cur, favorable_cur)
        self.mae_cur = min(self.mae_cur, adverse_cur)

        # Excursions in R
        if self.stop is not None:
            denom = max(1e-12, abs(self.entry_price - self.stop))
            self.mfe_R = max(self.mfe_R, (high - self.entry_price) * self.dir / denom)
            self.mae_R = min(self.mae_R, (low  - self.entry_price) * self.dir / denom)

        # Floating PnL at the bar's close
        unreal = self.unrealized_pnl(close)

        # Append full snapshot for analysis
        self.unrealized_pnl_history.append({
            "time": ts,
            "close": close,
            "unrealized": unreal,
            "size": self.size,
            "stop": self.stop,
            "tp": self.tp,
            "highest": self.highest,
            "lowest": self.lowest,
            "mfe_R": self.mfe_R,
            "mae_R": self.mae_R,
            "mfe_cur": self.mfe_cur,
            "mae_cur": self.mae_cur,
        })

    def unrealized_pnl(self, mark_price: float) -> float:
        """Compute current floating PnL in currency (positive long up, short down)."""
        return (mark_price - self.entry_price) * self.dir * self.size * self.contract_value

    def unrealized_frame(self) -> pd.DataFrame:
        """Return unrealized PnL history as a DataFrame indexed by time."""
        if not self.unrealized_pnl_history:
            return pd.DataFrame(columns=["unrealized"])
        df = pd.DataFrame(self.unrealized_pnl_history)
        return df.set_index("time").sort_index()

    # -------------- Stops, TPs, trailing, breakeven --------------

    def set_stop(self, stop: Optional[float]) -> None:
        """
        Set/clear stop. Caller should ensure logical placement:
        - Long: stop < current/entry
        - Short: stop > current/entry
        """
        self.stop = stop

    def set_tp(self, tp: Optional[float]) -> None:
        """Set/clear take profit."""
        self.tp = tp

    def move_stop_to_breakeven(self) -> None:
        """Move SL to entry price (breakeven)."""
        if self.is_open:
            self.stop = self.entry_price

    def move_stop_to_breakeven_on_mfe_R(self, threshold_R: float = 1.0) -> None:
        """Auto-breakeven if MFE in R reached threshold."""
        if self.is_open and self.mfe_R >= threshold_R:
            self.move_stop_to_breakeven()

    def trail_by_atr(self, atr: float, mult: float) -> None:
        """ATR-based trailing stop (tightens only)."""
        if not self.is_open:
            return
        if self.side == "long":
            new_stop = self.highest - mult * atr
            self.stop = max(self.stop if self.stop is not None else new_stop, new_stop)
        else:
            new_stop = self.lowest + mult * atr
            self.stop = min(self.stop if self.stop is not None else new_stop, new_stop)

    def trail_by_extremes(self, offset: float) -> None:
        """
        Trail using highest/lowest extremes with a fixed offset:
        - Long: stop = max(old_stop, highest - offset)
        - Short: stop = min(old_stop, lowest + offset)
        """
        if not self.is_open:
            return
        if self.side == "long":
            new_stop = self.highest - offset
            self.stop = max(self.stop if self.stop is not None else new_stop, new_stop)
        else:
            new_stop = self.lowest + offset
            self.stop = min(self.stop if self.stop is not None else new_stop, new_stop)

    # -------------- Intrabar trigger checks --------------

    def check_stop_tp(
        self,
        high: float,
        low: float,
        priority: Literal["stop-first", "tp-first"] = "stop-first",
    ) -> Optional[Dict]:
        """
        Check whether SL or TP is hit inside current bar range.
        If both hit, resolve via priority. Returns {'price', 'reason'} or None.
        """
        if not self.is_open:
            return None

        hit_tp = hit_sl = False
        if self.side == "long":
            hit_tp = self.tp   is not None and high >= self.tp
            hit_sl = self.stop is not None and low  <= self.stop
        else:
            hit_tp = self.tp   is not None and low  <= self.tp
            hit_sl = self.stop is not None and high >= self.stop

        if hit_tp and hit_sl:
            if priority == "stop-first":
                return {"price": self.stop, "reason": "stop"}
            else:
                return {"price": self.tp, "reason": "tp"}
        if hit_tp:
            return {"price": self.tp, "reason": "tp"}
        if hit_sl:
            return {"price": self.stop, "reason": "stop"}
        return None

    # -------------- Multi-target plan (optional) --------------

    def set_targets(self, targets: List[Tuple[float, float, str]]) -> None:
        """
        Define a multi-target plan as a list of (price, ratio, label).
        ratio ∈ (0,1]; targets are filled once when price hits them.
        """
        self.targets = [TargetPlan(price=p, ratio=r, label=(lab or "")) for (p, r, lab) in targets]

    def check_targets(
        self,
        high: float,
        low: float,
    ) -> List[TargetPlan]:
        """
        Return a list of unfilled TargetPlan entries that are hit this bar.
        Does not mutate size; caller should execute partial exits accordingly.
        """
        if not self.is_open or not self.targets:
            return []

        hits = []
        for t in self.targets:
            if t.filled:
                continue
            if self.side == "long":
                hit = high >= t.price
            else:
                hit = low  <= t.price
            if hit:
                hits.append(t)
        return hits

    def mark_target_filled(self, t: TargetPlan) -> None:
        """Mark a target as filled after executing its partial exit."""
        t.filled = True

    # -------------- Exit mechanics --------------

    def reduce(
        self,
        exit_size: float,
        exit_price: float,
        exit_time: pd.Timestamp,
        fee_out: float = 0.0,
        reason: str = "partial",
    ) -> Dict:
        """
        Partially close the position; returns a trade record dict.
        Adjusts size, realized PnL, and fee tracking.
        """
        if not self.is_open or exit_size <= 0:
            return {}

        exec_size = min(exit_size, self.size)
        gross = (exit_price - self.entry_price) * self.dir * exec_size * self.contract_value
        pnl_net = gross - fee_out
        self.realized_pnl += pnl_net
        self.fee_out_cum += fee_out

        self.size -= exec_size

        trade = {
            "side": self.side,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "exit_time": exit_time,
            "exit_price": exit_price,
            "size": exec_size,
            "fee_in": self.fee_in,         # full entry fee attached for context
            "fee_out": fee_out,
            "pnl_net": pnl_net,
            "reason": reason,
            "mfe_R": self.mfe_R,
            "mae_R": self.mae_R,
            "mfe_cur": self.mfe_cur,
            "mae_cur": self.mae_cur,
        }

        if self.size <= 0:
            self.closed = True
            self.exit_price = exit_price
            self.exit_time = exit_time
            self.exit_reason = reason

        return trade

    def close(
        self,
        exit_price: float,
        exit_time: pd.Timestamp,
        fee_out: float = 0.0,
        reason: str = "close",
    ) -> Dict:
        """Close the entire remaining position (full exit)."""
        if not self.is_open:
            return {}
        return self.reduce(self.size, exit_price, exit_time, fee_out, reason)

    # -------------- Export --------------

    def to_dict(self) -> Dict:
        """Serialize core state for logs/reports."""
        return {
            "market":self.market,
            "side": self.side,
            "dir": self.dir,
            "size": self.size,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "stop": self.stop,
            "tp": self.tp,
            "highest": self.highest,
            "lowest": self.lowest,
            "fee_in": self.fee_in,
            "fee_out_cum": self.fee_out_cum,
            "realized_pnl": self.realized_pnl,
            "closed": self.closed,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time,
            "exit_reason": self.exit_reason,
            "mfe_R": self.mfe_R,
            "mae_R": self.mae_R,
            "mfe_cur": self.mfe_cur,
            "mae_cur": self.mae_cur,
            "risk_per_unit": self.risk_per_unit,
            "risk_amount": self.risk_amount,
            "targets": [t.__dict__ for t in self.targets],
            "orders": [getattr(o, "__dict__", str(o)) for o in self.orders],
        }
        
        
    def __repr__(self):
        return f"< Position {self.side} on {self.market} @ {self.entry_time.strftime("%Y-%M-%d %H:%M")} >"
