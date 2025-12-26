import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox
import datetime  # スクリプトの冒頭に追加してください
# =========================
# 1. 設定・パス
# =========================
MN_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv"
D1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/B_data.csv"
H1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"

WINDOW_H1, WINDOW_D1, WINDOW_MN = 200, 100, 60
INITIAL_BALANCE = 1500000.0
RISK_PER_TRADE = 10000.0

# =========================
# 2. データ読み込み関数
# =========================
def load_csv(path):
    if not os.path.exists(path): raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path)
    # 列名の正規化（小文字・大文字の揺れを吸収）
    df.columns = [c.capitalize() for c in df.columns]
    
    temp_df = df.copy()
    if "Day" not in df.columns: temp_df["Day"] = 1
    if "Hour" not in df.columns: temp_df["Hour"] = 0
    
    df["Date"] = pd.to_datetime(temp_df[["Year", "Month", "Day", "Hour"]])
    df.set_index("Date", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]

def get_pair_settings(df):
    sample_price = df['Close'].iloc[0]
    if sample_price > 50:  # クロス円
        return 0.01, 1000  # 1pips単位, 1lotあたりの1pips損益(円)
    else:                  # ドルストレート
        return 0.0001, 1500 # 1pips単位, 1lotあたりの1pips損益(円)

# データロード
try:
    df_mn, df_d1, df_h1 = load_csv(MN_PATH), load_csv(D1_PATH), load_csv(H1_PATH)
    PIPS_UNIT, ONE_LOT_PIPS_VALUE = get_pair_settings(df_h1)
    print(f"H1データ読み込み成功: {len(df_h1)} 行")
except Exception as e:
    print(f"読み込みエラー: {e}"); exit()

# =========================
# 3. 状態管理
# =========================
idx_h1 = WINDOW_H1 + 50
view_offset = 0
balance = INITIAL_BALANCE
current_lot = 0.1
trade = None
hlines_data, stop_lines_data, rects_data = [], [], []
markers, history = [], []
pressed = set()
rect_start, temp_rect = None, None
selected_obj, dragging = None, False

# =========================
# 4. 補助関数
# =========================
def calculate_dynamic_lot(entry_price, stop_price):
    if stop_price == 0 or entry_price == stop_price: return 0.1
    pips_diff = abs(entry_price - stop_price) / PIPS_UNIT
    if pips_diff < 0.1: return 0.1
    lot = RISK_PER_TRADE / (pips_diff * ONE_LOT_PIPS_VALUE)
    return max(0.01, round(lot, 2))

def check_stop_loss():
    global trade, balance, stop_lines_data
    if not trade or not stop_lines_data: return
    curr = df_h1.iloc[idx_h1]
    for p, c, ls in stop_lines_data:
        is_hit = (trade["side"]=="BUY" and curr["Low"] <= p) or (trade["side"]=="SELL" and curr["High"] >= p)
        if is_hit:
            pips = (p - trade["price"]) / PIPS_UNIT if trade["side"]=="BUY" else (trade["price"] - p) / PIPS_UNIT
            profit = pips * ONE_LOT_PIPS_VALUE * trade["lot"]
            history.append({**trade, "exit_p": p, "exit_time": curr.name, "pips": pips, "profit": profit})
            balance += profit
            markers.append((curr.name, p, "x", "black"))
            trade = None; stop_lines_data.clear(); break

def get_time_from_x(ax, xdata):
    if xdata is None: return None
    end_idx = idx_h1 + view_offset
    if ax == ax_h1: data, start = df_h1, max(0, end_idx - WINDOW_H1)
    elif ax == ax_d1:
        d1_past = df_d1[df_d1.index <= df_h1.index[end_idx]]
        data, start = df_d1, max(0, len(d1_past) - WINDOW_D1)
    elif ax == ax_mn:
        mn_past = df_mn[df_mn.index <= df_h1.index[end_idx]]
        data, start = df_mn, max(0, len(mn_past) - WINDOW_MN)
    else: return None
    idx = max(0, min(int(round(xdata)), len(data.iloc[start:end_idx+1]) - 1))
    return data.iloc[start + idx].name

