import pandas as pd
import numpy as np

def calculate_efficiency_thresholds(csv_path):
    df = pd.read_csv(csv_path)
    
    # 統計量の算出
    stats = df['Efficiency'].describe(percentiles=[.5, .75, .9, .95, .99])
    
    print("=== Efficiency 統計分布 ===")
    print(f"平均値: {stats['mean']:.4f}")
    print(f"中央値: {stats['50%']:.4f}")
    print(f"上位25% (Q3): {stats['75%']:.4f}  <-- これが『強い』の基準案")
    print(f"上位10%     : {stats['90%']:.4f}  <-- これが『異常』の基準案")
    print(f"上位5%      : {stats['95%']:.4f}")
    print(f"上位1%      : {stats['99%']:.4f}")
    
    # 上位10%の値を閾値として採用する例
    threshold_10p = stats['90%']
    
    return threshold_10p

# 実行
threshold = calculate_efficiency_thresholds(r"C:\Users\81803\OneDrive\ドキュメント\EURUSD_tick_2004_2025_analyzed.csv")