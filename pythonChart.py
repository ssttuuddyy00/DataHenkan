import pandas as pd

path = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"

df = pd.read_csv(path)

# datetime 列を作成
df["datetime"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Day"].astype(str) + " " +
    df["Hour"].astype(str) + ":00"
)

# index に設定
df.set_index("datetime", inplace=True)

print(df.head())
import mplfinance as mpf
WINDOW = 100   # 表示する本数
pos = WINDOW

mpf.plot(df.iloc[pos-WINDOW:pos], type="candle")

import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )
])

fig.show()
