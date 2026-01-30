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
# --- main.py ---
# 追加
formation_mode = True  # True: 1分足で形成、False: その時間足単位でジャンプ

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
    global idx_base, is_autoplay, current_view, fibo_mode, fibo_points, selected_obj, trade, balance, history, markers , formation_mode 
    global pressed
    # デバッグ用：何のキーが押されたかコンソールに表示
    # print(f"Key Pressed: {e.key}") 
    pressed.add(e.key.lower()) # 全て小文字で保存して判定を安定させる
    
    pressed.add(e.key)
    step = 10 if "control" in pressed else 1
    # --- 1. 移動量の計算 ---
    tf_steps = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "D1": 1440, "MN": 43200}
    base_step = tf_steps.get(current_view, 1)
    move_amount = base_step * (10 if "control" in pressed else 1)

    # --- 2. 実際の移動（ここを1つのブロックにまとめる） ---
    # --- 1. 移動量の計算と実行 ---
   # --- 1. 移動ロジック：データの並び順（整数位置）で直接指定 ---
    full_df = DFS[current_view]
    current_dt = df_base.index[idx_base]

    # 現在の時刻以前で、最も近い上位足の「行番号」を取得
    # searchsorted は非常に高速で、確実に「何番目の行か」を返します
    current_row_idx = full_df.index.searchsorted(current_dt, side='right') - 1

    # --- main.py / on_key_press 内 ---
    # --- 右移動 (進む) ---
    if e.key == "right":
        if formation_mode:
            # 形成モード: 1分足のインデックスを1つ進める
            step = 1 if not "control" in pressed else 10
            idx_base = min(len(df_base) - 1, idx_base + step)
        else:
            # ジャンプモード: 現在の表示足の「次の行」へジャンプ
            current_row_idx = full_df.index.searchsorted(current_dt, side='right')
            target_row_idx = min(len(full_df) - 1, current_row_idx + (9 if "control" in pressed else 0))
            idx_base = df_base.index.searchsorted(full_df.index[target_row_idx])

        # 損切りチェックと再描画
        engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers)
        visualizer.redraw(ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
                         hlines_data, stop_lines_data, markers, history, balance, 
                         is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
                         retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
                         fibo_mode, fibo_points, selected_obj, formation_mode)
        return

    # --- 左移動 (戻る) ---
    elif e.key == "left":
        if formation_mode:
            # 形成モード: 1分足のインデックスを1つ戻す
            step = 1 if not "control" in pressed else 10
            idx_base = max(WINDOW_SIZES["M1"], idx_base - step)
        else:
            # ジャンプモード: 現在の表示足の「前の行」へジャンプ
            # 現在時刻より「前」の開始時刻を持つ行を探す
            current_row_idx = full_df.index.searchsorted(current_dt, side='left') - 1
            target_row_idx = max(0, current_row_idx - (9 if "control" in pressed else 0))
            idx_base = df_base.index.searchsorted(full_df.index[target_row_idx])

        visualizer.redraw(ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
                         hlines_data, stop_lines_data, markers, history, balance, 
                         is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
                         retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
                         fibo_mode, fibo_points, selected_obj, formation_mode)
        return
 

    # モード切り替えキー（例：'m'キー）
    elif e.key == "m":
        formation_mode = not formation_mode
        mode_text = "形成表示モード" if formation_mode else "確定ジャンプモード"
        print(f">> モード変更: {mode_text}")

    
    if e.key == "a": is_autoplay = not is_autoplay
   
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
                        if engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers): 
                            # ★ ここに画像保存を追加！ ★
                            visualizer.save_trade_screenshot(
    df_base, 
    history[-1], 
    current_view, 
    folder_base=config.RESULT_SAVE_DIR  # configから渡す
)
                            break
                    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
)
                elif new_idx <= idx_base:
                    idx_base = max(WINDOW_SIZES["M1"], new_idx)
                    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
)
            except Exception as ex: print(f"Jump Error: {ex}")
    
    elif e.key in ["delete", "backspace"] and selected_obj:
        t, i = selected_obj
        if t == 'hline': hlines_data.pop(i)
        elif t == 'stop': stop_lines_data.pop(i)
        selected_obj = None
  
    # 1〜6の数字キー判定を確実に
    if e.key in ["1", "2", "3", "4", "5", "6"]:
        # 1. ここで new_view を定義（これが漏れると NameError）
        new_view = VIEW_MAP[e.key]
        
        # 2. スナップロジック（現在時刻をその時間足の起点に合わせる）
        current_dt = df_base.index[idx_base]
        freq_map = {
            "M1": "1min", "M5": "5min", "M15": "15min", 
            "H1": "1H", "D1": "1D", "MN": "MS"
        }
        
        if new_view in freq_map:
            if new_view == "MN":
                snapped_dt = current_dt.replace(day=1, hour=0, minute=0, second=0)
            else:
                snapped_dt = current_dt.floor(freq_map[new_view])
            
            new_idx = df_base.index.get_indexer([snapped_dt], method='pad')[0]
            if new_idx != -1:
                idx_base = max(WINDOW_SIZES["M1"], new_idx)

        # 3. ここで現在のビューを更新
        current_view = new_view
        print(f">> 表示切り替え: {current_view}")

        # 4. 描画（ここでも formation_mode を忘れずに！）
        visualizer.redraw(
            ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
            hlines_data, stop_lines_data, markers, history, balance, 
            is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
            retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
            fibo_mode, fibo_points, selected_obj,
            formation_mode
        )
        return  # ここで終わらせないと、下の共通のredrawでまた NameError が出る可能性があります

