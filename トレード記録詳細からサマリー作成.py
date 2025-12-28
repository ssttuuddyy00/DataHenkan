import pandas as pd

# CSVとして保存したファイルを読み込み
df = pd.read_csv("Rikakuzoon_trading_details.csv", header=None)

df.columns = [
    "Direction", "Entry_Price", "Start_Time", "Lots",
    "SL", "TP", "Type", "Exit_Price",
    "End_Time", "Pips", "Profit_JPY"
]

df["Start_Time"] = pd.to_datetime(df["Start_Time"])
df["End_Time"] = pd.to_datetime(df["End_Time"])

# Execution time
df["Execution_Time"] = (df["End_Time"] - df["Start_Time"]).dt.total_seconds()

total_trades = len(df)
total_pips = df["Pips"].sum()
profit_jpy = df["Profit_JPY"].sum()
final_balance = df["Profit_JPY"].iloc[-1]

wins = df[df["Pips"] > 0]
losses = df[df["Pips"] < 0]

win_rate = len(wins) / total_trades * 100

risk_reward = wins["Pips"].mean() / abs(losses["Pips"].mean())
pf = wins["Pips"].sum() / abs(losses["Pips"].sum())

# 連勝・連敗
streak = (df["Pips"] > 0).astype(int)
win_streak = streak.groupby((streak != streak.shift()).cumsum()).sum().max()

streak_loss = (df["Pips"] < 0).astype(int)
loss_streak = streak_loss.groupby((streak_loss != streak_loss.shift()).cumsum()).sum().max()

result = {
    "Execution_RealTime_avg_sec": df["Execution_Time"].mean(),
    "Start_Trade_Time": df["Start_Time"].min(),
    "End_Trade_Time": df["End_Time"].max(),
    "Total_Trades": total_trades,
    "Total_Pips": total_pips,
    "Profit_JPY": profit_jpy,
    "Final_Balance": final_balance,
    "Win_Rate_%": win_rate,
    "Risk_Reward": risk_reward,
    "PF": pf,
    "Win_Streaks": win_streak,
    "Loss_Streaks": loss_streak
}

for k, v in result.items():
    print(f"{k}: {v}")
