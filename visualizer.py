import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import mplfinance as mpf
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import datetime
import os
import pandas as pd
import numpy as np

def redraw(ax_main, ax_info, fig, dfs, df_base, idx_base, current_view, hlines_data, stop_lines_data, markers, history, balance, is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, fibo_mode, fibo_points, selected_obj):
    try:
        # 1. データの取得
        current_time = df_base.index[idx_base]
        v_price = df_base.iloc[idx_base]["Close"]
        
        full_df = dfs[current_view] # 小文字に修正
        plot_df = full_df[full_df.index <= current_time].copy()
        
        if not plot_df.empty:
            last_idx = plot_df.index[-1]
            plot_df.at[last_idx, "Close"] = v_price
            if v_price > plot_df.at[last_idx, "High"]: plot_df.at[last_idx, "High"] = v_price
            if v_price < plot_df.at[last_idx, "Low"]: plot_df.at[last_idx, "Low"] = v_price

        # 2. 表示範囲の切り出し
        plot_df = plot_df.iloc[-WINDOW_SIZES[current_view]:]

        ax_main.clear() 
        ax_info.clear()
        ax_info.axis("off")

        if not plot_df.empty:
            mpf.plot(plot_df, ax=ax_main, type="candle", style="yahoo")
            ax_main.set_xlim(-0.5, len(plot_df) - 0.5)
            ax_main.set_title(f"VIEW: {current_view} | {current_time}", fontsize=10, loc='left')

        # 3. フィボナッチ描画
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

        # 5. 売買マーカー
        plot_times = plot_df.index.tolist()
        for mt, mp, ms, mc, ma in markers:
            if mt in plot_times:
                ax_main.scatter(plot_times.index(mt), mp, marker=ms, color=mc, s=100, alpha=ma, zorder=1)

        # 6. 情報パネル
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


def save_trade_screenshot(df, trade_info, current_view, folder_base="trade_results"):
    # 1. 勝ち負けでフォルダを分ける
    sub_folder = "win" if trade_info['profit'] >= 0 else "loss"
    target_dir = os.path.join(folder_base, sub_folder)
    if not os.path.exists(folder_base): 
        os.makedirs(folder_base)
    
    # 2. 描画範囲の決定 (エントリーから決済までが見えるように)
    entry_idx = df.index.get_indexer([trade_info['time']], method='pad')[0]
    exit_idx = df.index.get_indexer([trade_info['exit_time']], method='pad')[0]
    
    start_idx = max(0, entry_idx - 30) # エントリーの30本前から
    end_idx = min(len(df) - 1, exit_idx + 30) # 決済の30本後まで
    subset = df.iloc[start_idx:end_idx]
    
    # 3. エントリーと決済を画像内にマークする (追加描画の設定)
    # エントリー点と決済点に印をつけるためのリスト
    apds = [
        # エントリー地点に青(Buy)または赤(Sell)の矢印
        mpf.make_addplot([trade_info['price'] if i == entry_idx else np.nan for i in range(start_idx, end_idx)],
                         type='scatter', markersize=200, marker='^' if trade_info['side']=='BUY' else 'v',
                         color='blue' if trade_info['side']=='BUY' else 'red'),
        # 決済地点に黒の×印
        mpf.make_addplot([trade_info['exit_p'] if i == exit_idx else np.nan for i in range(start_idx, end_idx)],
                         type='scatter', markersize=200, marker='x', color='black')
    ]

    # 4. ファイル名とタイトル (時間足を入れる)
    time_str = trade_info['exit_time'].strftime("%Y%m%d_%H%M%S")
    filename = f"{target_dir}/{time_str}_{current_view}_{trade_info['pips']}pips.png"
    chart_title = f"Result: {trade_info['pips']} pips ({trade_info['side']} on {current_view})"
    
    # 5. 描画
    mpf.plot(subset, type='candle', style='yahoo', 
             addplot=apds,
             title=chart_title,
             savefig=filename, 
             warn_too_much_data=1000)
    
    print(f"画像保存完了 [{sub_folder}]: {filename}")
    if not os.path.exists(folder): os.makedirs(folder)
    
    # トレードの前後を表示範囲にする
    start = max(0, df.index.get_loc(trade_info['time']) - 30)
    end = min(len(df)-1, df.index.get_loc(trade_info['exit_time']) + 30)
    subset = df.iloc[start:end]
    
    # idの代わりに決済時刻(exit_time)をファイル名に使う
    # 時刻の「:」などはファイル名に使えないので、strftimeで数字だけに変換します
    time_str = trade_info['exit_time'].strftime("%Y%m%d_%H%M%S")
    filename = f"{folder}/{time_str}_{trade_info['side']}_{trade_info['pips']}pips.png"
    # 描画して保存（mpfを使うと楽です）
    mpf.plot(subset, type='candle', style='yahoo', savefig=filename)
    print(f"画像保存完了: {filename}")