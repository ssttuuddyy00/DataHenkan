import pandas as pd
import numpy as np

def analyze_imbalance_and_reversal(csv_path):
    print(f"--- 1分足統計から需給矛盾を分析中 ---")
    df = pd.read_csv(csv_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 7時~16時(UTC)にフィルタリング
    df['Hour'] = df['Timestamp'].dt.hour
    df = df[(df['Hour'] >= 7) & (df['Hour'] <= 16)].copy()

    # --- 基本データの作成 ---
    # 陽線・陰線の判定
    df['Is_Positive'] = df['Price_Close'] > df['Price_Open']
    df['Is_Negative'] = df['Price_Close'] < df['Price_Open']
    
    # 買い/売り比率の算出
    df['Buy_Ratio'] = df['Buy_Ticks'] / df['Tick_Count']
    df['Sell_Ratio'] = df['Sell_Ticks'] / df['Tick_Count']

    # --- 1. 確率の算出 ---
    # 買い優勢(60%以上)の時の陽線確率
    strong_buy_df = df[df['Buy_Ratio'] >= 0.6]
    prob_buy_pos = strong_buy_df['Is_Positive'].mean()

    # 売り優勢(60%以上)の時の陰線確率
    strong_sell_df = df[df['Sell_Ratio'] >= 0.6]
    prob_sell_neg = strong_sell_df['Is_Negative'].mean()

    # --- 2. 逆行（Absorption）の特定 ---
    # 買いが多いのに下落（＝強力な売り壁に吸収された）
    absorption_buy = strong_buy_df[strong_buy_df['Is_Positive'] == False].copy()
    
    # 売りが多いのに上昇（＝強力な買い壁に吸収された）
    absorption_sell = strong_sell_df[strong_sell_df['Is_Negative'] == False].copy()

    # --- 3. 結果表示 ---
    print("\n" + "="*45)
    print(f"【分析対象数】 7時-16時の合計: {len(df)} 分")
    print("-" * 45)
    print(f"■ 買い優勢時(>=60%)の陽線確率: {prob_buy_pos*100:.2f}%")
    print(f"■ 売り優勢時(>=60%)の陰線確率: {prob_sell_neg*100:.2f}%")
    print("-" * 45)
    print(f"■ 買い逆行（Buy多/価格下落）の発生数: {len(absorption_buy)} 件")
    print(f"■ 売り逆行（Sell多/価格上昇）の発生数: {len(absorption_sell)} 件")
    print("="*45)

    # 逆行が起きた「時間帯」の傾向
    if len(absorption_buy) > 0:
        print("\n[買い逆行が起きやすい時間(Top3)]")
        print(absorption_buy['Hour'].value_counts().head(3))

    # 逆行地点をリストとして保存
    absorption_buy[['Timestamp', 'Buy_Ratio', 'Price_Open', 'Price_Close']].to_csv('buy_absorption_list.csv', index=False)
    
    return absorption_buy, absorption_sell

# 実行
path = r'C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025_tick_stats_1min.csv'
abs_buy, abs_sell = analyze_imbalance_and_reversal(path)