import pandas as pd
import numpy as np

def analyze_from_existing_csv(tick_1min_path):
    print(f"--- 1分足統計データから分析開始 ---")
    df = pd.read_csv(tick_1min_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 7時~16時(UTC)にフィルタリング
    df['Hour'] = df['Timestamp'].dt.hour
    df = df[(df['Hour'] >= 7) & (df['Hour'] <= 16)].copy()

    # 1. 密度の平均と90%タイル
    avg_density = df['Tick_Count'].mean()
    q90_density = df['Tick_Count'].quantile(0.9)
    top_q90_hours = df[df['Tick_Count'] >= q90_density]['Hour'].value_counts().head(3)

    # 2. 密度(Tick_Count)と時間間隔(Avg_Gap)の相関
    correlation = df['Tick_Count'].corr(df['Avg_Gap'])

    # 3. 需給と価格の逆行・確率
    # 陽線判定
    df['Is_Positive'] = df['Price_Close'] > df['Price_Open']
    # 買い優勢 (>60%) / 売り優勢 (<40%)
    df['Buy_Ratio'] = df['Buy_Ticks'] / df['Tick_Count']
    
    prob_buy_pos = df[df['Buy_Ratio'] > 0.6]['Is_Positive'].mean()
    prob_sell_neg = df[df['Buy_Ratio'] < 0.4]['Is_Positive'].mean() == False
    
    # 逆行地点の抽出
    absorption_buy = df[(df['Buy_Ratio'] > 0.6) & (df['Is_Positive'] == False)]
    absorption_sell = df[(df['Buy_Ratio'] < 0.4) & (df['Is_Positive'] == True)]

    # 結果表示
    print("\n" + "="*40)
    print(f"【1. 密度分析】")
    print(f"平均密度: {avg_density:.2f} ticks/min")
    print(f"90%タイル閾値: {q90_density:.2f} ticks/min")
    print(f"高密度な時間帯(Hour):\n{top_q90_hours}")

    print(f"\n【2. 相関と間隔】")
    print(f"密度と平均間隔の相関: {correlation:.4f}")
    print(f"※相関が強い負であれば、密度上昇に伴い間隔が均一に短縮されています。")

    print(f"\n【3. 需給と方向の整合性】")
    print(f"買い優勢(>60%)で陽線になる確率: {prob_buy_pos*100:.2f}%")
    print(f"売り優勢(>60%)で陰線になる確率: {prob_sell_neg*100:.2f}%")
    print(f"逆行発生件数: 買い逆行={len(absorption_buy)}, 売り逆行={len(absorption_sell)}")
    print("="*40)

    return absorption_buy, absorption_sell

# 実行
path = r'C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025_tick_stats_1min.csv'
abs_buy, abs_sell = analyze_from_existing_csv(path)