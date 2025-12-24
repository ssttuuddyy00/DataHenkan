import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import os
import numpy as np

# =========================
# 設定
# =========================
MN_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv"
D1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/B_data.csv"
H1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"

WINDOW_H1, WINDOW_D1, WINDOW_MN = 200, 100, 60
PIP_VALUE = 0.0001 

def load_csv(path):
    if not os.path.exists(path): raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    temp_df = df.copy()
    if "Day" not in cols: temp_df["Day"] = 1
    if "Hour" not in cols: temp_df["Hour"] = 0
    df["Date"] = pd.to_datetime(temp_df[["Year", "Month", "Day", "Hour"]])
    df.set_index("Date", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]

try:
    df_mn, df_d1, df_h1 = load_csv(MN_PATH), load_csv(D1_PATH), load_csv(H1_PATH)
except Exception as e:
    print(f"Error: {e}"); exit()

idx_h1, view_offset = 500, 0 

# =========================
# 状態管理
# =========================
hlines_data = []     # [price, color, linestyle]
stop_lines_data = [] # [price, color, linestyle]
rects_data = []      # [t1, t2, p_top, p_bottom]
markers, history = [], []
trade = None
pressed = set()
rect_start = None
temp_rect = None
selected_obj = None # (type, index)
dragging = False

# =========================
# 補助関数
# =========================
def check_stop_loss():
    global trade, stop_lines_data
    if not trade or not stop_lines_data: return
    curr = df_h1.iloc[idx_h1]
    for i, (p, c, ls) in enumerate(stop_lines_data):
        if (trade["side"]=="BUY" and curr["Low"] <= p) or (trade["side"]=="SELL" and curr["High"] >= p):
            pips = ((p - trade["price"]) if trade["side"]=="BUY" else (trade["price"] - p)) / PIP_VALUE
            history.append({**trade, "exit_p":p, "pips":pips, "exit_time": curr.name})
            markers.append((curr.name, p, "x", "black"))
            trade = None; stop_lines_data.clear(); break

def get_time_from_x(ax, xdata):
    if xdata is None: return None
    end_idx = idx_h1 + view_offset
    if ax == ax_h1:
        data, start = df_h1, max(0, end_idx - WINDOW_H1)
    elif ax == ax_d1:
        curr_t = df_h1.index[end_idx]
        d1_end = df_d1.index[df_d1.index <= curr_t].shape[0] - 1
        data, start = df_d1, max(0, d1_end - WINDOW_D1)
    elif ax == ax_mn:
        curr_t = df_h1.index[end_idx]
        mn_end = df_mn.index[df_mn.index <= curr_t].shape[0] - 1
        data, start = df_mn, max(0, mn_end - WINDOW_MN)
    else: return None
    count = len(data.iloc[start : end_idx + 1])
    idx = int(round(xdata))
    idx = max(0, min(idx, count - 1))
    return data.iloc[start + idx].name

def redraw():
    end_idx = idx_h1 + view_offset
    h1_data = df_h1.iloc[max(0, end_idx - WINDOW_H1) : end_idx + 1]
    v_times = h1_data.index.tolist()
    curr_time = v_times[-1]
    
    # 上位足の「未来」を表示しないようにフィルタリング
    d1_all_past = df_d1[df_d1.index <= curr_time]
    d1_data = d1_all_past.iloc[-WINDOW_D1-1:]
    vd1_times = d1_data.index.tolist()
    
    mn_all_past = df_mn[df_mn.index <= curr_time]
    mn_data = mn_all_past.iloc[-WINDOW_MN-1:]
    vmn_times = mn_data.index.tolist()

    ax_mn.clear(); ax_d1.clear(); ax_h1.clear(); ax_info.clear()
    mpf.plot(mn_data, ax=ax_mn, type="candle", style="yahoo")
    mpf.plot(d1_data, ax=ax_d1, type="candle", style="yahoo")
    mpf.plot(h1_data, ax=ax_h1, type="candle", style="yahoo")

    for ax, times in [(ax_mn, vmn_times), (ax_d1, vd1_times), (ax_h1, v_times)]:
        if not times: continue
        all_l = hlines_data + stop_lines_data
        for i, (p, c, ls) in enumerate(all_l):
            is_stop = i >= len(hlines_data)
            type_str = 'stop' if is_stop else 'hline'
            real_idx = i - len(hlines_data) if is_stop else i
            sel = selected_obj == (type_str, real_idx)
            ax.add_line(Line2D([0, 1], [p, p], transform=ax.get_yaxis_transform(), 
                               color="orange" if sel else c, linestyle=ls, linewidth=2.5 if sel else 1.5))
        
        display_rects = rects_data + ([temp_rect] if temp_rect else [])
        for i, r_data in enumerate(display_rects):
            t1, t2, pt, pb = r_data
            is_preview = (temp_rect and i == len(display_rects)-1)
            if (min(t1, t2) <= times[-1]) and (max(t1, t2) >= times[0]):
                x1 = times.index(t1) if t1 in times else (0 if t1 < times[0] else len(times)-1)
                x2 = times.index(t2) if t2 in times else (0 if t2 < times[0] else len(times)-1)
                color = "cyan" if is_preview else ("orange" if selected_obj==('rect',i) else "green")
                ax.add_patch(Rectangle((min(x1, x2), min(pt, pb)), abs(x1 - x2), abs(pt - pb), 
                                       fill=False, edgecolor=color, linewidth=1.5, linestyle="--" if is_preview else "-"))

    for mt, mp, ms, mc in markers:
        if mt in v_times: ax_h1.scatter(v_times.index(mt), mp, marker=ms, color=mc, s=100, zorder=5)

    ax_info.axis("off")
    total = sum(h['pips'] for h in history)
    txt = f"TOTAL: {total:+.1f}p\n"
    txt += f"TRADES: {len(history)}\n"
    txt += "-"*10 + "\n"
    for h in history[-8:]: txt += f"{h['side']} {h['pips']:+.1f}p\n"
    ax_info.text(0, 1, txt, transform=ax_info.transAxes, verticalalignment="top", fontsize=9, fontfamily="monospace")
    ax_h1.set_title(f"REPLAY: {df_h1.index[idx_h1]} | {'LIVE' if view_offset==0 else 'PAST'}")
    fig.canvas.draw_idle()

