import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import datetime

# =========================
# 1. 設定・パス
# =========================
MN_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv"
D1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/B_data.csv"
H1_PATH = r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"

WINDOW_H1, WINDOW_D1, WINDOW_MN = 200, 100, 60
INITIAL_BALANCE = 1500000.0
RISK_PER_TRADE = 10000.0
# ドラッグ中の軸固定用変数
fixed_ylim = None
# =========================
# 2. 起動時設定ダイアログ
# =========================
class StartupSettings:
    def __init__(self, initial_dt):
        self.root = tk.Tk()
        self.root.title("リプレイ設定")
        self.root.attributes("-topmost", True)
        
        self.dt_result = initial_dt
        self.lot_mode = "AUTO"
        self.fixed_lot = 0.1
        self.confirmed = False

        # --- 日時選択セクション ---
        self.vals = {"Year": initial_dt.year, "Month": initial_dt.month, "Day": initial_dt.day, "Hour": initial_dt.hour}
        dt_frame = ttk.LabelFrame(self.root, text="開始日時 (マウスホイールで操作)", padding=10)
        dt_frame.pack(padx=10, pady=5, fill="x")
        
        self.labels = {}
        for i, col in enumerate(["Year", "Month", "Day", "Hour"]):
            f = ttk.Frame(dt_frame)
            f.grid(row=0, column=i, padx=5)
            ttk.Label(f, text=col).pack()
            lbl = ttk.Label(f, text=str(self.vals[col]), font=("Arial", 14, "bold"))
            lbl.pack()
            self.labels[col] = lbl
            lbl.bind("<MouseWheel>", lambda e, c=col: self.on_wheel(e, c))

        # --- ロットモード設定セクション ---
        lot_frame = ttk.LabelFrame(self.root, text="ロット設定 (トレード中変更不可)", padding=10)
        lot_frame.pack(padx=10, pady=5, fill="x")
        
        self.mode_var = tk.StringVar(value="FIX")
        ttk.Radiobutton(lot_frame, text="変動ロット (損切り幅から算出)", variable=self.mode_var, value="AUTO").pack(anchor="w")
        ttk.Radiobutton(lot_frame, text="固定ロット", variable=self.mode_var, value="FIX").pack(anchor="w")
        
        ttk.Label(lot_frame, text="固定ロット数:").pack(side="left")
        self.lot_entry = ttk.Entry(lot_frame, width=10)
        self.lot_entry.insert(0, "0.1")
        self.lot_entry.pack(side="left", padx=5)

        ttk.Button(self.root, text="リプレイ開始", command=self.confirm).pack(pady=10)
        self.root.mainloop()

    def on_wheel(self, event, col):
        delta = 1 if event.delta > 0 else -1
        if col == "Year": self.vals[col] += delta
        elif col == "Month": self.vals[col] = (self.vals[col] + delta - 1) % 12 + 1
        elif col == "Day": self.vals[col] = (self.vals[col] + delta - 1) % 31 + 1
        elif col == "Hour": self.vals[col] = (self.vals[col] + delta) % 24
        self.labels[col].config(text=str(self.vals[col]))

    def confirm(self):
        try:
            self.dt_result = pd.Timestamp(year=self.vals["Year"], month=self.vals["Month"], day=self.vals["Day"], hour=self.vals["Hour"])
            self.lot_mode = self.mode_var.get()
            self.fixed_lot = float(self.lot_entry.get())
            self.confirmed = True
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"設定が正しくありません: {e}")

# =========================
# 3. データ読み込み
# =========================
def load_csv(path):
    if not os.path.exists(path): raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path)
    df.columns = [c.capitalize() for c in df.columns]
    temp = df.copy()
    if "Day" not in df.columns: temp["Day"] = 1
    if "Hour" not in df.columns: temp["Hour"] = 0
    df["Date"] = pd.to_datetime(temp[["Year", "Month", "Day", "Hour"]])
    df.set_index("Date", inplace=True)
    return df[["Open", "High", "Low", "Close", "Volume"]]

def get_pair_settings(df):
    sample = df['Close'].iloc[0]
    return (0.01, 1000) if sample > 50 else (0.0001, 1500)

