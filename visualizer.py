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
        # 1. 基準となる現在時刻
        current_time = df_base.index[idx_base]
        
        # 2. その時間足のデータを取得
        full_df = dfs[current_view]
        
        # 3. 現在時刻「以下」のデータを抽出
        # ※ ここで .copy() した後に Close を v_price で上書きしていた処理を完全に削除しました。
        plot_df = full_df[full_df.index <= current_time].copy()
        
        # 4. 表示範囲の切り出し
        plot_df = plot_df.iloc[-WINDOW_SIZES[current_view]:]

        # 5. 描画（CSVにある Open, High, Low, Close をそのまま使用）
        ax_main.clear()
        ax_info.clear()
        ax_info.axis("off")

        if not plot_df.empty:
            # mpf.plot は与えられた DataFrame の値をそのまま描画します
            mpf.plot(plot_df, ax=ax_main, type='candle', style='yahoo')
            ax_main.set_xlim(-0.5, len(plot_df) - 0.5)
            ax_main.set_title(f"VIEW: {current_view} | {current_time.strftime('%Y-%m-%d %H:%M')}", loc='left', fontsize=10)
        # --- 以下、描画処理 (変更なし) ---
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

        # 6. 情報パネルの描画
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

def save_trade_screenshot(df, trade_info, current_view, folder_base=r"C:\Users\81803\OneDrive\画像\リプレイ画像"):
    # 1. 勝ち負けでフォルダを分ける
    sub_folder = "win" if trade_info['profit'] >= 0 else "loss"
    target_dir = os.path.join(folder_base, sub_folder)
    
    # フォルダがなければ作成
    if not os.path.exists(target_dir): 
        os.makedirs(target_dir, exist_ok=True)
    
    # 2. 描画範囲を「エントリーと決済が見える」ように絞る
    # これにより "WARNING: TOO MUCH DATA" を回避し、ローソク足を太く見やすくします
    try:
        entry_idx = df.index.get_indexer([trade_info['time']], method='pad')[0]
        exit_idx = df.index.get_indexer([trade_info['exit_time']], method='pad')[0]
        
        # 前後に少し余裕を持たせる (前後30本ずつ)
        start_idx = max(0, entry_idx - 30)
        end_idx = min(len(df) - 1, exit_idx + 30)
        subset = df.iloc[start_idx:end_idx]
        
        # 3. チャート上に印（矢印と×）を付けるための設定
        # 全データ分 NaN で埋めたリストを作り、特定のインデックスだけ価格を入れる
        entry_markers = [np.nan] * len(subset)
        exit_markers = [np.nan] * len(subset)
        
        # subset内での相対的な位置を計算
        entry_pos = entry_idx - start_idx
        exit_pos = exit_idx - start_idx
        
        entry_markers[entry_pos] = trade_info['price']
        exit_markers[exit_pos] = trade_info['exit_p']

        apds = [
            # エントリー：青の上矢印（BUY）または赤の下矢印（SELL）
            mpf.make_addplot(entry_markers, type='scatter', markersize=200, 
                             marker='^' if trade_info['side']=='BUY' else 'v',
                             color='blue' if trade_info['side']=='BUY' else 'red'),
            # 決済：黒の×印
            mpf.make_addplot(exit_markers, type='scatter', markersize=200, 
                             marker='x', color='black')
        ]

        # 4. 保存
        time_str = trade_info['exit_time'].strftime("%Y%m%d_%H%M%S")
        filename = f"{target_dir}/{time_str}_{current_view}_{trade_info['pips']}pips.png"
        
        mpf.plot(subset, type='candle', style='yahoo', addplot=apds,
                 title=f"Result: {trade_info['pips']} pips ({current_view})",
                 savefig=filename, warn_too_much_data=1000)
        
        print(f"画像保存完了 [{sub_folder}]: {filename}")

    except Exception as e:
        print(f"画像保存中にエラーが発生しました: {e}")
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

def generate_report(folder_base="trade_results"):
    report_path = os.path.join(folder_base, "report.html")
    
    html_content = """
    <html>
    <head>
        <title>Trade Review Report</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f0f0f0; text-align: center; }
            .trade-container { background: white; margin: 20px auto; padding: 15px; border-radius: 8px; max-width: 900px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            img { max-width: 100%; height: auto; border: 1px solid #ddd; }
            h1 { color: #333; }
            .win { color: blue; } .loss { color: red; }
        </style>
    </head>
    <body>
        <h1>トレード検証レポート</h1>
    """

    # WinとLossのフォルダを走査して画像を探す
    for result_type in ["win", "loss"]:
        dir_path = os.path.join(folder_base, result_type)
        if not os.path.exists(dir_path): continue
        
        html_content += f"<h2 class='{result_type}'>{result_type.upper()} Trades</h2>"
        
        # 画像ファイルを取得してHTMLに追加
        images = [f for f in os.listdir(dir_path) if f.endswith('.png')]
        images.sort(reverse=True) # 新しい順
        
        for img_name in images:
            img_rel_path = f"{result_type}/{img_name}"
            html_content += f"""
            <div class="trade-container">
                <p>ファイル名: {img_name}</p>
                <img src="{img_rel_path}" alt="trade">
            </div>
            """

    html_content += "</body></html>"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"レポートを作成しました: {report_path}")