from .CoinExPortfolio import CoinexPortfolio, Position, Transaction
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os



class CoinexDashboard:

    def __init__(self, portfo: CoinexPortfolio):
        self.portfo = portfo

    def position_value_analyze(
        self,
        position: Position,
        without_leverage: bool = False,
        figsize=(15, 8),
        margin_scale: float = 0.1,
        volume_color: str = "blue",
        zero_line_color: str = "orange",
        buy_label: str = "buy order",
        sell_label: str = "sell order",
        buy_color: str = "g",
        sell_color: str = "r",
        date_format: str = "%b %d %H:%M:%S",
        save_path: str = None
    ):
        
        """
        Visualizes the cumulative value of a trading position over time, based on transaction prices and amounts.
        Optionally adjusts for leverage to show the raw capital exposure.

        Parameters:
            position (Position): The trading position to analyze.
            without_leverage (bool): If True, divides cumulative value by leverage to show unleveraged exposure.
            figsize (tuple): Size of the matplotlib figure (width, height). Default is (15, 8).
            margin_scale (float): Fraction of time margin added before/after the data range for padding. Default is 0.1.
            volume_color (str): Color used for the cumulative value step line. Default is "blue".
            zero_line_color (str): Color of the horizontal zero reference line. Default is "orange".
            buy_label (str): Label for buy orders in the legend.
            sell_label (str): Label for sell orders in the legend.
            buy_color (str): Color used for buy order markers. Default is "g".
            sell_color (str): Color used for sell order markers. Default is "r".
            date_format (str): Format string for x-axis datetime labels. Default is "%b %d %H:%M:%S".
            save_path (str): Path to save plot image (png format).

        Returns:
            pd.DataFrame: A DataFrame containing cumulative value over time, including synthetic 'init' and 'finish' points.

        Notes:
            - Buy and sell transactions are directionally adjusted based on position side (long/short).
            - Value is calculated as price × amount and accumulated over time.
            - If `without_leverage` is True, the value is normalized by the position's leverage.
            - Buy/sell events are shown as scatter points.
            - A horizontal line marks the final value before the synthetic 'finish' point.
            - The chart includes metadata such as realized PnL, total fee, volume, and max value.
            - Time padding is applied to ensure visual clarity at the edges.
        """
        
        
        position.sort_transactions_by_time()
        transactions = position.transactions.copy()
        market_status = self.portfo.get_market_status(position.market)
        sum_amount = pd.DataFrame()
        is_long: bool = position.side == "long"
        for tr in transactions:
            if tr.side == "buy":
                df = tr.dataframe()
                df = df[["created_at", "price", "amount", "side"]]
                df.loc[:, "amount"] = df["amount"].mul(1 if is_long else -1)
                sum_amount = pd.concat([sum_amount, df])
            if tr.side == "sell":
                df = tr.dataframe()
                df = df[["created_at", "price", "amount", "side"]]
                df.loc[:, "amount"] = df["amount"].mul(-1 if is_long else 1)
                sum_amount = pd.concat([sum_amount, df])

        sum_amount["value"] = sum_amount["amount"] * sum_amount["price"]
        sum_amount["value"] = sum_amount["value"].cumsum()

        if without_leverage:
            sum_amount["value"] = sum_amount["value"] / position.leverage

        transaction_df = position.transactions_as_dataframe()

        margin = (
            transaction_df.iloc[-1]["created_at"] - transaction_df.iloc[0]["created_at"]
        )

        init_point = pd.DataFrame(
            [
                {
                    "created_at": sum_amount.iloc[0]["created_at"]
                    - pd.Timedelta(margin * margin_scale, unit="s"),
                    "value": 0.0,
                    "side": "init",
                }
            ]
        )

        finish_point = pd.DataFrame(
            [
                {
                    "created_at": sum_amount.iloc[-1]["created_at"]
                    + pd.Timedelta(margin * margin_scale, unit="s"),
                    "value": sum_amount.iloc[-1]["value"],
                    "side": "finish",
                }
            ]
        )

        sum_amount = pd.concat(
            [sum_amount, init_point, finish_point], ignore_index=True
        )

        sum_amount.set_index("created_at", inplace=True)
        sum_amount.sort_index(inplace=True)

        fig, ax = plt.subplots(figsize=figsize)

        ax.step(
            sum_amount.index,
            sum_amount["value"],
            where="post",
            label="volume",
            color=volume_color,
        )

        ax.scatter(
            sum_amount.loc[sum_amount["side"] == "buy"].index,
            sum_amount.loc[sum_amount["side"] == "buy"]["value"],
            color=buy_color,
            label=buy_label,
            marker="o",
        )
        ax.scatter(
            sum_amount.loc[sum_amount["side"] == "sell"].index,
            sum_amount.loc[sum_amount["side"] == "sell"]["value"],
            color=sell_color,
            label=sell_label,
            marker="o",
        )

        ax.axhline(0.0, linestyle="--", color=zero_line_color, linewidth=0.7)

        ax.axhline(
            sum_amount.iloc[-2]["value"], linestyle="--", color="r", linewidth=0.7
        )

        ax.set_title(
            f"value analyze for position_id: {position.position_id}\nrealized pnl :{position.realized_pnl} {market_status.quote_ccy}\ntotal fee: {position.total_fee()} {transactions[0].fee_ccy}\ntotal volume: {position.ath_position_amount} {market_status.base_ccy}\nmax value: {position.max_position_value}\n{position.side.upper()} position on {position.market}\n{"**with out leverage plotted**" if without_leverage else ""}"
        )

        ax.set_ylabel(f"value({market_status.quote_ccy})")
        ax.set_xlabel(f"Time")
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        ax.legend()
        plt.xticks(rotation=45)

        plt.show()
        
        if save_path:
            filename = f"position_{position.position_id}_value_analysis.png"
            save_path = os.path.join(save_path, filename)
            fig.savefig(save_path, bbox_inches="tight", dpi=300)

        return sum_amount

    def position_volume_analyze(
        self,
        position: Position,
        figsize=(15, 8),
        margin_scale: float = 0.1,
        volume_color: str = "blue",
        zero_line_color: str = "orange",
        buy_label: str = "buy order",
        sell_label: str = "sell order",
        buy_color: str = "g",
        sell_color: str = "r",
        date_format: str = "%b %d %H:%M:%S",
        save_path: str = None
    ):
        
        """
        Visualizes the cumulative volume evolution of a trading position, distinguishing buy and sell events.

        Parameters:
            position (Position): The trading position to analyze.
            figsize (tuple): Size of the matplotlib figure (width, height). Default is (15, 8).
            margin_scale (float): Fraction of time margin added before/after the data range for padding. Default is 0.1.
            volume_color (str): Color used for the cumulative volume step line. Default is "blue".
            zero_line_color (str): Color of the horizontal zero reference line. Default is "orange".
            buy_label (str): Label for buy orders in the legend.
            sell_label (str): Label for sell orders in the legend.
            buy_color (str): Color used for buy order markers. Default is "g".
            sell_color (str): Color used for sell order markers. Default is "r".
            date_format (str): Format string for x-axis datetime labels. Default is "%b %d %H:%M:%S".
            save_path (str): Path to save plot image (png format).


        Returns:
            pd.DataFrame: A DataFrame containing cumulative volume over time, including synthetic 'init' and 'finish' points.

        Notes:
            - Buy and sell transactions are aggregated and directionally adjusted based on position side (long/short).
            - Cumulative volume is plotted as a step chart.
            - Buy/sell events are shown as scatter points.
            - Time padding is applied to ensure visual clarity at the edges.
            - The chart includes a zero reference line and is annotated with position metadata.
        """

        position.sort_transactions_by_time()
        transactions = position.transactions.copy()
        market_status = self.portfo.get_market_status(position.market)
        sum_amount = pd.DataFrame()
        is_long: bool = position.side == "long"
        for tr in transactions:
            if tr.side == "buy":
                df = tr.dataframe()
                df = df[["created_at", "amount", "side"]]
                df.loc[:, "amount"] = df["amount"].mul(1 if is_long else -1)
                sum_amount = pd.concat([sum_amount, df])
            if tr.side == "sell":
                df = tr.dataframe()
                df = df[["created_at", "amount", "side"]]
                df.loc[:, "amount"] = df["amount"].mul(-1 if is_long else 1)
                sum_amount = pd.concat([sum_amount, df])

        sum_amount["amount"] = sum_amount["amount"].cumsum()

        transaction_df = position.transactions_as_dataframe()

        margin = (
            transaction_df.iloc[-1]["created_at"] - transaction_df.iloc[0]["created_at"]
        )

        init_point = pd.DataFrame(
            [
                {
                    "created_at": sum_amount.iloc[0]["created_at"]
                    - pd.Timedelta(margin * margin_scale, unit="s"),
                    "amount": 0.0,
                    "side": "init",
                }
            ]
        )

        finish_point = pd.DataFrame(
            [
                {
                    "created_at": sum_amount.iloc[-1]["created_at"]
                    + pd.Timedelta(margin * margin_scale, unit="s"),
                    "amount": sum_amount.iloc[-1]["amount"],
                    "side": "finish",
                }
            ]
        )

        sum_amount = pd.concat(
            [sum_amount, init_point, finish_point], ignore_index=True
        )

        sum_amount.set_index("created_at", inplace=True)
        sum_amount.sort_index(inplace=True)

        fig, ax = plt.subplots(figsize=figsize)

        ax.step(
            sum_amount.index,
            sum_amount["amount"],
            where="post",
            label="volume",
            color=volume_color,
        )

        ax.scatter(
            sum_amount.loc[sum_amount["side"] == "buy"].index,
            sum_amount.loc[sum_amount["side"] == "buy"]["amount"],
            color=buy_color,
            label=buy_label,
            marker="o",
        )
        ax.scatter(
            sum_amount.loc[sum_amount["side"] == "sell"].index,
            sum_amount.loc[sum_amount["side"] == "sell"]["amount"],
            color=sell_color,
            label=sell_label,
            marker="o",
        )

        ax.axhline(0.0, linestyle="--", color=zero_line_color, linewidth=0.7)

        ax.set_title(
            f"volume analyze for position_id: {position.position_id}\ntotal volume: {position.ath_position_amount} {market_status.base_ccy}\n{position.side.upper()} position on {position.market}"
        )

        ax.set_ylabel(f"volume({market_status.base_ccy})")
        ax.set_xlabel(f"Time")
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        ax.legend()
        plt.xticks(rotation=45)

        plt.show()
        
        if save_path:
            filename = f"position_{position.position_id}_volume_analysis.png"
            save_path = os.path.join(save_path, filename)
            fig.savefig(save_path, bbox_inches="tight", dpi=300)

        return sum_amount

    def position_pnl_analyze(
        self,
        position: Position,
        figsize: tuple = (15, 8),
        buy_color: str = "g",
        sell_color: str = "r",
        funding_color: str = "black",
        fee_color: str = "r",
        realized_color: str = "blue",
        zero_line_color: str = "orange",
        buy_label: str = "buy order",
        sell_label: str = "sell order",
        funding_label: str = "funding rate",
        margin_scale: float = 0.1,
        date_format: str = "%b %d %H:%M:%S",
        save_path: str = None
    ):
        
        """
        Visualizes the realized PnL evolution of a trading position, including buy/sell events,
        funding rate adjustments, and transaction fees.

        Parameters:
            position (Position): The trading position to analyze.
            figsize (tuple): Size of the matplotlib figure (width, height). Default is (15, 8).
            buy_color (str): Color used for buy order markers. Default is "g".
            sell_color (str): Color used for sell order markers. Default is "r".
            funding_color (str): Color used for funding rate markers. Default is "black".
            fee_color (str): Color used for cumulative fee line. Default is "r".
            realized_color (str): Color used for realized PnL step line. Default is "blue".
            zero_line_color (str): Color of the horizontal zero PnL reference line. Default is "orange".
            buy_label (str): Label for buy orders in the legend.
            sell_label (str): Label for sell orders in the legend.
            funding_label (str): Label for funding rate events in the legend.
            margin_scale (float): Fraction of time margin added before/after the data range for padding. Default is 0.1.
            date_format (str): Format string for x-axis datetime labels. Default is "%b %d %H:%M:%S".
            save_path (str): Path to save plot image (png format).


        Returns:
            pd.DataFrame: A DataFrame of transactions including synthetic 'init' and 'finish' points,
                        used for fee visualization alignment.
        
        Notes:
            - Realized PnL is plotted as a step chart with cumulative values.
            - Buy/sell/funding events are shown as scatter points.
            - Fees are visualized as a dotted cumulative step line.
            - The chart includes a zero reference line and is annotated with position metadata.
            - Time padding is applied to ensure visual clarity at the edges.
        """

        fig, ax = plt.subplots(figsize=figsize)
        realized_pnl = position.realized_pnl_change()
        realized_pnl["realized_pnl_change"] = realized_pnl[
            "realized_pnl_change"
        ].cumsum()

        ax.scatter(
            realized_pnl.loc[realized_pnl["side"] == "buy"]["created_at"],
            realized_pnl.loc[realized_pnl["side"] == "buy"]["realized_pnl_change"],
            color=buy_color,
            label=buy_label,
        )

        ax.scatter(
            realized_pnl.loc[realized_pnl["side"] == "sell"]["created_at"],
            realized_pnl.loc[realized_pnl["side"] == "sell"]["realized_pnl_change"],
            color=sell_color,
            label=sell_label,
        )

        ax.scatter(
            realized_pnl.loc[realized_pnl["side"] == "funding"]["created_at"],
            realized_pnl.loc[realized_pnl["side"] == "funding"]["realized_pnl_change"],
            color=funding_color,
            label=funding_label,
        )

        margin = (
            realized_pnl.iloc[-1]["created_at"] - realized_pnl.iloc[0]["created_at"]
        ).total_seconds()

        init_time = realized_pnl.iloc[0]["created_at"] - pd.Timedelta(
            margin * margin_scale, unit="s"
        )

        finish_time = realized_pnl.iloc[-1]["created_at"] + pd.Timedelta(
            margin * margin_scale, unit="s"
        )

        init = pd.DataFrame(
            [
                {
                    "created_at": init_time,
                    "realized_pnl_change": 0.0,
                    "realized_type": "init",
                }
            ]
        )

        finish = pd.DataFrame(
            [
                {
                    "created_at": finish_time,
                    "realized_pnl_change": realized_pnl.iloc[-1]["realized_pnl_change"],
                    "realized_type": "finish",
                }
            ]
        )

        realized_pnl = pd.concat([realized_pnl, init, finish], ignore_index=True)

        realized_pnl.sort_values("created_at", inplace=True)
        realized_pnl.reset_index(drop=True, inplace=True)

        ax.axhline(0.0, linestyle="--", color=zero_line_color, linewidth=0.7)

        ax.step(
            realized_pnl["created_at"],
            realized_pnl["realized_pnl_change"],
            color=realized_color,
            where="post",
            label="realized pnl",
        )

        transactios = position.transactions_as_dataframe().copy()

        tr_init = pd.DataFrame([{"created_at": init_time, "fee": 0.0}])
        tr_finish = pd.DataFrame([{"created_at": finish_time, "fee": 0.0}])
        transactios = pd.concat([transactios, tr_init, tr_finish], ignore_index=True)
        transactios.sort_values("created_at", inplace=True)
        transactios.reset_index(drop=True, inplace=True)

        ax.step(
            transactios["created_at"],
            transactios["fee"].mul(-1).cumsum(),
            color=fee_color,
            where="post",
            linestyle="dotted",
            label="fee",
        )

        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))

        market_status = self.portfo.get_market_status(position.market)

        ax.set_ylabel(f"profit({market_status.quote_ccy})")
        ax.set_xlabel(f"Time")
        ax.set_title(
            f"pnl analyze for position_id: {position.position_id}\n{position.side.upper()} position on {position.market}\ntotal realized pnl: {position.realized_pnl:.4f} {market_status.quote_ccy}\n volume {position.ath_position_amount} {market_status.base_ccy}"
        )
        ax.legend()

        plt.xticks(rotation=45)

        plt.show()
        
        if save_path:
            filename = f"position_{position.position_id}_pnl_analysis.png"
            save_path = os.path.join(save_path, filename)
            fig.savefig(save_path, bbox_inches="tight", dpi=300)

        return transactios
