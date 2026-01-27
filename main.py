import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import config        # config.py を読み込む
import data_manager  # data_manager.py を読み込む
import engine        # engine.py を読み込む
import visualizer    # visualizer.py を読み込む
import pandas as pd # StartupSettings内でpd.Timestampを使うため必要


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
# 5. イベント処理
# =========================
def on_key_press(e):
    global idx_base, is_autoplay, current_view, fibo_mode, fibo_points    
    pressed.add(e.key)
    step = 10 if "control" in pressed else 1
    # --- 1. 移動量の計算 ---
    tf_steps = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "D1": 1440, "MN": 43200}
    base_step = tf_steps.get(current_view, 1)
    move_amount = base_step * (10 if "control" in pressed else 1)

    # --- 2. 実際の移動（ここを1つのブロックにまとめる） ---
    if e.key == "right":
        if idx_base + move_amount < len(df_base):
            idx_base += move_amount  # ここで指定分だけ進める
            engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers)
            visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
            return # 処理を終了して、下の「+1」を通さないようにする
            
    elif e.key == "left":
        idx_base = max(WINDOW_SIZES["M1"], idx_base - move_amount)
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
        return
    if e.key == "a": is_autoplay = not is_autoplay
    # 時間足切り替え（追加）
   
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
                        if engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers): break
                    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
                elif new_idx <= idx_base:
                    idx_base = max(WINDOW_SIZES["M1"], new_idx)
                    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
            except Exception as ex: print(f"Jump Error: {ex}")
    
    elif e.key in ["delete", "backspace"] and selected_obj:
        t, i = selected_obj
        if t == 'hline': hlines_data.pop(i)
        elif t == 'stop': stop_lines_data.pop(i)
        selected_obj = None
  
    # 1〜6の数字キー判定を確実に
    if e.key in ["1", "2", "3", "4", "5", "6"]:
        current_view = VIEW_MAP[e.key]
        print(f">> 表示切り替え: {current_view}")
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
) # 即座に再描画
        
  
    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
def on_motion(e):
    global dragging, selected_obj, fixed_ylim
    if dragging and selected_obj and e.ydata and e.inaxes:
        # ドラッグ中は記憶した範囲を強制適用して画面の揺れを防ぐ
        e.inaxes.set_ylim(fixed_ylim)
        target_list = hlines_data if selected_obj[0] == 'hline' else stop_lines_data
        target_list[selected_obj[1]][0] = e.ydata
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
def on_button_press(e):
    global dragging, selected_obj, fixed_ylim, fibo_points, fibo_mode, trade, balance, lot_mode, fixed_lot_size   
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
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
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
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
); return

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
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
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
        if engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers): break
        curr = df_base.iloc[idx_base]
        if any(curr["Low"] <= p <= curr["High"] for p, c, ls in hlines_data): break
    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
    

def on_close(event):
    if history and messagebox.askyesno("保存", "CSVに記録しますか？"): visualizer.save_csv_files(history, balance)
    plt.close()


# =========================
# 7. 実行
# =========================
# --- ここから追加 ---
# 1. configから設定を読み込む
PATHS = config.PATHS
WINDOW_SIZES = config.WINDOW_SIZES
VIEW_MAP = config.VIEW_MAP

# 2. data_managerを使ってデータをロードする
DFS = {}
for tf, path in PATHS.items():
    DFS[tf] = data_manager.load_csv(path)

df_base = DFS["M1"]

# 3. 初期状態の変数（これがないと黄色い線が出る）
balance = config.INITIAL_BALANCE
RISK_PER_TRADE = config.RISK_PER_TRADE
idx_base = 0
trade = None
hlines_data, stop_lines_data = [], []
markers, history = [], []
pressed = set()
selected_obj, dragging = None, False
fibo_mode, fibo_points = None, []
retracements, extensions = [], []
is_autoplay = False
autoplay_speed = 0.5
# ------------------

# 価格単位の判定（これもdata_managerに移してもいいですが、一旦ここに）
PIPS_UNIT, ONE_LOT_PIPS_VALUE = (0.01, 1000) if df_base['Close'].iloc[0] > 50 else (0.0001, 1500)

# 表示位置の決定とダイアログ
start_margin = WINDOW_SIZES["M1"] + 50
st = StartupSettings(df_base.index[start_margin])
if not st.confirmed: exit()

lot_mode = st.lot_mode
fixed_lot_size = st.fixed_lot
idx_base = df_base.index.get_indexer([st.dt_result], method='pad')[0]
idx_base = max(start_margin, idx_base)
current_view = "H1"
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
fig.canvas.mpl_connect("motion_notify_event", lambda e: (dragging and selected_obj and e.ydata and (globals().update(dragging=True) or ((hlines_data[selected_obj[1]] if selected_obj[0]=='hline' else stop_lines_data[selected_obj[1]]).__setitem__(0, e.ydata)) or visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
))))
fig.canvas.mpl_connect("button_release_event", lambda e: globals().update(dragging=False))
fig.canvas.mpl_connect("close_event", on_close)

timer = fig.canvas.new_timer(interval=int(autoplay_speed * 1000))
timer.add_callback(lambda: (idx_base < len(df_base)-1 and is_autoplay and (globals().update(idx_base=idx_base+1) or engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers) or visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
))))
timer.start()

visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj
)
plt.show()