# -*- coding: utf-8 -*-

import asyncio
import websockets
import json
import time
import gzip
import os
import csv

BIN_WS_URL = "wss://fstream.binance.com/stream"
WS_URL = "wss://socket.coinex.com/v2/futures"  # Change "spot" to "futures" when interacting with WS ports

bin_symbol = "btcusdt"
coinex_symbol = "BTCUSDT"

PING_ID = -1
ATH_ID = 1001
DEPTH_ID = 80
ASSET_ID = 230
STATUS_ID = 134
INDEX_ID = 670

MAX_POINTS = 2


count = 0
MAX_FILE_SAVE = 2

shutdown_event = asyncio.Event()



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





async def get_coinex_data(count):
    while True:

        try:
            async with websockets.connect(
                uri=WS_URL, compression=None, ping_interval=None
            ) as conn:
                await subscribe_market_status(conn)
                global ping_task
                ping_task = asyncio.create_task(ping(conn))
                ping_task.add_done_callback(lambda t: print(f"Ping task error: {t.exception()}") if t.exception() else None)
                f = open("streamData/coinex_BTCUSDT.csv", "a", newline="", encoding="utf-8")
                wr = csv.writer(f)

                while True:
                    if count % 10 == 0:
                        f.close()
                        await asyncio.sleep(0.01)
                        f = open("streamData/coinex_BTCUSDT.csv", "a", newline="", encoding="utf-8")
                        wr = csv.writer(f)
                        
                    if count == 1:
                        wr.writerow(["timestamp", "price"])

                    
                    res = await conn.recv()
                    res = gzip.decompress(res)
                    res = json.loads(res)
                    if res.get("method") == "state.update":
                        last = float(res.get("data")["state_list"][0]["last"])
                        count += 1
                        wr.writerow([time.time(), last])

                    await asyncio.sleep(0.01)
                    
        except websockets.exceptions.ConnectionClosedError as e:
            print("Coinex Connection Error try to reconnectiong...")
            await asyncio.sleep(.5)
            
            
        except Exception as e:
            print(f"An error occurred: {e}")
            if not f.closed:
                f.close()





async def binance_get_data(count):
    try:
        async with websockets.connect(build_binance_ws_url([bin_symbol], stream_type="ticker")) as conn:
            while True:
                if count % 10 == 1:
                    if count > 1:
                        f.close()
                    f = open("streamData/binance_BTCUSDT.csv", "a", newline="", encoding="utf-8")
                    wr = csv.writer(f)
                
                if count == 1:
                    wr.writerow(["timestamp", "price"])


                res = await conn.recv()
                data = json.loads(res)
                wr.writerow([data["data"]["E"], data["data"]["c"]])
                count += 1
                await asyncio.sleep(0.01)

    except Exception as e:
        print(f"binance_get_data Exception: {e}")
            




async def main():
    asyncio.create_task(get_coinex_data(1))
    asyncio.create_task(binance_get_data(1))
    await asyncio.sleep(86400)


if __name__ == "__main__":
    os.makedirs("./streamData", exist_ok=True)
    asyncio.run(main())
