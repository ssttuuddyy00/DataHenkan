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

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import mplfinance as mpf
import os
import pandas as pd
import numpy as np

def redraw(ax_main, ax_info, fig, dfs, df_base, idx_base, current_view, hlines_data, stop_lines_data, markers, history, balance, is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, retracements, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, fibo_mode, fibo_points, selected_obj, formation_mode):
    try:
        # 1. データの準備
        current_time = df_base.index[idx_base]
        v_price = df_base.iloc[idx_base]["Close"]
        full_df = dfs[current_view]
        
        # 2. データの抽出（現在時刻まで）
        plot_df = full_df[full_df.index <= current_time].copy()
        
        if not plot_df.empty:
            if formation_mode:
                last_idx = plot_df.index[-1]
                plot_df.at[last_idx, "Close"] = v_price
                m1_segment = df_base.loc[last_idx:current_time]
                plot_df.at[last_idx, "High"] = m1_segment["High"].max()
                plot_df.at[last_idx, "Low"] = m1_segment["Low"].min()

        # 3. 描画クリア
        ax_main.clear()
        ax_info.clear()
        ax_info.axis("off")
        
        if not plot_df.empty:
            # 表示範囲を取得
            display_df = plot_df.iloc[-WINDOW_SIZES[current_view]:]
            
            # --- 【ここがポイント】右側に1本分の「未来の余白」を作る ---
            # これにより、最新足が「右から2番目」になり、マーカー位置が安定します
            mpf.plot(display_df, ax=ax_main, type='candle', style='yahoo')
            
            # --- ここから追加：価格軸と時間軸の見栄え調整 ---
            
            # 1. 価格軸（右軸）の調整：5pipsや10pips刻みに設定
            # 現在の表示範囲の最大・最小価格を取得
            ymin, ymax = ax_main.get_ylim()
            # 0.01刻み（10pipsごと）などでグリッドを引きやすくする
            from matplotlib.ticker import MultipleLocator
            ax_main.yaxis.set_major_locator(MultipleLocator(0.1)) # 10pips刻みの目盛り
            ax_main.yaxis.set_minor_locator(MultipleLocator(0.01)) # 1pips刻みの補助目盛り
            
            # 2. 時間軸（下軸）の調整：表示本数に合わせて適切な間隔で時刻を表示
            ax_main.xaxis.set_major_locator(MultipleLocator(max(1, len(display_df)//5)))
            
            # 3. グリッド線を表示（ラウンドナンバーを見やすく）
            ax_main.grid(True, which='major', axis='both', color='gray', linestyle='--', alpha=0.3)
            ax_main.grid(True, which='minor', axis='y', color='gray', linestyle=':', alpha=0.1)
            
            # 時刻ラベルのフォーマットを読みやすく（15:00 等）
            import matplotlib.dates as mdates
            # インデックスがDatetimeIndexの場合
            labels = [display_df.index[int(i)].strftime('%H:%M') for i in ax_main.get_xticks() if 0 <= i < len(display_df)]
            ax_main.set_xticklabels(labels, fontsize=8)
            # 横軸の範囲を「データの長さ」より1つ大きく設定する
            ax_main.set_xlim(-0.5, len(display_df) + 0.5) 

            # --- 水平線の描画 ---
            for i, (val, color, style) in enumerate(hlines_data):
                is_selected = (selected_obj and selected_obj[0]=='hline' and selected_obj[1]==i)
                ax_main.axhline(val, color=color, linestyle=style, linewidth=2.5 if is_selected else 1.0)

            # --- マーカー（エントリー・決済印）の描画 ---
            # --- マーカー（エントリー・決済印）の描画 ---
            for m_time, m_price, m_marker, m_color, m_alpha in markers:
                # 1. そもそも表示範囲内にあるかチェック
                if m_time >= display_df.index[0]:
                    
                    # 2. 現在の最新足の時刻を取得
                    last_time = display_df.index[-1]
                    
                    # 3. マーカーの時刻が「最新足の開始時刻」と同じ、もしくはそれ以降（形成中）なら
                    # インデックス番号で「一番右端」を指定する
                    if m_time >= last_time:
                        idx_pos = len(display_df) - 1
                    else:
                        # 過去の足なら、その位置を探す
                        idx_pos = display_df.index.get_indexer([m_time], method='pad')[0]
                    
                    # 描画（横位置 idx_pos, 縦位置 m_price）
                    ax_main.scatter(idx_pos, m_price, marker=m_marker, color=m_color, 
                                    s=200, alpha=m_alpha, zorder=5)
            # タイトルなど
            ax_main.set_title(f"{current_view} | {current_time}", loc='left', fontsize=9)

        fig.canvas.draw_idle()
    except Exception as e:
        print(f"Redraw Error: {e}")
def save_trade_screenshot(df, trade_info, current_view, folder_base=r"C:\Users\81803\OneDrive\画像\リプレイ画像"):
    # 1. 勝ち負けでサブフォルダを決定 (HTMLレポートが機能するために重要)
    sub_folder = "win" if trade_info['profit'] >= 0 else "loss"
    target_dir = os.path.join(folder_base, sub_folder)
    
    # 親フォルダとサブフォルダを再帰的に作成
    if not os.path.exists(target_dir): 
        os.makedirs(target_dir, exist_ok=True)
    
    try:
        # 2. 描画範囲の絞り込み
        entry_idx = df.index.get_indexer([trade_info['time']], method='pad')[0]
        exit_idx = df.index.get_indexer([trade_info['exit_time']], method='pad')[0]
        
        start_idx = max(0, entry_idx - 30)
        end_idx = min(len(df) - 1, exit_idx + 30)
        subset = df.iloc[start_idx:end_idx].copy()
        
        # 3. マーカー設定
        entry_markers = [np.nan] * len(subset)
        exit_markers = [np.nan] * len(subset)
        
        entry_pos = entry_idx - start_idx
        exit_pos = exit_idx - start_idx
        
        entry_markers[entry_pos] = trade_info['price']
        exit_markers[exit_pos] = trade_info['exit_p']

        apds = [
            mpf.make_addplot(entry_markers, type='scatter', markersize=200, 
                             marker='^' if trade_info['side']=='BUY' else 'v',
                             color='blue' if trade_info['side']=='BUY' else 'red'),
            mpf.make_addplot(exit_markers, type='scatter', markersize=200, 
                             marker='x', color='black')
        ]

        # 4. ファイル名の生成
        time_str = trade_info['exit_time'].strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(target_dir, f"{time_str}_{current_view}_{trade_info['pips']}pips.png")
        
        # 5. 保存実行
        mpf.plot(subset, type='candle', style='yahoo', addplot=apds,
                 title=f"Result: {trade_info['pips']} pips ({current_view})",
                 savefig=filename, warn_too_much_data=1000)
        
        print(f"画像保存完了 [{sub_folder}]: {filename}")

    except Exception as e:
        print(f"画像保存中にエラーが発生しました: {e}")
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