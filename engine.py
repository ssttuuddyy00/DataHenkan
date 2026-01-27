import numpy as np
import pandas as pd
import config

# 状態管理
balance = config.INITIAL_BALANCE
is_autoplay = False
autoplay_speed = 0.5
trade = None
hlines_data, stop_lines_data = [], []
markers, history = [], []
pressed = set()
selected_obj, dragging = None, False

# フィボナッチ用
fibo_mode = None # "RETRACE" or "EXT"
fibo_points = []
retracements = [] # list of dicts {p1, p2}
extensions = []   # list of dicts {p1, p2, p3}

# ドラッグ中の軸固定用変数
fixed_ylim = None

def check_stop_loss():
    global trade, balance, stop_lines_data, markers
    if not trade or not stop_lines_data: return False
    curr = df_base.iloc[idx_base]
    sl_p = stop_lines_data[0][0]
    is_hit = (trade["side"]=="BUY" and curr["Low"] <= sl_p) or (trade["side"]=="SELL" and curr["High"] >= sl_p)
    if is_hit:
        pips = round((sl_p - trade["price"]) / PIPS_UNIT if trade["side"]=="BUY" else (trade["price"] - sl_p) / PIPS_UNIT, 1)
        profit = round(pips * ONE_LOT_PIPS_VALUE * trade["lot"], 0)
        history.append({**trade, "exit_p": sl_p, "exit_time": curr.name, "pips": pips, "profit": profit})
        balance += profit
        markers.append((curr.name, sl_p, "x", "black", 0.3))
        trade = None; stop_lines_data.clear()
        return True
    return False

def get_pair_settings(df):
    sample = df['Close'].iloc[0]
    return (0.01, 1000) if sample > 50 else (0.0001, 1500)
