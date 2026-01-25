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
PATHS = {
    "MN":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv",
    "D1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/B_data.csv",
    "H1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv",
    "M15": r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/F_data.csv",
    "M5":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/G.csv",
    "M1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/H_data.csv"
}

WINDOW_SIZES = {"MN": 60, "D1": 100, "H1": 150, "M15": 200, "M5": 250, "M1": 300}
VIEW_MAP = {"1": "H1", "2": "D1", "3": "MN", "4": "M15", "5": "M5", "6": "M1"}
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
    df = pd.read_csv(path)
    df.columns = [c.capitalize() for c in df.columns]
    t = df.copy()
    t["Day"] = t.get("Day", 1)
    t["Hour"] = t.get("Hour", 0)
    t["Minute"] = t.get("Minute", 0)
    df["Date"] = pd.to_datetime(t[["Year", "Month", "Day", "Hour", "Minute"]])
    
    # --- ここを追加：日時の重複を削除 ---
    df = df.drop_duplicates(subset="Date", keep="last")
    # ----------------------------------
    
    df.set_index("Date", inplace=True)
    return df[["Open", "High", "Low", "Close"]]
def get_pair_settings(df):
    sample = df['Close'].iloc[0]
    return (0.01, 1000) if sample > 50 else (0.0001, 1500)

DFS = {}
try:
    for tf, path in PATHS.items():
        if os.path.exists(path):
            temp_df = load_csv(path)
            # 念のため日時順に並び替え
            DFS[tf] = temp_df.sort_index()
    
    # M1を基準足にする
    df_base = DFS["M1"]
    
    # 価格単位の判定
    PIPS_UNIT, ONE_LOT_PIPS_VALUE = (0.01, 1000) if df_base['Close'].iloc[0] > 50 else (0.0001, 1500)
    
    # 最初の表示位置を決定
    # WINDOW_SIZES["M1"] 分の余白を持たせて開始
    start_margin = WINDOW_SIZES["M1"] + 50
    st = StartupSettings(df_base.index[start_margin])
    
    if not st.confirmed: exit()
    
    # 指定した日時に最も近いインデックスを探す（method='pad'で過去方向の近似値）
    idx_base = df_base.index.get_indexer([st.dt_result], method='pad')[0]
    
    # 範囲外エラー対策
    idx_base = max(start_margin, idx_base)
    
    current_view = "H1"
except Exception as e:
    print(f"Init Error: {e}")
    import traceback
    traceback.print_exc() # 詳細なエラー場所を表示
    exit()
# 状態管理
balance = INITIAL_BALANCE
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
# =========================
# 4. 判定・操作ロジック
# =========================
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

def redraw():
    global balance, idx_base, current_view, fibo_mode
    try:
        current_time = df_base.index[idx_base]
        v_price = df_base.iloc[idx_base]["Close"]
        
        # 1. チャートデータの切り出し
        full_df = DFS[current_view]
        plot_df = full_df[full_df.index <= current_time].iloc[-WINDOW_SIZES[current_view]:]

        ax_main.clear(); ax_info.clear(); ax_info.axis("off")
        if not plot_df.empty:
            mpf.plot(plot_df, ax=ax_main, type="candle", style="yahoo")
            ax_main.set_title(f"View: {current_view} | {current_time}", fontsize=10)
        
        # 2. メインチャート描画
        title_str = f"{current_view} Chart | {current_time}"
        if not plot_df.empty:
            mpf.plot(plot_df, ax=ax_main, type="candle", style="yahoo")
            ax_main.set_title(title_str)

        # 3. フィボナッチ描画
        # (前回のフィボナッチ描画コードをここに配置。ax_h1 を ax_main に書き換え)
        for f in retracements:
            p1, p2 = f['p1'], f['p2']
            diff = p2 - p1
            for lv in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618]:
                val = p1 + diff * lv
                ax_main.add_line(Line2D([0, 1], [val, val], transform=ax_main.get_yaxis_transform(), color="darkgoldenrod", alpha=0.4, linestyle="--", linewidth=0.8))
        
        # 4. 水平線・損切り線の描画
        for i, (p, c, ls) in enumerate(hlines_data + stop_lines_data):
            sel = selected_obj == ('stop' if i >= len(hlines_data) else 'hline', i if i < len(hlines_data) else i - len(hlines_data))
            ax_main.add_line(Line2D([0, 1], [p, p], transform=ax_main.get_yaxis_transform(), color="orange" if sel else c, linestyle=ls, linewidth=2 if sel else 1))

        # 5. 売買マーカー（表示中の足の時間軸に含まれる場合のみ表示）
        plot_times = plot_df.index.tolist()
        for mt, mp, ms, mc, ma in markers:
            if mt in plot_times:
                ax_main.scatter(plot_times.index(mt), mp, marker=ms, color=mc, s=100, alpha=ma, zorder=1)

        # 6. 情報パネル（前回修正した info の作成順序を守る）
        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        current_lot = max(0.01, round(RISK_PER_TRADE / (max(0.1, abs(v_price - sl_p))/PIPS_UNIT * ONE_LOT_PIPS_VALUE), 2)) if lot_mode=="AUTO" and sl_p else fixed_lot_size
        total_pips = round(sum(h['pips'] for h in history), 1)

        info = f"VIEW: {current_view}\n"
        info += f"AUTO: {'ON' if is_autoplay else 'OFF'}\n"
        if fibo_mode: info += f"MODE: {fibo_mode} ({len(fibo_points)}pt)\n"
        info += f"BAL : {balance:,.0f}\n"
        info += f"PIPS: {total_pips:>6}p\n"
        info += f"LOT : {current_lot:.2f} ({lot_mode})\n"
        info += f"TRADES: {len(history)}\n" + "-"*15 + "\n"
        for h in history[-8:]: info += f"{h['side']} {h['lot']:.2f}L {h['pips']:>+5.1f}p\n"
        ax_info.text(0, 1, info, transform=ax_info.transAxes, verticalalignment="top", fontsize=9, fontfamily="monospace")
        
        fig.canvas.draw_idle()
    except Exception as e: print(f"描画エラー: {e}")
