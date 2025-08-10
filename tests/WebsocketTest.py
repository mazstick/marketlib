# -*- coding: utf-8 -*-

import asyncio
import websockets
import json
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.dates import date2num
from matplotlib.animation import FuncAnimation
import hashlib
import gzip
import hmac


BIN_WS_URL = "wss://fstream.binance.com/stream"
WS_URL = "wss://socket.coinex.com/v2/futures"  # Change "spot" to "futures" when interacting with WS ports
access_id = "19B5BFA0056444769D37DCD7A45BB646"  # Replace with your access id
secret_key = (
    "5909588B7DF5807D378E1C241B4E39F94247126004691590"  # Replace with your secret key
)

PING_ID = -1
ATH_ID = 1001
DEPTH_ID = 80
ASSET_ID = 230
STATUS_ID = 134
INDEX_ID = 670

MAX_POINTS = 200


def build_binance_ws_url(symbols, stream_type, update_speed_ms=1):

    stream_parts = []
    for symbol in symbols:
        symbol_lower = symbol.lower()
        if stream_type == "markPrice":
            stream_parts.append(f"{symbol_lower}@{stream_type}@{update_speed_ms}s")
        else:
            stream_parts.append(f"{symbol_lower}@{stream_type}")

    stream_query = "/".join(stream_parts)
    url = f"{BIN_WS_URL}?streams={stream_query}"
    return url


async def ping(conn):
    param = {"method": "server.ping", "params": {}, "id": PING_ID}
    while True:
        await conn.send(json.dumps(param))
        await asyncio.sleep(3)


async def auth(conn):
    timestamp = int(time.time() * 1000)

    prepared_str = f"{timestamp}"
    signed_str = (
        hmac.new(
            bytes(secret_key, "latin-1"),
            msg=bytes(prepared_str, "latin-1"),
            digestmod=hashlib.sha256,
        )
        .hexdigest()
        .lower()
    )

    param = {
        "method": "server.sign",
        "params": {
            "access_id": access_id,
            "signed_str": signed_str,
            "timestamp": timestamp,
        },
        "id": ATH_ID,
    }
    await conn.send(json.dumps(param))
    res = await conn.recv()
    res = gzip.decompress(res)
    print("Authentication Result: ", json.loads(res))


async def subscribe_depth(conn):
    param = {
        "method": "depth.subscribe",
        "params": {"market_list": [["BTCUSDT", 5, "0", True]]},
        "id": DEPTH_ID,
    }
    await conn.send(json.dumps(param))
    res = await conn.recv()
    res = gzip.decompress(res)
    print("SUBSCRIBE DEPTH :", json.loads(res))


async def subscribe_asset(conn):
    param = {
        "method": "balance.subscribe",
        "params": {"ccy_list": ["USDT"]},
        "id": ASSET_ID,
    }
    await conn.send(json.dumps(param))
    res = await conn.recv()
    res = gzip.decompress(res)
    print("SUBSCRIBE ASSET BALANCE :", json.loads(res))


async def subscribe_market_index(conn):
    param = {
        "method": "index.subscribe",
        "params": {"market_list": ["BTCUSDT"]},
        "id": INDEX_ID,
    }
    await conn.send(json.dumps(param))
    res = await conn.recv()
    res = gzip.decompress(res)
    print("SUBSCRIBE INDEX:", json.loads(res))


async def subscribe_market_status(conn):
    param = {
        "method": "state.subscribe",
        "params": {"market_list": [coinex_symbol]},
        "id": STATUS_ID,
    }
    await conn.send(json.dumps(param))
    res = await conn.recv()
    res = gzip.decompress(res)
    print("SUBSCRIBE STATUS:", json.loads(res))


prices = []
timestamp = []
coinex_symbol = "ETHUSDT"


async def get_data():
    try:
        async with websockets.connect(
            uri=WS_URL, compression=None, ping_interval=None
        ) as conn:
            await auth(conn)
            await subscribe_market_status(conn)
            asyncio.create_task(ping(conn))

            while True:
                res = await conn.recv()
                res = gzip.decompress(res)
                res = json.loads(res)
                if res.get("method") == "state.update":
                    last = float(res.get("data")["state_list"][0]["last"])
                    print("\033[92mcoinex-btc: ", last, "\033[00m")
                    prices.append(last)
                    timestamp.append(
                        pd.Timestamp(time.time(), unit="s", tz="Asia/Tehran")
                    )

                    if len(prices) > MAX_POINTS:
                        prices[:] = prices[-MAX_POINTS:]
                        timestamp[:] = timestamp[-MAX_POINTS:]

                await asyncio.sleep(0.01)

    except Exception as e:
        print(f"An error occurred: {e}")


