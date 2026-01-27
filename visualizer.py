import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import mplfinance as mpf
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import datetime

def redraw(ax_main, ax_info, dfs, df_base, idx_base, current_view, hlines_data, stop_lines_data, markers, history, balance, is_autoplay, lot_mode, fixed_lot_size):
    global balance, idx_base, current_view, fibo_mode, lot_mode, fixed_lot_size
    try:
        # 現在の「1分単位」の時刻
        current_time = df_base.index[idx_base]
        v_price = df_base.iloc[idx_base]["Close"]
        
        # 1. 選択した足の全データを取得
        full_df = DFS[current_view]
        
        # 2. 【重要】「現在時刻以前」のデータを抽出
        # これにより、M5なら5分、M15なら15分ごとの確定した足までが表示されます
        plot_df = full_df[full_df.index <= current_time].copy()
        
        # 3. 未確定の「最新の足」を現在価格(M1のClose)でリアルタイム更新する処理
        # これを入れないと、M5やM15で次の5分/15分が来るまで価格が止まって見えます
        if not plot_df.empty:
            last_idx = plot_df.index[-1]
            # M1の価格を、表示中の足の最新値に反映（ヒゲの動きを再現）
            plot_df.at[last_idx, "Close"] = v_price
            if v_price > plot_df.at[last_idx, "High"]: plot_df.at[last_idx, "High"] = v_price
            if v_price < plot_df.at[last_idx, "Low"]: plot_df.at[last_idx, "Low"] = v_price

        # 4. 指定したWINDOWサイズ分だけ切り出し
        plot_df = plot_df.iloc[-WINDOW_SIZES[current_view]:]

        ax_main.clear() 
        ax_info.clear()
        ax_info.axis("off")

        if not plot_df.empty:
            # 5. チャート描画
            mpf.plot(plot_df, ax=ax_main, type="candle", style="yahoo")
            # 軸の範囲を固定してガタつきを抑える
            ax_main.set_xlim(-0.5, len(plot_df) - 0.5)
            ax_main.set_title(f"VIEW: {current_view} | {current_time}", fontsize=10, loc='left')
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