# =========================
# 5. 描画
# =========================
def redraw():
    global balance, current_lot, idx_h1, view_offset
    try:
        end_idx = max(WINDOW_H1, min(len(df_h1)-1, idx_h1 + view_offset))
        h1_data = df_h1.iloc[end_idx - WINDOW_H1 : end_idx + 1]
        v_times = h1_data.index.tolist()
        curr_time = v_times[-1]
        v_price = h1_data.iloc[-1]["Close"]

        ax_mn.clear(); ax_d1.clear(); ax_h1.clear(); ax_info.clear()
        
        # 上位足フィルタリング
        d1_data = df_d1[df_d1.index <= curr_time].iloc[-WINDOW_D1:]
        mn_data = df_mn[df_mn.index <= curr_time].iloc[-WINDOW_MN:]

        mpf.plot(h1_data, ax=ax_h1, type="candle", style="yahoo")
        mpf.plot(d1_data, ax=ax_d1, type="candle", style="yahoo")
        mpf.plot(mn_data, ax=ax_mn, type="candle", style="yahoo")

        # ライン描画
        for ax, times in [(ax_h1, v_times), (ax_d1, d1_data.index.tolist()), (ax_mn, mn_data.index.tolist())]:
            for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
                is_s = i >= len(hlines_data)
                sel = selected_obj == ('stop' if is_s else 'hline', i - len(hlines_data) if is_s else i)
                ax.add_line(Line2D([0, 1], [p, p], transform=ax.get_yaxis_transform(), color="orange" if sel else c, linestyle=ls, linewidth=2 if sel else 1))
            
            # 矩形
            disp_rects = rects_data + ([temp_rect] if temp_rect else [])
            for i, r in enumerate(disp_rects):
                is_p = temp_rect and i == len(disp_rects)-1
                if min(r[0], r[1]) <= times[-1] and max(r[0], r[1]) >= times[0]:
                    x1 = times.index(r[0]) if r[0] in times else (0 if r[0]<times[0] else len(times)-1)
                    x2 = times.index(r[1]) if r[1] in times else (0 if r[1]<times[0] else len(times)-1)
                    ax.add_patch(Rectangle((min(x1, x2), min(r[2], r[3])), abs(x1-x2), abs(r[2]-r[3]), fill=False, edgecolor="cyan" if is_p else "green", linestyle="--" if is_p else "-"))

        for mt, mp, ms, mc in markers:
            if mt in v_times: ax_h1.scatter(v_times.index(mt), mp, marker=ms, color=mc, s=100, zorder=5)

        # 情報パネル
        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        planned_lot = calculate_dynamic_lot(v_price, sl_p) if sl_p > 0 else 0.1
        ax_info.axis("off")
        txt = f"BALANCE : {balance:,.0f} JPY\nRISK    : {RISK_PER_TRADE:,.0f}\nNEXT LOT: {planned_lot:.2f}\nTRADES  : {len(history)}\n" + "-"*15 + "\n"
        for h in history[-5:]: txt += f"{h['side']} {h['lot']:.2f}L {h['profit']:+,.0f}\n"
        ax_info.text(0, 1, txt, transform=ax_info.transAxes, verticalalignment="top", fontsize=9, fontfamily="monospace")
        fig.canvas.draw_idle()
    except Exception as e: print(f"描画エラー: {e}")

# =========================
# 6. イベント
# =========================
def on_key_press(e):
    global idx_h1, view_offset, selected_obj
    pressed.add(e.key)
    if e.key == "t":
        target = input("Jump to (YYYY-MM-DD HH:MM): ")
        try:
            new_idx = df_h1.index.get_indexer([pd.to_datetime(target)], method='pad')[0]
            if new_idx != -1: idx_h1, view_offset = new_idx, 0
        except: print("Invalid date")
    if e.key in ["delete", "backspace"] and selected_obj:
        t, i = selected_obj
        if t == 'hline': hlines_data.pop(i)
        elif t == 'stop': stop_lines_data.pop(i)
        elif t == 'rect': rects_data.pop(i)
        selected_obj = None
    step = 10 if "control" in pressed else 1
    if e.key == "right":
        if view_offset < 0: view_offset = min(0, view_offset + step)
        else: idx_h1 = min(len(df_h1)-1, idx_h1 + step); check_stop_loss()
    elif e.key == "left":
        if "shift" in pressed: idx_h1 = max(WINDOW_H1, idx_h1 - step)
        else: view_offset -= step
    redraw()