try:
    df_mn, df_d1, df_h1 = load_csv(MN_PATH), load_csv(D1_PATH), load_csv(H1_PATH)
    PIPS_UNIT, ONE_LOT_PIPS_VALUE = get_pair_settings(df_h1)
    
    # 起動時設定の呼び出し
    settings = StartupSettings(df_h1.index[WINDOW_H1 + 50])
    if not settings.confirmed: exit()
    
    idx_h1 = df_h1.index.get_indexer([settings.dt_result], method='pad')[0]
    idx_h1 = max(WINDOW_H1, idx_h1)
    lot_mode = settings.lot_mode
    fixed_lot_size = settings.fixed_lot
except Exception as e:
    print(f"初期化エラー: {e}"); exit()

# 状態管理
balance = INITIAL_BALANCE
is_autoplay = False
autoplay_speed = 0.5
trade = None
hlines_data, stop_lines_data = [], []
markers, history = [], []
pressed = set()
selected_obj, dragging = None, False

# =========================
# 4. 判定・操作ロジック
# =========================
def check_stop_loss():
    global trade, balance, stop_lines_data, markers
    if not trade or not stop_lines_data: return False
    curr = df_h1.iloc[idx_h1]
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

def redraw():
    global balance, idx_h1
    try:
        h1_data = df_h1.iloc[idx_h1 - WINDOW_H1 : idx_h1 + 1]
        v_times = h1_data.index.tolist()
        current_time = v_times[-1]
        v_price = h1_data.iloc[-1]["Close"]
        
        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        d1_visible = df_d1[df_d1.index < day_start].iloc[-WINDOW_D1:]
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mn_visible = df_mn[df_mn.index < month_start].iloc[-WINDOW_MN:]
        
        ax_mn.clear(); ax_d1.clear(); ax_h1.clear(); ax_info.clear()
        mpf.plot(h1_data, ax=ax_h1, type="candle", style="yahoo")
        if not d1_visible.empty: mpf.plot(d1_visible, ax=ax_d1, type="candle", style="yahoo")
        if not mn_visible.empty: mpf.plot(mn_visible, ax=ax_mn, type="candle", style="yahoo")

        for ax in [ax_h1, ax_d1, ax_mn]:
            for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
                sel = selected_obj == ('stop' if i >= len(hlines_data) else 'hline', i if i < len(hlines_data) else i - len(hlines_data))
                ax.add_line(Line2D([0, 1], [p, p], transform=ax.get_yaxis_transform(), color="orange" if sel else c, linestyle=ls, linewidth=2 if sel else 1))
        
        for item in markers:
            mt, mp, ms, mc = item[0], item[1], item[2], item[3]
            ma = item[4] if len(item) > 4 else 1.0
            if mt in v_times:
                ax_h1.scatter(v_times.index(mt), mp, marker=ms, color=mc, s=80, alpha=ma, zorder=1)

        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        current_lot = max(0.01, round(RISK_PER_TRADE / (abs(v_price - sl_p)/PIPS_UNIT * ONE_LOT_PIPS_VALUE), 2)) if lot_mode == "AUTO" and sl_p else (fixed_lot_size if lot_mode == "FIX" else 0.1)

        total_pips = round(sum(h['pips'] for h in history), 1)
        ax_info.axis("off")
        info = f"AUTO: {'ON' if is_autoplay else 'OFF'}\nBAL : {balance:,.0f}\nPIPS: {total_pips:>6}p\nLOT : {current_lot:.2f} ({lot_mode})\nTRADES: {len(history)}\n" + "-"*15 + "\n"
        for h in history[-8:]: 
            info += f"{h['side']} {h['lot']:.2f}L {h['pips']:>+5.1f}p ({h['profit']:+,.0f})\n"
        
        ax_info.text(0, 1, info, transform=ax_info.transAxes, verticalalignment="top", fontsize=8, fontfamily="monospace")
        fig.canvas.draw_idle()
    except Exception as e: print(f"描画エラー: {e}")

