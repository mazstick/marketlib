import asyncio
import websockets
import json

BIN_WS_URL = "wss://fstream.binance.com/stream"


def build_binance_ws_url(symbols, stream_type, update_speed_ms=1):

    stream_parts = []
    for symbol in symbols:
        symbol_lower = symbol.lower()
        if stream_type == 'markPrice':
            stream_parts.append(f"{symbol_lower}@{stream_type}@{update_speed_ms}s")
        else:
            stream_parts.append(f"{symbol_lower}@{stream_type}")

    stream_query = "/".join(stream_parts)
    url = f"{BIN_WS_URL}?streams={stream_query}"
    return url


async def main():
    try:
        async with websockets.connect(build_binance_ws_url(["btcusdt"], stream_type="ticker")) as conn:
            while True:
                res = await conn.recv()
                data = json.loads(res)
                print(f"📊 BTCUSDT Price: {data.get("data").get("c")}")

    except Exception as e:
        print(f"Exception occurred: {e}")

asyncio.run(main())