async def plot_align_price():

    from matplotlib.dates import DateFormatter

    plt.ion()
    fig, ax = plt.subplots(figsize=(15, 7))
    (coinex_line,) = ax.plot([], [], color="blue", label=f"coinex: {coinex_symbol}")
    (binance_line,) = ax.plot(
        [], [], color="red", label=f"binance: {bin_symbol.upper()}"
    )
    (fee_1_up,) = ax.plot([], [], color="#701", linestyle="--", label=f"1 * fee({fee})")
    (fee_1_down,) = ax.plot([], [], color="#701", linestyle="--")
    (fee_2_up,) = ax.plot([], [], color="orange", linestyle="--", label=f"2 * fee({fee})")
    (fee_2_down,) = ax.plot([], [], color="orange", linestyle="--")

    ax.set_xlabel("Time")
    ax.set_ylabel("Align on binance price")
    ax.ticklabel_format(style="plain", axis="y", useOffset=False)
    # ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    fig.autofmt_xdate(rotation=45)
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S", tz="Asia/Tehran"))
    aligned_coinex_price = []
    aligned_coinex_time = []

    ax.legend(loc="upper left")
    while True:
        if prices and binance_prices:
            aligned_coinex_price.append(prices[-1] / binance_prices[-1])
            aligned_coinex_time.append(timestamp[-1])
            x = date2num(aligned_coinex_time)
            coinex_line.set_data(x, aligned_coinex_price)
            b_x = date2num(binance_time.copy())
            binance_line.set_data(b_x, [x / x for x in binance_prices])
            ax.set_title(
                f"Real-time {coinex_symbol} Aligned on binance Price\ndif price percent {100 * (binance_prices[-1] - prices[-1])/ binance_prices[-1] :.4f} %\ndif price {binance_prices[-1] - prices[-1]}\n binnace tick: {binance_prices[-1]:.4f} --------- coinex tick: {prices[-1]:.4f}"
            )
            fee1_list = [(x * (1 + fee)) / x for x in binance_prices]
            fee1_list_down = [(x * (1 - fee) / x) for x in binance_prices]
            fee2_list = [(x * (1 + 2 * fee)) / x for x in binance_prices]
            fee2_list_down = [(x * (1 - 2 * fee)) / x for x in binance_prices]
            fee_1_up.set_data(b_x, fee1_list)
            fee_1_down.set_data(b_x, fee1_list_down)
            fee_2_up.set_data(b_x, fee2_list)
            fee_2_down.set_data(b_x, fee2_list_down)
            ax.set_ylim(
                (
                    min(min(aligned_coinex_price), min(fee2_list_down)) * 0.998,
                    max(max(aligned_coinex_price), max(fee2_list)) * 1.002,
                )
            )

            ax.relim()
            ax.autoscale_view()
            fig.canvas.draw()
            fig.canvas.flush_events()
        await asyncio.sleep(0.5)


async def plot_price():

    from matplotlib.dates import DateFormatter

    plt.ion()
    fig, ax = plt.subplots(figsize=(15, 7))
    (coinex_line,) = ax.plot([], [], color="blue", label=f"coinex: {coinex_symbol}")
    (binance_line,) = ax.plot(
        [], [], color="red", label=f"binance: {bin_symbol.upper()}"
    )
    (fee_1_up,) = ax.plot([], [], color="#701", linestyle="--", label=f"1 * fee({fee})")
    (fee_1_down,) = ax.plot([], [], color="#701", linestyle="--")
    (fee_2_up,) = ax.plot([], [], color="orange", linestyle="--", label=f"2 * fee({fee})")
    (fee_2_down,) = ax.plot([], [], color="orange", linestyle="--")

    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    ax.ticklabel_format(style="plain", axis="y", useOffset=False)
    # ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    fig.autofmt_xdate(rotation=45)
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S", tz="Asia/Tehran"))

    ax.legend(loc="upper left")
    while True:
        if prices and binance_prices:
            x = date2num(timestamp.copy())
            coinex_line.set_data(x, prices.copy())
            b_x = date2num(binance_time.copy())
            binance_line.set_data(b_x, binance_prices.copy())
            ax.set_title(
                f"Real-time {coinex_symbol} Price\ndif price percent {100 * (binance_prices[-1] - prices[-1])/ binance_prices[-1] :.4f} %\ndif price {binance_prices[-1] - prices[-1]}\n binnace tick: {binance_prices[-1]:.4f} --------- coinex tick: {prices[-1]:.4f}"
            )
            fee1_list = [x * (1 + fee) for x in binance_prices]
            fee1_list_down = [x * (1 - fee) for x in binance_prices]
            fee2_list = [x * (1 + 2 * fee) for x in binance_prices]
            fee2_list_down = [x * (1 - 2 * fee) for x in binance_prices]
            fee_1_up.set_data(b_x, fee1_list)
            fee_1_down.set_data(b_x, fee1_list_down)
            fee_2_up.set_data(b_x, fee2_list)
            fee_2_down.set_data(b_x, fee2_list_down)
            ax.set_ylim(
                (
                    min(min(prices), min(binance_prices), min(fee2_list_down)) * 0.9998,
                    max(max(prices), max(binance_prices), max(fee2_list)) * 1.0002,
                )
            )

            ax.relim()
            ax.autoscale_view()
            fig.canvas.draw()
            fig.canvas.flush_events()
        await asyncio.sleep(0.5)


binance_prices = []
binance_time = []
bin_symbol = "ethusdt"
fee = 0.028/100


    


async def binance_get_data():
    try:
        async with websockets.connect(
            build_binance_ws_url([bin_symbol], stream_type="ticker")
        ) as conn:
            while True:
                res = await conn.recv()
                data = json.loads(res)
                last = float(data.get("data").get("c"))
                print(f"\033[96mbinance-btc: {last}\033[00m")

                binance_prices.append(last)
                binance_time.append(
                    pd.Timestamp(
                        float(data.get("data").get("E")), unit="ms", tz="Asia/Tehran"
                    )
                )

                if len(binance_prices) > MAX_POINTS:
                    binance_prices[:] = binance_prices[-MAX_POINTS:]
                    binance_time[:] = binance_time[-MAX_POINTS:]

    except Exception as e:
        print(f"Exception occurred: {e}")
        
        
        


async def save_data(path):

    while True:
        await asyncio.sleep(5)
        if binance_prices and prices:
            
            coinex_df = pd.DataFrame(prices, index=timestamp)
            binance_df = pd.DataFrame(binance_prices, index=binance_time)
            print(coinex_df)
            


async def main():
    await asyncio.gather(get_data(), binance_get_data(), save_data(""))


if __name__ == "__main__":
    asyncio.run(main())
