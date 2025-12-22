import pandas as pd
import plotly.graph_objects as go

# ===== データ読み込み =====
path = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"
df = pd.read_csv(path)

df["datetime"] = pd.to_datetime(
    df["Year"].astype(str) + "-" +
    df["Month"].astype(str) + "-" +
    df["Day"].astype(str) + " " +
    df["Hour"].astype(str) + ":00"
)
df.set_index("datetime", inplace=True)

# 表示本数を制限（超重要）
df = df.tail(300)

# ===== 描画データ作成 =====
x_upper, y_upper = [], []
x_lower, y_lower = [], []

for t, row in df.iterrows():
    o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]

    if c >= o:
        # 陽線
        # 上：高値→終値（陰線色）
        x_upper += [t, t, None]
        y_upper += [h, c, None]

        # 下：安値→始値（陽線色）
        x_lower += [t, t, None]
        y_lower += [l, o, None]
    else:
        # 陰線
        # 上：高値→始値（陰線色）
        x_upper += [t, t, None]
        y_upper += [h, o, None]

        # 下：安値→終値（陽線色）
        x_lower += [t, t, None]
        y_lower += [l, c, None]

# ===== Plotly描画 =====
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=x_upper,
    y=y_upper,
    mode="lines",
    line=dict(color="red", width=2),
    name="upper"
))

fig.add_trace(go.Scatter(
    x=x_lower,
    y=y_lower,
    mode="lines",
    line=dict(color="green", width=2),
    name="lower"
))

fig.update_layout(
    xaxis=dict(type="date"),
    showlegend=False
)

fig.show()