def on_motion(e):
    global dragging, selected_obj, fixed_ylim, hlines_data, stop_lines_data
    
    # マウスがチャート内にあり、かつドラッグ中のオブジェクトがある場合
    if dragging and selected_obj and e.ydata is not None and e.inaxes:
        # 1. 軸の範囲を固定（ガタつき防止）
        e.inaxes.set_ylim(fixed_ylim)
        
        # 2. 選択中のラインの価格を更新
        obj_type, idx = selected_obj
        if obj_type == 'hline':
            hlines_data[idx][0] = e.ydata
        elif obj_type == 'stop':
            stop_lines_data[idx][0] = e.ydata
            
        # 3. 再描画を実行
        visualizer.redraw(
            ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
            hlines_data, stop_lines_data, markers, history, balance, 
            is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
            retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
            fibo_mode, fibo_points, selected_obj,
            formation_mode # 忘れずに追加
        )
def on_button_press(e):
    # 修正：retracements と extensions を global に追加
    global dragging, selected_obj, fixed_ylim, fibo_points, fibo_mode, \
           trade, balance, lot_mode, fixed_lot_size, hlines_data, \
           stop_lines_data, retracements, extensions # ←ここに追加
    
    if not e.inaxes or e.xdata is None: return
    
    # フィボナッチ打点
    if fibo_mode:
        # 価格(y)と位置(x)をセットで保存することを推奨
        fibo_points.append(e.ydata) 
        print(f"Point {len(fibo_points)} captured at {e.ydata:.3f}")

        if fibo_mode == "RETRACE" and len(fibo_points) == 2:
            # 2点揃ったらリストを更新
            retracements.append({'p1': fibo_points[0], 'p2': fibo_points[1]})
            print("Retracement defined!")
            fibo_mode, fibo_points = None, []
        elif fibo_mode == "EXT" and len(fibo_points) == 3:
            # ここ！ extensions.appen になっていたのを append に修正
            extensions.append({'p1': fibo_points[0], 'p2': fibo_points[1], 'p3': fibo_points[2]})
            fibo_mode, fibo_points = None, []
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
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
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
); return

    # 新規ライン描画（HキーやShiftキー時）
    if not e.inaxes or e.xdata is None or e.ydata is None:
        return

    # --- デバッグ用：クリック時の状態を確認 ---
    # print(f"Click: Button={e.button}, Keys={pressed}")

    # 左クリック(1)の時の処理
    if e.button == 1:
        # Hキーが押されている場合
        if "h" in pressed:
            hlines_data.append([e.ydata, "blue", "-"])
            print(f">> 水平線を追加: {e.ydata:.5f}")
            # 強制描画
            visualizer.redraw(ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
                             hlines_data, stop_lines_data, markers, history, balance, 
                             is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
                             retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
                             fibo_mode, fibo_points, selected_obj, formation_mode)
            return # ラインを引いたら他の判定（エントリーなど）をさせない

        # Shiftキー（Matplotlibでは 'shift'）が押されている場合
        elif "shift" in pressed:
            stop_lines_data.clear()
            stop_lines_data.append([e.ydata, "red", "--"])
            print(f">> 損切りラインを設定: {e.ydata:.5f}")
            visualizer.redraw(ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
                             hlines_data, stop_lines_data, markers, history, balance, 
                             is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
                             retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
                             fibo_mode, fibo_points, selected_obj, formation_mode)
            return
        
    if e.button == 1:
        sl_p = stop_lines_data[0][0] if stop_lines_data else 0
        entry_lot = max(0.01, round(RISK_PER_TRADE / (abs(curr_p - sl_p)/PIPS_UNIT * ONE_LOT_PIPS_VALUE), 2)) if lot_mode == "AUTO" and sl_p else (fixed_lot_size if lot_mode == "FIX" else 0.1)

        # エントリー・決済価格の決定ロジック
        if formation_mode:
            # 【FORMATIONモード】
            # 現在動いているM1のCloseを「現在のリアルタイム価格」として採用
            curr_p = df_base.iloc[idx_base]["Close"]
            curr_t = df_base.index[idx_base]
        else:
            # 【SNAPモード】
            # current_view（H1やD1など）の「確定した足」の終値を採用
            # dfs[current_view] から、現在時刻以下の最新の確定足を取得
            view_df = DFS[current_view]
            valid_view_df = view_df[view_df.index <= df_base.index[idx_base]]
            curr_p = valid_view_df.iloc[-1]["Close"]
            curr_t = valid_view_df.index[-1]

        if "b" in pressed or "v" in pressed:
            side = "BUY" if "b" in pressed else "SELL"
            trade = {"side": side, "price": curr_p, "time": curr_t, "lot": entry_lot, "sl": sl_p, "tp": 0, "symbol": "FX"}
            markers.append((curr_t, curr_p, "^" if side=="BUY" else "v", "blue" if side=="BUY" else "red", 0.6))
        elif "c" in pressed and trade:
            pips = round((curr_p - trade["price"]) / PIPS_UNIT if trade["side"]=="BUY" else (trade["price"] - curr_p) / PIPS_UNIT, 1)
            profit = round(pips * ONE_LOT_PIPS_VALUE * trade["lot"], 0)
            history.append({**trade, "exit_p": curr_p, "exit_time": curr_t, "pips": pips, "profit": profit})
            # ★ ここに画像保存を追加！ ★
            visualizer.save_trade_screenshot(
    df_base, 
    history[-1], 
    current_view, 
    folder_base=config.RESULT_SAVE_DIR  # configから渡す
)
            balance += profit; markers.append((curr_t, curr_p, "x", "black", 0.3)); trade = None; stop_lines_data.clear()
        
        visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
)
def on_button_release(e):
    global dragging, fixed_ylim
    global pressed
    dragging = False
    fixed_ylim = None # 解放
    if e.key.lower() in pressed:
        pressed.discard(e.key.lower())

    fig.canvas.mpl_connect("key_release_event", on_key_release)
