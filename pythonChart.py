import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# =========================
# 設定
# =========================
H1_PATH = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv"
D1_PATH = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/B_data.csv"
WINDOW_H1 = 200
WINDOW_D1 = 100

def load_csv(path):
    df = pd.read_csv(path)
    if "Hour" in df.columns:
        df["Date"] = pd.to_datetime(df[["Year","Month","Day","Hour"]])
    else:
        df["Date"] = pd.to_datetime(df[["Year","Month","Day"]])
    df.set_index("Date", inplace=True)
    return df[["Open","High","Low","Close","Volume"]]

try:
    df_h1 = load_csv(H1_PATH)
    df_d1 = load_csv(D1_PATH)
except Exception as e:
    print(f"Error: {e}"); exit()

idx_h1 = WINDOW_H1

# =========================
# 状態管理
# =========================
pressed = set()
hlines, stop_lines, rects = [], [], []
selected = None
dragging = False
drag_start = None

trade = None
history = []
markers = [] 

current_rect = None
rect_start = None

# =========================
# レイアウト
# =========================
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 2], hspace=0.3, wspace=0.1)
ax_d1 = fig.add_subplot(gs[0, 0])
ax_h1 = fig.add_subplot(gs[1, 0])
ax_info = fig.add_subplot(gs[:, 1])
ax_info.axis("off")

