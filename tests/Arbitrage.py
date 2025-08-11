import matplotlib.pyplot as plt
import pandas as pd


coinex_btc = pd.read_csv("coinex_BTCUSDT.csv")
binance_btc = pd.read_csv("binance_BTCUSDT.csv")
coinex_btc["timestamp"] = pd.to_datetime(coinex_btc["timestamp"], unit="s")
binance_btc["timestamp"] = pd.to_datetime(binance_btc["timestamp"], unit="ms")


fee = 0.028/100

fig1, ax1 = plt.subplots(figsize=(20, 7))



ax1.plot(binance_btc["timestamp"], binance_btc["price"], label="binanc BTCUSDT")
ax1.plot(coinex_btc["timestamp"], coinex_btc["price"], label="coinex BTCUSDT")

# ax1.plot(binance_btc["timestamp"], binance_btc["price"].mul(1+fee), linestyle="--", color="#450", label="1 fee")
# ax1.plot(binance_btc["timestamp"], binance_btc["price"].mul(1-fee), linestyle="--", color="#450")
# ax1.plot(binance_btc["timestamp"], binance_btc["price"].mul(1+2*fee), linestyle="--", color="#380", label="2 fee")
# ax1.plot(binance_btc["timestamp"], binance_btc["price"].mul(1-2*fee), linestyle="--", color="#380")
ax1.ticklabel_format(style="plain", axis="y", useOffset=False)
ax1.grid()


fig, ax2 = plt.subplots(figsize=(20,7))
merged = pd.merge_asof(coinex_btc, binance_btc, on="timestamp").bfill()

ax2.plot(binance_btc["timestamp"], binance_btc["price"]/binance_btc["price"], label="binanc BTCUSDT")
ax2.plot(coinex_btc["timestamp"], merged["price_x"]/merged["price_y"], label="coinex BTCUSDT")


ax2.plot(binance_btc["timestamp"], binance_btc["price"]/binance_btc["price"].mul(1+fee), linestyle="--", color="#450", label="1 fee")
ax2.plot(binance_btc["timestamp"], binance_btc["price"]/binance_btc["price"].mul(1-fee), linestyle="--", color="#450")
ax2.plot(binance_btc["timestamp"], binance_btc["price"]/binance_btc["price"].mul(1+2*fee), linestyle="--", color="#380", label="2 fee")
ax2.plot(binance_btc["timestamp"], binance_btc["price"]/binance_btc["price"].mul(1-2*fee), linestyle="--", color="#380")
ax2.ticklabel_format(style="plain", axis="y", useOffset=False)


plt.legend()
plt.show()