def on_button_press(e):
    global trade, rect_start, selected_obj, dragging, balance, stop_lines_data
    if not e.inaxes or e.xdata is None: return
    t_c = get_time_from_x(e.inaxes, e.xdata)
    curr_idx = max(0, min(len(df_h1)-1, idx_h1 + view_offset))
    v_time, v_price = df_h1.index[curr_idx], df_h1.iloc[curr_idx]["Close"]

    if e.button == 1 and not any(k in pressed for k in ["control", "shift", "b", "v", "c", "h"]):
        selected_obj = None
        yr = e.inaxes.get_ylim()[1] - e.inaxes.get_ylim()[0]
        for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
            if abs(p - e.ydata) < yr * 0.03:
                is_s = i >= len(hlines_data)
                selected_obj = ('stop' if is_s else 'hline', i - len(hlines_data) if is_s else i); break
        if not selected_obj:
            for i, r in enumerate(rects_data):
                if min(r[0], r[1]) <= t_c <= max(r[0], r[1]) and min(r[2], r[3]) <= e.ydata <= max(r[2], r[3]):
                    selected_obj = ('rect', i); break
        if selected_obj: dragging = True
        redraw(); return

    if e.button == 3: rect_start = (t_c, e.ydata); return
    if e.button == 1:
        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        if "b" in pressed or "v" in pressed:
            side = "BUY" if "b" in pressed else "SELL"
            lot = calculate_dynamic_lot(v_price, sl_p)
            trade = {"side": side, "price": v_price, "time": v_time, "lot": lot, "sl": sl_p, "tp": 0, "symbol": "USDJPY"}
            markers.append((v_time, v_price, "^" if side=="BUY" else "v", "blue" if side=="BUY" else "red"))
        elif "c" in pressed and trade:
            pips = (v_price - trade["price"]) / PIPS_UNIT if trade["side"]=="BUY" else (trade["price"] - v_price) / PIPS_UNIT
            profit = pips * ONE_LOT_PIPS_VALUE * trade["lot"]
            history.append({**trade, "exit_p": v_price, "exit_time": v_time, "pips": pips, "profit": profit})
            balance += profit; markers.append((v_time, v_price, "x", "black")); trade = None; stop_lines_data.clear()
        elif "h" in pressed: hlines_data.append([e.ydata, "blue", "-"])
        elif "shift" in pressed: stop_lines_data.clear(); stop_lines_data.append([e.ydata, "red", "--"])
        redraw()

def on_motion(e):
    global dragging, temp_rect
    if not e.inaxes or e.xdata is None: return
    t_curr = get_time_from_x(e.inaxes, e.xdata)
    if rect_start: temp_rect = [rect_start[0], t_curr, rect_start[1], e.ydata]; redraw(); return
    if dragging and selected_obj:
        t, i = selected_obj
        if t in ['hline', 'stop']: (hlines_data if t=='hline' else stop_lines_data)[i][0] = e.ydata
        redraw()

def on_release(e):
    global rect_start, dragging, temp_rect; dragging = False
    if e.button == 3 and rect_start:
        if temp_rect: rects_data.append(temp_rect)
        rect_start = temp_rect = None; redraw()

# =========================
# 7. 統計・CSV保存
# =========================
def show_statistics():
    if not history: return None
    df = pd.DataFrame(history)
    print("\n" + "★" * 20 + " 最終統計レポート " + "★" * 20)
    
    def analyze(data, label):
        if data.empty: return {}
        pips, wins, losses = data['pips'], data[data['pips']>0]['pips'], data[data['pips']<=0]['pips']
        
        # 勝率の計算
        win_rate = (len(wins) / len(data)) * 100
        
        # 連勝・連敗履歴
        res = (data['pips'] > 0).astype(int).tolist()
        w_s, l_s, cw, cl = [], [], 0, 0
        for r in res:
            if r==1: cw+=1; (l_s.append(cl) if cl>=2 else None); cl=0
            else: cl+=1; (w_s.append(cw) if cw>=2 else None); cw=0
        (w_s.append(cw) if cw>=2 else None); (l_s.append(cl) if cl>=2 else None)
        
        pf = abs(wins.sum()/losses.sum()) if not losses.empty else float('inf')
        
        print(f"\n--- {label} ---")
        print(f"トレード数: {len(data)} | 勝率: {win_rate:.1f}% | PF: {pf:.2f}")
        
        return {
            "Total_Pips": round(pips.sum(), 1),
            "Win_Rate": round(win_rate, 1), # ここを確実に追加
            "PF": round(pf, 2),
            "Win_Streaks": str(w_s),
            "Loss_Streaks": str(l_s),
            "Start_Time": data['time'].min(),
            "End_Time": data['exit_time'].max(),
            "Total_Trades": len(data)
        }

    # 総合(TOTAL)の結果をベースにする
    stats = analyze(df, "総合 (TOTAL)")
    analyze(df[df['side']=='BUY'], "買い (BUY)")
    analyze(df[df['side']=='SELL'], "売り (SELL)")
    return stats