# =========================
# 補助関数
# =========================
def redraw():
    # 最新（一番右）のデータ情報を取得
    h1_start = max(0, idx_h1 - WINDOW_H1)
    h1_plot_data = df_h1.iloc[h1_start:idx_h1]
    current_time = h1_plot_data.index[-1]
    
    idx_d1 = df_d1.index.get_indexer([current_time], method='pad')[0]
    d1_plot_data = df_d1.iloc[max(0, idx_d1 - WINDOW_D1):idx_d1 + 1]

    ax_d1.clear()
    ax_h1.clear()

    # チャート描画
    mpf.plot(d1_plot_data, ax=ax_d1, type="candle", style="yahoo")
    mpf.plot(h1_plot_data, ax=ax_h1, type="candle", style="yahoo")
    
    ax_d1.set_title(f"Daily Chart - {current_time.date()}")
    ax_h1.set_title("H1 Replay [B:Buy, V:Sell, C:Close, Shift+Click: StopLoss/Exit, Right-Drag:Rect]")

    # オブジェクト描画
    for ax in [ax_d1, ax_h1]:
        for l in hlines + stop_lines:
            new_l = Line2D([0, 1], [l.get_ydata()[0], l.get_ydata()[0]], transform=ax.get_yaxis_transform())
            new_l.set_color(l.get_color()); new_l.set_linestyle(l.get_linestyle())
            new_l.set_linewidth(3.0 if l == selected else 1.5)
            ax.add_line(new_l)
        for r in rects:
            ax.add_patch(Rectangle(r.get_xy(), r.get_width(), r.get_height(), 
                                   fill=False, edgecolor="orange" if r == selected else "green", 
                                   linewidth=2 if r == selected else 1))

    # エントリーマーカー描画
    visible_times = h1_plot_data.index.tolist()
    for m_time, m_price, m_text, m_color in markers:
        if m_time in visible_times:
            x_pos = visible_times.index(m_time)
            ax_h1.text(x_pos, m_price, m_text, color=m_color, fontsize=9, fontweight="bold", 
                       ha="center", bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    if trade:
        ax_h1.text(0.02, 0.95, f"POS: {trade['side']} @ {trade['price']:.5f}", 
                   transform=ax_h1.transAxes, color="red", fontweight="bold", bbox=dict(facecolor='white', alpha=0.8))

    # 履歴表示
    ax_info.clear()
    ax_info.axis("off")
    total_pnl = sum(h['pnl'] for h in history)
    hist_text = f"【TRADE HISTORY】\nTOTAL: {total_pnl:+.4f}\n" + "-"*15 + "\n"
    for h in history[-10:]:
        hist_text += f"{h['side']} {h['pnl']:+.4f}\nIn:{h['entry_p']:.4f} Out:{h['exit_p']:.4f}\n\n"
    ax_info.text(0, 1, hist_text, transform=ax_info.transAxes, verticalalignment="top", fontfamily="monospace", fontsize=9)

    fig.canvas.draw_idle()

# =========================
# ハンドラ
# =========================
def on_key_press(e):
    global idx_h1, selected; pressed.add(e.key)
    if e.key == "right": idx_h1 = min(len(df_h1), idx_h1 + 1); redraw()
    elif e.key == "left": idx_h1 = max(WINDOW_H1, idx_h1 - 1); redraw()
    elif e.key in ["delete", "backspace"] and selected:
        if selected in hlines: hlines.remove(selected)
        elif selected in stop_lines: stop_lines.remove(selected)
        elif selected in rects: rects.remove(selected)
        selected = None; redraw()

def on_key_release(e):
    pressed.discard(e.key)

def on_button_press(e):
    global selected, dragging, drag_start, trade, markers, history, rect_start, current_rect
    if e.inaxes not in [ax_d1, ax_h1]: return
    
    # 現在の足の情報（常に最新の足を使用）
    current_idx = idx_h1 - 1
    current_time = df_h1.index[current_idx]
    current_price = df_h1.iloc[current_idx]["Close"]

    # 右クリック: 矩形
    if e.button == 3:
        rect_start = (e.xdata, e.ydata)
        current_rect = Rectangle(rect_start, 0, 0, fill=False, edgecolor="green", linestyle="--")
        e.inaxes.add_patch(current_rect)
        return

    # 左クリック
    if e.button == 1:
        # 1. 買い (B) - 最新足でエントリー
        if "b" in pressed:
            trade = {"side":"BUY", "price":current_price, "time":current_time}
            markers.append((current_time, current_price, "▲BUY", "blue")); redraw(); return
        
        # 2. 売り (V) - 最新足でエントリー
        elif "v" in pressed:
            trade = {"side":"SELL", "price":current_price, "time":current_time}
            markers.append((current_time, current_price, "▼SELL", "red")); redraw(); return
        
        # 3. 成行決済 (C) - 最新足で決済
        elif "c" in pressed and trade:
            pnl = (current_price - trade["price"]) if trade["side"]=="BUY" else (trade["price"] - current_price)
            history.append({"side":trade["side"], "entry_p":trade["price"], "exit_p":current_price, "pnl":pnl})
            markers.append((current_time, current_price, f"✖CLOSE\n{pnl:+.4f}", "black"))
            trade = None; redraw(); return

        # 4. 逆指値決済 (Shift + Click)
        elif "shift" in pressed:
            # 逆指値ラインを引く
            stop_price = e.ydata
            l = Line2D([0, 1], [stop_price, stop_price], color="red", linestyle="--")
            stop_lines.append(l)
            
            # もしポジションがあれば、クリックした価格で決済（指値/逆指値シミュレーション）
            if trade:
                pnl = (stop_price - trade["price"]) if trade["side"]=="BUY" else (trade["price"] - stop_price)
                history.append({"side":trade["side"], "entry_p":trade["price"], "exit_p":stop_price, "pnl":pnl})
                markers.append((current_time, stop_price, f"✖STOP\n{pnl:+.4f}", "darkred"))
                trade = None
            redraw(); return

        # 5. 水平線 (Ctrl)
        elif "control" in pressed:
            l = Line2D([0, 1], [e.ydata, e.ydata], color="blue", linestyle="-")
            hlines.append(l); selected = l; redraw(); return

        # 6. オブジェクト選択
        selected = None
        for l in hlines + stop_lines:
            if abs(l.get_ydata()[0] - e.ydata) < (e.inaxes.get_ylim()[1]-e.inaxes.get_ylim()[0])*0.04:
                selected = l; dragging = True; drag_start = e.ydata; break
        if not selected:
            for r in rects:
                rx, ry = r.get_xy(); rw, rh = r.get_width(), r.get_height()
                if min(rx, rx+rw) <= e.xdata <= max(rx, rx+rw) and min(ry, ry+rh) <= e.ydata <= max(ry, ry+rh):
                    selected = r; dragging = True; drag_start = (e.xdata, e.ydata); break
        redraw()

def on_motion(e):
    global dragging, drag_start
    if e.inaxes not in [ax_d1, ax_h1]: return
    if e.button == 3 and current_rect:
        current_rect.set_width(e.xdata - rect_start[0])
        current_rect.set_height(e.ydata - rect_start[1])
        fig.canvas.draw_idle()
    if dragging and selected:
        if isinstance(selected, Line2D):
            selected.set_ydata([e.ydata, e.ydata])
        elif isinstance(selected, Rectangle):
            dx, dy = e.xdata - drag_start[0], e.ydata - drag_start[1]
            rx, ry = selected.get_xy()
            selected.set_xy((rx + dx, ry + dy))
            drag_start = (e.xdata, e.ydata)
        redraw()

def on_release(e):
    global dragging, current_rect
    if e.button == 3 and current_rect:
        rects.append(current_rect); current_rect = None; redraw()
    dragging = False

# =========================
# 接続
# =========================
fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", on_key_release)
fig.canvas.mpl_connect("button_press_event", on_button_press)
fig.canvas.mpl_connect("motion_notify_event", on_motion)
fig.canvas.mpl_connect("button_release_event", on_release)

redraw()
plt.show()