# =========================
# イベント
# =========================
def on_key_press(e):
    global idx_h1, view_offset, selected_obj; pressed.add(e.key)
    if e.key == "t":
        target = input("Jump to (YYYY-MM-DD HH:MM): ")
        try:
            new_idx = df_h1.index.get_indexer([pd.to_datetime(target)], method='pad')[0]
            if new_idx != -1: idx_h1, view_offset = new_idx, 0
        except: print("Invalid date")
        redraw(); return

    if e.key in ["delete", "backspace"] and selected_obj:
        t, i = selected_obj
        if t == 'hline': hlines_data.pop(i)
        elif t == 'stop': stop_lines_data.pop(i)
        elif t == 'rect': rects_data.pop(i)
        selected_obj = None; redraw(); return

    step = 10 if "control" in pressed else 1
    if e.key == "right":
        if view_offset < 0: view_offset = min(0, view_offset + step)
        else: idx_h1 = min(len(df_h1)-1, idx_h1 + step); check_stop_loss()
    elif e.key == "left":
        if "shift" in pressed: idx_h1 = max(WINDOW_H1, idx_h1 - step)
        else: view_offset -= step
    elif e.key == "home": view_offset = 0
    redraw()

def on_button_press(e):
    global trade, rect_start, selected_obj, dragging, stop_lines_data
    if not e.inaxes or e.xdata is None: return
    t_click = get_time_from_x(e.inaxes, e.xdata)
    curr_v_idx = max(0, min(len(df_h1)-1, idx_h1 + view_offset))
    v_time, v_price = df_h1.index[curr_v_idx], df_h1.iloc[curr_v_idx]["Close"]

    if e.button == 1 and not any(k in pressed for k in ["control", "shift", "b", "v", "c", "h"]):
        selected_obj = None
        yr = e.inaxes.get_ylim()[1] - e.inaxes.get_ylim()[0]
        for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
            if abs(p - e.ydata) < yr * 0.03:
                is_s = i >= len(hlines_data)
                selected_obj = ('stop' if is_s else 'hline', i - len(hlines_data) if is_s else i); break
        if not selected_obj:
            for i, (t1, t2, pt, pb) in enumerate(rects_data):
                if min(t1, t2) <= t_click <= max(t1, t2) and min(pt, pb) <= e.ydata <= max(pt, pb):
                    selected_obj = ('rect', i); break
        if selected_obj: dragging = True
        redraw(); return

    if e.button == 3: rect_start = (t_click, e.ydata); return
    if e.button == 1:
        if "b" in pressed:
            trade = {"side":"BUY", "price":v_price, "time":v_time}
            markers.append((v_time, v_price, "^", "blue"))
        elif "v" in pressed:
            trade = {"side":"SELL", "price":v_price, "time":v_time}
            markers.append((v_time, v_price, "v", "red"))
        elif "c" in pressed and trade:
            pips = ((v_price - trade["price"]) if trade["side"]=="BUY" else (trade["price"] - v_price)) / PIP_VALUE
            history.append({**trade, "exit_p":v_price, "pips":pips, "exit_time": v_time})
            markers.append((v_time, v_price, "x", "black")); trade = None; stop_lines_data.clear()
        elif "h" in pressed: hlines_data.append([e.ydata, "blue", "-"])
        elif "shift" in pressed: stop_lines_data.append([e.ydata, "red", "--"])
        redraw()