def save_csv_files(stats, history_data):
    if not stats: return
    
    execution_real_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_profit_jpy = sum(h['profit'] for h in history_data)
    final_balance = INITIAL_BALANCE + total_profit_jpy
    
    # リスクリワード計算
    wins = [h['pips'] for h in history_data if h['pips'] > 0]
    losses = [abs(h['pips']) for h in history_data if h['pips'] <= 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    rr_ratio = round(avg_win / avg_loss, 2) if avg_loss != 0 else 0

    # CSV書き込み用データ
    summary_data = {
        "Execution_RealTime": execution_real_time,
        "Start_Trade_Time": stats.get("Start_Time"),
        "End_Trade_Time": stats.get("End_Time"),
        "Total_Trades": stats.get("Total_Trades"),
        "Total_Pips": stats.get("Total_Pips"),
        "Profit_JPY": round(total_profit_jpy, 0),
        "Final_Balance": round(final_balance, 0),
        "Win_Rate": stats.get("Win_Rate"), # ← これで書き込まれるようになります
        "Risk_Reward": rr_ratio,
        "PF": stats.get("PF"),
        "Win_Streaks": stats.get("Win_Streaks"),
        "Loss_Streaks": stats.get("Loss_Streaks")
    }

    summary_file = "trading_summary.csv"
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(summary_file, mode='a', index=False, 
                      header=not os.path.exists(summary_file), encoding='utf-8-sig')
    
    # (詳細ログの保存部分は変更なし)
    # ... (以下省略)
    # 5. 全トレード詳細の保存 (trading_details_log.csv 用)
    details = []
    for h in history_data:
        details.append({
            "Execution_RealTime": execution_real_time,
            "symbol": h.get('symbol', 'Unknown'),
            "Type": h['side'],
            "lots": h['lot'],
            "OpenTime": h['time'],
            "Close Time": h['exit_time'],
            "Open Price": h['price'],
            "Close Price": h['exit_p'],
            "Profit_JPY": round(h['profit'], 0),
            "Pips": round(h['pips'], 1),
            "S/L": h['sl'],
            "T/P": h['tp']
        })
    
    detail_file = "trading_details_log.csv"
    detail_df = pd.DataFrame(details)
    
    detail_df.to_csv(detail_file, mode='a', index=False, 
                     header=not os.path.exists(detail_file), encoding='utf-8-sig')
    
    print(f"\n" + "="*30)
    print(f">> 保存完了 (追記モード)")
    print(f">> 今回の純損益: {total_profit_jpy:+,.0f} JPY")
    print(f">> リスクリワード: {rr_ratio}")
    print(f">> 最終残高: {final_balance:,.0f} JPY")
    print("="*30)
    
def on_close(event):
    if not history: print("トレードなし。"); return
    root = tk.Tk(); root.withdraw()
    if messagebox.askyesno("整理", "トレードを除外しますか？"):
        print(pd.DataFrame(history)[['side','time','pips']])
        target = input("除外番号(カンマ区切り): ")
        try:
            for idx in sorted([int(x)-1 for x in target.split(",") if x.strip()], reverse=True): history.pop(idx)
        except: pass
    stats = show_statistics()
    if stats and messagebox.askyesno("保存", "CSVに記録しますか？"): save_csv_files(stats, history)
    root.destroy()

# =========================
# 8. 実行
# =========================
fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 2], width_ratios=[5, 1], hspace=0.3, wspace=0.1)
ax_mn, ax_d1, ax_h1, ax_info = fig.add_subplot(gs[0,0]), fig.add_subplot(gs[1,0]), fig.add_subplot(gs[2,0]), fig.add_subplot(gs[:,1])

fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", lambda e: pressed.discard(e.key))
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("motion_notify_event", on_motion)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("close_event", on_close)

redraw()
plt.show()