# =========================
# 5. イベント処理
# =========================
def on_key_press(e):
    global idx_h1, is_autoplay, autoplay_speed, selected_obj
    pressed.add(e.key)
    step = 10 if "control" in pressed else 1
    
    if e.key == "a": is_autoplay = not is_autoplay
    elif e.key == " ": execute_skip()
    elif e.key == "t":
        t_str = simpledialog.askstring("Jump", "時刻入力 (YYYY-MM-DD HH:MM):")
        if t_str:
            try:
                target_dt = pd.to_datetime(t_str)
                new_idx = df_h1.index.get_indexer([target_dt], method='pad')[0]
                if new_idx != -1 and new_idx > idx_h1:
                    while idx_h1 < new_idx:
                        idx_h1 += 1
                        if check_stop_loss(): break
                    redraw()
                elif new_idx <= idx_h1:
                    idx_h1 = max(WINDOW_H1, new_idx)
                    redraw()
            except Exception as ex: print(f"Jump Error: {ex}")
    elif e.key == "right":
        if idx_h1 < len(df_h1)-1: 
            idx_h1 += step
            check_stop_loss()
    elif e.key == "left":
        idx_h1 = max(WINDOW_H1, idx_h1 - step)
    elif e.key in ["delete", "backspace"] and selected_obj:
        t, i = selected_obj
        if t == 'hline': hlines_data.pop(i)
        elif t == 'stop': stop_lines_data.pop(i)
        selected_obj = None
    redraw()
def on_motion(e):
    global dragging, selected_obj, fixed_ylim
    if dragging and selected_obj and e.ydata and e.inaxes:
        # ドラッグ中は記憶した範囲を強制適用して画面の揺れを防ぐ
        e.inaxes.set_ylim(fixed_ylim)
        target_list = hlines_data if selected_obj[0] == 'hline' else stop_lines_data
        target_list[selected_obj[1]][0] = e.ydata
        redraw()
def on_button_press(e):
    global trade, selected_obj, dragging, balance, fixed_ylim
    if not e.inaxes or e.xdata is None: return
    
    # ボタンを押した瞬間の表示範囲を記憶（軸の変動を防止）
    fixed_ylim = e.inaxes.get_ylim()
    
    curr_t, curr_p = df_h1.index[idx_h1], df_h1.iloc[idx_h1]["Close"]
    
    # 既存ラインの選択判定
    if e.button == 1 and not any(k in pressed for k in ["b","v","c","h","shift"]):
        selected_obj = None
        yr = fixed_ylim[1] - fixed_ylim[0]
        for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
            if abs(p - e.ydata) < yr * 0.03:
                selected_obj = ('stop' if i >= len(hlines_data) else 'hline', 
                                i if i < len(hlines_data) else i - len(hlines_data))
                dragging = True; break
        redraw(); return

    # 新規ライン描画（HキーやShiftキー時）
    if e.button == 1:
        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        entry_lot = max(0.01, round(RISK_PER_TRADE / (abs(curr_p - sl_p)/PIPS_UNIT * ONE_LOT_PIPS_VALUE), 2)) if lot_mode == "AUTO" and sl_p else (fixed_lot_size if lot_mode == "FIX" else 0.1)

        if "b" in pressed or "v" in pressed:
            side = "BUY" if "b" in pressed else "SELL"
            trade = {"side": side, "price": curr_p, "time": curr_t, "lot": entry_lot, "sl": sl_p, "tp": 0, "symbol": "FX"}
            markers.append((curr_t, curr_p, "^" if side=="BUY" else "v", "blue" if side=="BUY" else "red", 0.6))
        elif "c" in pressed and trade:
            pips = round((curr_p - trade["price"]) / PIPS_UNIT if trade["side"]=="BUY" else (trade["price"] - curr_p) / PIPS_UNIT, 1)
            profit = round(pips * ONE_LOT_PIPS_VALUE * trade["lot"], 0)
            history.append({**trade, "exit_p": curr_p, "exit_time": curr_t, "pips": pips, "profit": profit})
            balance += profit; markers.append((curr_t, curr_p, "x", "black", 0.3)); trade = None; stop_lines_data.clear()
        elif "h" in pressed: hlines_data.append([e.ydata, "blue", "-"])
        elif "shift" in pressed: stop_lines_data.clear(); stop_lines_data.append([e.ydata, "red", "--"])
        redraw()
