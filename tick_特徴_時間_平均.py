import pandas as pd
import numpy as np

def deep_analyze_tick_bars(csv_path):
    # データの読み込み
    df = pd.read_csv(csv_path)
    df['StartTime'] = pd.to_datetime(df['StartTime'])
    df['Hour'] = df['StartTime'].dt.hour  # 時間帯（0-23）を抽出

    # --- 1. 時間帯別の基本統計 ---
    print("=== 時間帯別の統計 (0時-23時) ===")
    hourly_stats = df.groupby('Hour').agg({
        'Duration_Sec': 'mean',    # 平均完成時間
        'Efficiency': 'mean'       # 平均効率性
    }).rename(columns={'Duration_Sec': 'Avg_Duration', 'Efficiency': 'Avg_Efficiency'})
    
    # 1000ティックが最も早く溜まる時間帯（Top 3）
    fastest_hours = hourly_stats['Avg_Duration'].nsmallest(3)
    print(f"\n1000ティックが溜まるのが早い時間帯:\n{fastest_hours}")
    
    # --- 2. 買い/売りインバランスの逆行分析 ---
    # ※もし元データにBuy_Count/Sell_Countを入れている場合、以下で抽出可能
    # ここでは「価格変化」と「需給」の不一致を探します
    if 'Buy_Count' in df.columns:
        # 買いが60%以上なのに価格が下落した足
        buy_absorption = df[(df['Buy_Count'] > 600) & (df['Close'] < df['Open'])]
        # 売りが60%以上なのに価格が上昇した足
        sell_absorption = df[(df['Sell_Count'] > 600) & (df['Close'] > df['Open'])]
        
        print(f"\n買いが多いのに下落した回数: {len(buy_absorption)}")
        print(f"売りが多いのに上昇した回数: {len(sell_absorption)}")
        # サンプルを表示
        print("\n[買い逆行のサンプル時間]\n", buy_absorption[['StartTime', 'Buy_Count', 'Open', 'Close']].head())

    # --- 3. Efficiency 0.2前後の「高効率」な瞬間を特定 ---
    print("\n=== Efficiency 0.2以上の異常値データ ===")
    high_eff_df = df[df['Efficiency'] >= 0.106].copy()
    
    if not high_eff_df.empty:
        # 高効率な足がいつ発生しやすいか（時間帯別カウント）
        high_eff_hourly = high_eff_df.groupby('Hour').size()
        print(f"Efficiency >= 0.2 が発生しやすい時間帯:\n{high_eff_hourly.nlargest(5)}")
        
        # 具体的な場所（時間）をCSVで保存
        high_eff_df.to_csv('high_efficiency_moments.csv', index=False)
        print(f"\n✅ 高効率な瞬間のリストを 'high_efficiency_moments.csv' に保存しました。")
    else:
        print("Efficiency 0.2以上のデータは見つかりませんでした。")

    return hourly_stats, high_eff_df

# 実行（パスを書き換えてください）
stats, high_eff = deep_analyze_tick_bars(r"C:\Users\81803\OneDrive\ドキュメント\EURUSD_tick_2004_2025_analyzed.csv")