from typing import Literal, Optional
import pandas as pd

class Order:
    """
    Represents a trading order (buy or sell) with execution tracking.

    Features:
    - Supports market, limit, and stop order types
    - Tracks fill status, average fill price, and execution fee
    - Can be linked to a Position for audit and reporting
    - Records fill time and reason (e.g., triggered by TP, SL, or manual)
    """

    def __init__(
        self,
        side: Literal["sell", "buy"],              # Order direction
        amount: float,                             # Order quantity
        price: float,                              # Order price (for limit/stop)
        timestamp: pd.Timestamp,                   # Time the order was created
        order_type: Literal["market", "limit", "stop"] = "market",  # Type of order
    ):
        self.side = side
        self.amount = amount
        self.price = price
        self.order_type = order_type
        self.timestamp = timestamp

        # Execution status
        self.status: Literal["new", "filled", "partially_filled", "canceled"] = "new"
        self.filled_quantity: float = 0.0
        self.avg_fill_price: Optional[float] = None
        self.fee: float = 0.0
        self.comment: str = ""

        # Position linkage and execution metadata
        self.fill_time: Optional[pd.Timestamp] = None     # Time the order was filled
        self.fill_reason: Optional[str] = None            # Reason for execution (e.g., "tp", "stop", "manual")
        self.position_id: Optional[str] = None            # Optional ID of the linked position

    def fill(
        self,
        quantity: float,
        fill_price: float,
        fee: float = 0.0,
        fill_time: Optional[pd.Timestamp] = None,
        reason: Optional[str] = None
    ):
        """
        Record a fill (partial or full) for this order.

        Parameters:
        - quantity: amount filled in this execution
        - fill_price: price at which the fill occurred
        - fee: execution fee
        - fill_time: timestamp of the fill
        - reason: optional reason for execution (e.g., "tp", "stop", "manual")
        """
        if quantity <= 0:
            return

        prev_qty = self.filled_quantity
        new_qty = prev_qty + quantity

        # Update weighted average fill price
        if self.avg_fill_price is None:
            self.avg_fill_price = fill_price
        else:
            total_value = (self.avg_fill_price * prev_qty) + (fill_price * quantity)
            self.avg_fill_price = total_value / new_qty

        self.filled_quantity = new_qty
        self.fee += fee
        self.fill_time = fill_time
        self.fill_reason = reason

        # Update order status
        if self.filled_quantity >= self.amount:
            self.status = "filled"
        else:
            self.status = "partially_filled"

    def cancel(self, reason: str = ""):
        """
        Cancel the order and optionally record a comment.
        """
        self.status = "canceled"
        self.comment = reason

    def link_to_position(self, position_id: str):
        """
        Link this order to a specific position (for tracking and reporting).
        """
        self.position_id = position_id

    def to_dict(self) -> dict:
        """
        Convert the order to a dictionary for logging or export.
        """
        return {
            "side": self.side,
            "amount": self.amount,
            "price": self.price,
            "order_type": self.order_type,
            "timestamp": self.timestamp,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "avg_fill_price": self.avg_fill_price,
            "fee": self.fee,
            "fill_time": self.fill_time,
            "fill_reason": self.fill_reason,
            "position_id": self.position_id,
            "comment": self.comment,
        }
    
    def __repr__(self):
        return f"< Order {self.side} {self.order_type} @ {self.price} : {self.timestamp.strftime("%Y-%M-%d %H:%M")} status : {self.status} >"