# =========================
# 5. イベント処理
# =========================
def on_key_press(e):
    global idx_base, is_autoplay, current_view, fibo_mode, fibo_points    
    pressed.add(e.key)
    step = 10 if "control" in pressed else 1
    
    if e.key == "a": is_autoplay = not is_autoplay
    # 時間足切り替え（追加）
    elif e.key == "1": 
        current_view = "H1"
        print(">> 表示: H1 (1時間足)")
    elif e.key == "2": 
        current_view = "D1"
        print(">> 表示: D1 (日足)")
    elif e.key == "3": 
        current_view = "MN"
        print(">> 表示: MN (月足)")
    elif e.key == " ": execute_skip()
    elif e.key == "f": # リトレースメント開始
        fibo_mode, fibo_points = "RETRACE", []
        print(">> フィボナッチ・リトレースメント: 2点クリックしてください")
    elif e.key == "e": # エクステンション開始
        fibo_mode, fibo_points = "EXT", []
        print(">> フィボナッチ・エクステンション: 3点クリックしてください")
    elif e.key == "x": # フィボ全消去
        retracements.clear(); extensions.clear(); fibo_mode = None
        print(">> フィボナッチをすべて削除しました")
    elif e.key == "t":
        t_str = simpledialog.askstring("Jump", "時刻入力 (YYYY-MM-DD HH:MM):")
        if t_str:
            try:
                target_dt = pd.to_datetime(t_str)
                new_idx = df_base.index.get_indexer([target_dt], method='pad')[0]
                if new_idx != -1 and new_idx > idx_base:
                    while idx_base < new_idx:
                        idx_base += 1
                        if check_stop_loss(): break
                    redraw()
                elif new_idx <= idx_base:
                    idx_base = max(WINDOW_SIZES["M1"], new_idx)
                    redraw()
            except Exception as ex: print(f"Jump Error: {ex}")
    elif e.key == "right":
        if idx_base < len(df_base)-1: 
            idx_base += (60 if "control" in pressed else 1) # 1分 or 60分(1時間)送り
            check_stop_loss()
    elif e.key == "left":
        idx_base = max(WINDOW_SIZES["M1"], idx_base - step)
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
    global dragging, selected_obj, fixed_ylim, fibo_points, fibo_mode, trade, balance    
    if not e.inaxes or e.xdata is None: return
    fixed_ylim = e.inaxes.get_ylim()
    cp, ct = df_base.iloc[idx_base]["Close"], df_base.index[idx_base]    
    # フィボナッチ打点
    if fibo_mode:
        fibo_points.append(e.ydata)
        if fibo_mode == "RETRACE" and len(fibo_points) == 2:
            retracements.append({'p1': fibo_points[0], 'p2': fibo_points[1]}); fibo_mode, fibo_points = None, []
        elif fibo_mode == "EXT" and len(fibo_points) == 3:
            # ここ！ extensions.appen になっていたのを append に修正
            extensions.append({'p1': fibo_points[0], 'p2': fibo_points[1], 'p3': fibo_points[2]})
            fibo_mode, fibo_points = None, []
        redraw()
        return # フィボナッチ操作時は他の処理（エントリー等）をスキップ
    # ボタンを押した瞬間の表示範囲を記憶（軸の変動を防止）
    fixed_ylim = e.inaxes.get_ylim()
    
    curr_t, curr_p = df_base.index[idx_base], df_base.iloc[idx_base]["Close"]
    
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
    global idx_base, is_autoplay
    is_autoplay = False
    print(">>> スキップ中...")
    while idx_base < len(df_base) - 1:
        idx_base += 1
        if check_stop_loss(): break
        curr = df_base.iloc[idx_base]
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
# 表示中の時間足を管理する変数（初期値はH1）
current_view = "H1" 

# --- プログラム後半の図の作成部分を以下に差し替え ---
fig = plt.figure(figsize=(15, 8))
gs = fig.add_gridspec(1, 2, width_ratios=[5, 1], wspace=0.05)
ax_main, ax_info = fig.add_subplot(gs[0,0]), fig.add_subplot(gs[0,1])
ax_info = fig.add_subplot(gs[0, 1]) # 情報パネル

fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", lambda e: pressed.discard(e.key))
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("motion_notify_event", lambda e: (dragging and selected_obj and e.ydata and (globals().update(dragging=True) or ((hlines_data[selected_obj[1]] if selected_obj[0]=='hline' else stop_lines_data[selected_obj[1]]).__setitem__(0, e.ydata)) or redraw())))
fig.canvas.mpl_connect("button_release_event", lambda e: globals().update(dragging=False))
fig.canvas.mpl_connect("close_event", on_close)

timer = fig.canvas.new_timer(interval=int(autoplay_speed * 1000))
timer.add_callback(lambda: (idx_base < len(df_base)-1 and is_autoplay and (globals().update(idx_base=idx_base+1) or check_stop_loss() or redraw())))
timer.start()

redraw()
plt.show()