def on_motion(e):
    global dragging, temp_rect
    if not e.inaxes or e.xdata is None: return
    t_curr = get_time_from_x(e.inaxes, e.xdata)
    if rect_start: temp_rect = [rect_start[0], t_curr, rect_start[1], e.ydata]; redraw(); return
    if not (dragging and selected_obj): return
    type, i = selected_obj
    if type in ['hline', 'stop']: (hlines_data if type=='hline' else stop_lines_data)[i][0] = e.ydata
    redraw()

def on_release(e):
    global rect_start, dragging, temp_rect; dragging = False
    if e.button == 3 and rect_start:
        if temp_rect: rects_data.append([temp_rect[0], temp_rect[1], temp_rect[2], temp_rect[3]])
        rect_start = temp_rect = None; redraw()

# =========================
# 統計算出
# =========================
# =========================
# 統計算出（強化版）
# =========================
def show_statistics():
    if not history:
        print("\nトレードデータがありません。")
        return

    df = pd.DataFrame(history)

    def analyze_side(data, label):
        if data.empty:
            print(f"\n--- {label} レポート ---")
            print("トレードなし")
            return

        pips = data['pips']
        wins = pips[pips > 0]
        losses = pips[pips <= 0]
        
        # 連勝・連敗の解析
        results = (pips > 0).astype(int).tolist()
        max_wins = max_losses = curr_wins = curr_losses = 0
        win_streak_count = 0  # 連勝（2連勝以上）が発生した回数
        loss_streak_count = 0 # 連敗（2連敗以上）が発生した回数
        
        for i in range(len(results)):
            if results[i] == 1:
                curr_wins += 1
                if curr_losses >= 2: loss_streak_count += 1
                curr_losses = 0
                max_wins = max(max_wins, curr_wins)
            else:
                curr_losses += 1
                if curr_wins >= 2: win_streak_count += 1
                curr_wins = 0
                max_losses = max(max_losses, curr_losses)
        
        # 最後のループ分のカウント
        if curr_wins >= 2: win_streak_count += 1
        if curr_losses >= 2: loss_streak_count += 1

        pf = abs(wins.sum() / losses.sum()) if not losses.empty else float('inf')
        rr = abs(wins.mean() / losses.mean()) if not losses.empty and not wins.empty else 0
        wr = (len(wins) / len(data)) * 100

        print(f"\n--- {label} レポート ---")
        print(f"トレード数   : {len(data)} 回")
        print(f"勝率         : {wr:.1f} %")
        print(f"合計損益     : {pips.sum():+.1f} pips")
        print(f"PF           : {pf:.2f}")
        print(f"リスクリワード: {rr:.2f}")
        print(f"平均利益     : {wins.mean():.1f} pips" if not wins.empty else "平均利益     : 0")
        print(f"平均損失     : {losses.mean():.1f} pips" if not losses.empty else "平均損失     : 0")
        print(f"最大利益     : {pips.max():+.1f} pips")
        print(f"最大損失     : {pips.min():+.1f} pips")
        print(f"最大連勝数   : {max_wins} 回")
        print(f"最大連敗数   : {max_losses} 回")
        print(f"連勝発生回数 : {win_streak_count} 回 (2連勝以上)")
        print(f"連敗発生回数 : {loss_streak_count} 回 (2敗以上)")

    print("\n" + "★" * 20 + " 最終統計レポート " + "★" * 20)
    
    # 総合レポート
    analyze_side(df, "総合 (TOTAL)")
    
    # 買いレポート
    analyze_side(df[df['side'] == 'BUY'], "買い (BUY ONLY)")
    
    # 売りレポート
    analyze_side(df[df['side'] == 'SELL'], "売り (SELL ONLY)")
    
    print("\n" + "★" * 50)
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 2], width_ratios=[5, 1], hspace=0.4, wspace=0.1)
ax_mn, ax_d1, ax_h1, ax_info = fig.add_subplot(gs[0,0]), fig.add_subplot(gs[1,0]), fig.add_subplot(gs[2,0]), fig.add_subplot(gs[:,1])

fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", lambda e: pressed.discard(e.key))
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("motion_notify_event", on_motion)
fig.canvas.mpl_connect("button_release_event", on_release)

# 終了時に統計を表示
fig.canvas.mpl_connect("close_event", lambda e: show_statistics())

redraw(); plt.show()