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
from matplotlib.ticker import MultipleLocator

def redraw(ax_main, ax_info, fig, DFS, df_base, idx_base, current_view, hlines_data, stop_lines_data, markers, history, balance, is_autoplay, lot_mode, fixed_lot_size, WINDOW_SIZES, retracements, extensions, RISK_PER_TRADE, PIPS_UNIT, ONE_LOT_PIPS_VALUE, fibo_mode, fibo_points, selected_obj, formation_mode):
    try:
        # 1. データの準備
        current_time = df_base.index[idx_base]
        v_price = df_base.iloc[idx_base]["Close"]
        full_df = DFS[current_view]
        plot_df = full_df[full_df.index <= current_time].copy()
        
        if not plot_df.empty and formation_mode:
            last_idx = plot_df.index[-1]
            plot_df.at[last_idx, "Close"] = v_price
            m1_segment = df_base.loc[last_idx:current_time]
            plot_df.at[last_idx, "High"] = m1_segment["High"].max()
            plot_df.at[last_idx, "Low"] = m1_segment["Low"].min()

        # 2. 描画エリアの整理
        ax_main.clear()
        ax_info.clear()
        # 右側の情報用ボックスを完全に非表示にして、チャートを右端まで広げる
        ax_info.set_visible(False) 
        
        if not plot_df.empty:
            display_df = plot_df.iloc[-WINDOW_SIZES[current_view]:]
            
            # --- ローソク足描画 ---
            mpf.plot(display_df, ax=ax_main, type='candle', style='yahoo')
            
            # --- 価格軸（右軸）とグリッドの調整 ---
            # 10pips(0.1)ごとに太い点線、1pips(0.01)ごとに細い点線を引く
            ax_main.yaxis.set_major_locator(MultipleLocator(0.1)) 
            ax_main.yaxis.set_minor_locator(MultipleLocator(0.01))
            ax_main.grid(True, which='major', axis='y', color='gray', linestyle='--', alpha=0.4)
            ax_main.grid(True, which='minor', axis='y', color='gray', linestyle=':', alpha=0.2)
            
            # --- 時間軸（下軸）の調整 ---
            # 表示本数に合わせて目盛りの数を自動調整（5〜6個程度表示）
            step = max(1, len(display_df) // 6)
            ax_main.xaxis.set_major_locator(MultipleLocator(step))
            labels = [display_df.index[int(i)].strftime('%H:%M') for i in ax_main.get_xticks() if 0 <= i < len(display_df)]
            ax_main.set_xticklabels(labels, fontsize=8)
            
            # チャート右側に少しだけ余白を作り、最新足を見やすくする
            ax_main.set_xlim(-0.5, len(display_df) + 1.5) 

            # --- 水平線の描画 (ラベル付き) ---
            for i, (val, color, style) in enumerate(hlines_data):
                is_selected = (selected_obj and selected_obj[0]=='hline' and selected_obj[1]==i)
                ax_main.axhline(val, color=color, linestyle=style, linewidth=2.5 if is_selected else 1.2, zorder=3)
                # 右端に価格を表示
                ax_main.text(len(display_df) + 0.2, val, f'{val:.3f}', 
                             va='center', fontsize=9, color=color, 
                             bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

            # --- 損切りラインの描画 (ラベル付き) ---
            for val, color, style in stop_lines_data:
                ax_main.axhline(val, color=color, linestyle=style, linewidth=1.5, zorder=4)
                # 右端に「SL: 価格」と表示
                ax_main.text(len(display_df) + 0.2, val, f'SL: {val:.3f}', 
                             va='bottom', fontsize=9, color=color, fontweight='bold',
                             bbox=dict(facecolor='white', alpha=0.8, edgecolor=color, pad=1))
                
            # --- マーカー（エントリー・決済印）の描画 ---
            for m_time, m_price, m_marker, m_color, m_alpha in markers:
                if m_time >= display_df.index[0]:
                    last_time = display_df.index[-1]
                    # 最新足以降なら右端に固定
                    idx_pos = len(display_df)-1 if m_time >= last_time else display_df.index.get_indexer([m_time], method='pad')[0]
                    
                    # 見やすくするために縁取りを追加（x以外）
                    edge = 'white' if m_marker != 'x' else None
                    ax_main.scatter(idx_pos, m_price, marker=m_marker, color=m_color, s=200, alpha=m_alpha, zorder=5, edgecolors=edge)
                    # マーカー位置に短い水平ガイド
                    ax_main.hlines(m_price, idx_pos - 0.5, idx_pos + 0.5, colors=m_color, alpha=0.5, linestyles='--')
            
            
            # --- フィボナッチ描画 (ラベル付き) ---
            
            # --- 時間軸目盛りの警告対策 ---
            step = max(1, len(display_df) // 6)
            ticks = np.arange(0, len(display_df), step)
            ax_main.set_xticks(ticks) # 先に位置を固定
            labels = [display_df.index[int(i)].strftime('%H:%M') for i in ticks]
            ax_main.set_xticklabels(labels, fontsize=8) # その後にラベルを貼る
            
            # 1. リトレースメント
            for f in retracements:
                p1, p2 = f['p1'], f['p2']
                diff = p1 - p2
                levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
                for lv in levels:
                    lv_p = p2 + diff * lv
                    ax_main.axhline(lv_p, color='orange', linestyle='--', alpha=0.6, linewidth=0.8)
                    # 右端にラベルを表示 (x座標は表示データ本数 + 0.5)
                    ax_main.text(len(display_df) + 0.5, lv_p, f'{lv*100:.1f}%', 
                                 va='center', fontsize=8, color='orange', fontweight='bold')

            # 2. エクステンション
            for e_f in extensions:
                ep1, ep2, ep3 = e_f['p1'], e_f['p2'], e_f['p3']
                exp_diff = ep2 - ep1
                exp_levels = [0, 0.618, 1.0, 1.618, 2.618]
                for lv in exp_levels:
                    lv_p = ep3 + exp_diff * lv
                    ax_main.axhline(lv_p, color='cyan', linestyle='-.', alpha=0.6, linewidth=0.8)
                    # 右端にラベルを表示
                    ax_main.text(len(display_df) + 0.5, lv_p, f'Exp {lv*100:.1f}%', 
                                 va='center', fontsize=8, color='cyan', fontweight='bold')
            # --- 仕上げ（tight_layoutの警告対策） ---
            # tight_layout() は使わず、手動で余白を調整
            fig.subplots_adjust(left=0.07, right=0.93, bottom=0.1, top=0.95)
            ax_main.set_title(f"{current_view} | {current_time} | Price: {v_price:.3f}", loc='left', fontsize=10)

        # チャート全体をウィンドウいっぱいに広げる（余白調整）
        #fig.tight_layout()
        fig.subplots_adjust(right=0.93) # 右側の目盛り数字が入るスペースだけ確保
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