def on_button_release(e):
    global dragging, fixed_ylim
    dragging = False
    fixed_ylim = None # 解放
def execute_skip():
    global idx_h1, is_autoplay
    is_autoplay = False
    print(">>> スキップ中...")
    while idx_h1 < len(df_h1) - 1:
        idx_h1 += 1
        if check_stop_loss(): break
        curr = df_h1.iloc[idx_h1]
        if any(curr["Low"] <= p <= curr["High"] for p, c, ls in hlines_data): break
    redraw()
    
def save_csv_files():
    if not history: return
    root = tk.Tk(); root.withdraw()
    f_path = filedialog.askopenfilename(title="追記するCSVを選択", filetypes=[("CSV","*.csv")])
    if not f_path:
        f_path = filedialog.asksaveasfilename(title="新規保存名", filetypes=[("CSV","*.csv")], defaultextension=".csv", initialfile="trading_summary.csv")
    if not f_path: return

    base = os.path.splitext(f_path)[0].replace("_summary","").replace("_details","")
    summary_file, detail_file = f"{base}_summary.csv", f"{base}_details.csv"
    df = pd.DataFrame(history)
    wins_df = df[df['profit'] > 0]
    losses_df = df[df['profit'] <= 0]
    pf = round(wins_df['profit'].sum() / abs(losses_df['profit'].sum()), 2) if not losses_df.empty else 0
    rr = round(wins_df['pips'].mean() / abs(losses_df['pips'].mean()), 2) if not losses_df.empty else 0
    wl = [1 if p > 0 else 0 for p in df['profit']]
    mw, ml, cw, cl = 0, 0, 0, 0
    for v in wl:
        if v == 1: cw += 1; cl = 0
        else: cl += 1; cw = 0
        mw, ml = max(mw, cw), max(ml, cl)

    summary = {
        "Execution_RealTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Start_Trade_Time": df['time'].min(),
        "End_Trade_Time": df['exit_time'].max(),
        "Total_Trades": len(df),
        "Total_Pips": round(df['pips'].sum(), 1),
        "Profit_JPY": round(df['profit'].sum(), 0),
        "Final_Balance": round(balance, 0),
        "Win_Rate": round(len(wins_df) / len(df) * 100, 1),
        "Risk_Reward": rr, "PF": pf, "Win_Streaks": mw, "Loss_Streaks": ml
    }
    pd.DataFrame([summary]).to_csv(summary_file, mode='a', index=False, header=not os.path.exists(summary_file), encoding='utf-8-sig')
    df.to_csv(detail_file, mode='a', index=False, header=not os.path.exists(detail_file), encoding='utf-8-sig')
    messagebox.showinfo("完了", f"保存完了: Pips {summary['Total_Pips']}")

def on_close(event):
    if history and messagebox.askyesno("保存", "CSVに記録しますか？"): save_csv_files()
    plt.close()

# =========================
# 7. 実行
# =========================
fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 2], width_ratios=[5, 1], hspace=0.3, wspace=0.1)
ax_mn, ax_d1, ax_h1, ax_info = fig.add_subplot(gs[0,0]), fig.add_subplot(gs[1,0]), fig.add_subplot(gs[2,0]), fig.add_subplot(gs[:,1])
fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", lambda e: pressed.discard(e.key))
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("motion_notify_event", lambda e: (dragging and selected_obj and e.ydata and (globals().update(dragging=True) or ((hlines_data[selected_obj[1]] if selected_obj[0]=='hline' else stop_lines_data[selected_obj[1]]).__setitem__(0, e.ydata)) or redraw())))
fig.canvas.mpl_connect("button_release_event", lambda e: globals().update(dragging=False))
fig.canvas.mpl_connect("close_event", on_close)

timer = fig.canvas.new_timer(interval=int(autoplay_speed * 1000))
timer.add_callback(lambda: (idx_h1 < len(df_h1)-1 and is_autoplay and (globals().update(idx_h1=idx_h1+1) or check_stop_loss() or redraw())))
timer.start()

redraw()
plt.show()