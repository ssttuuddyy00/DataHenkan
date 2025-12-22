import pandas as pd
import numpy as np
import mplfinance as mpf

# =========================
# CSV読み込み
# =========================
df = pd.read_csv(
    "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"
)


# DateTime生成
df["Date"] = pd.to_datetime(
    df["Year"].astype(str) + "-"
    + df["Month"].astype(str) + "-"
    + df["Day"].astype(str) + " "
    + df["Hour"].astype(str) + ":00"
)
df.set_index("Date", inplace=True)

df = df[["Open", "High", "Low", "Close", "Volume"]]

# =========================
# ローソク足描画
# =========================
df = df.tail(500)
fig, axlist = mpf.plot(
    df,
    type="candle",
    style="classic",
    returnfig=True,
    warn_too_much_data=len(df) + 1
)

ax = axlist[0]

# =========================
# 髭の色を上書き
# =========================
for i, (o, h, l, c) in enumerate(
    zip(df["Open"], df["High"], df["Low"], df["Close"])
):
    upper_wick_top = h
    upper_wick_bottom = max(o, c)

    lower_wick_top = min(o, c)
    lower_wick_bottom = l

    # 上髭（赤）
    ax.vlines(
        i,
        upper_wick_bottom,
        upper_wick_top,
        color="red",
        linewidth=1.2,
        zorder=3
    )

    # 下髭（緑）
    ax.vlines(
        i,
        lower_wick_bottom,
        lower_wick_top,
        color="green",
        linewidth=1.2,
        zorder=3
    )

mpf.show()