def execute_skip():
    global idx_base, is_autoplay
    is_autoplay = False
    print(">>> スキップ中...")
    while idx_base < len(df_base) - 1:
        idx_base += 1
        if engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers): 
            # ★ ここに画像保存を追加！ ★
            visualizer.save_trade_screenshot(
    df_base, 
    history[-1], 
    current_view, 
    folder_base=config.RESULT_SAVE_DIR  # configから渡す
)
            break
        curr = df_base.iloc[idx_base]
        if any(curr["Low"] <= p <= curr["High"] for p, c, ls in hlines_data): break
    visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
)
    

def on_close(event):
    if history and messagebox.askyesno("保存", "CSVに記録しますか？"): 
        visualizer.save_csv_files(history, balance)
        visualizer.generate_report(folder_base=config.RESULT_SAVE_DIR) # ← これを追加！
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
fig.canvas.mpl_connect("motion_notify_event", on_motion)
fig.canvas.mpl_connect("button_release_event", lambda e: globals().update(dragging=False))
fig.canvas.mpl_connect("close_event", on_close)

timer = fig.canvas.new_timer(interval=int(autoplay_speed * 1000))
timer.add_callback(lambda: (idx_base < len(df_base)-1 and is_autoplay and (globals().update(idx_base=idx_base+1) or engine.check_stop_loss(df_base, idx_base, trade, stop_lines_data, PIPS_UNIT, ONE_LOT_PIPS_VALUE, balance, history, markers) or visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
))))
timer.start()

visualizer.redraw(
    ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, 
    hlines_data, stop_lines_data, markers, history, balance, 
    is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, 
    retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, 
    fibo_mode, fibo_points, selected_obj,
    formation_mode # ← これを追加
)


plt.show()