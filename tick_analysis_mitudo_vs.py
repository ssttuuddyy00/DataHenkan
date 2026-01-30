import pandas as pd
import numpy as np
import os

def analyze_tick_density_1min(input_path, chunk_size=2000000):
    print(f"--- 1分単位のティック密度・インバランス分析開始 ---")
    output_path = input_path.replace('.csv', '_tick_stats_1min.csv')
    
    if os.path.exists(output_path):
        os.remove(output_path)

    # 読み込み開始
    reader = pd.read_csv(
        input_path, 
        usecols=['Timestamp', 'Bid', 'Ask'], 
        dtype={'Bid': np.float32, 'Ask': np.float32},
        chunksize=chunk_size
    )

    chunk_count = 0
    for chunk in reader:
        chunk_count += 1
        print(f"処理中: {chunk_count * chunk_size / 1000000:.0f} 百万行目...")

        # 前準備
        chunk['Timestamp'] = pd.to_datetime(chunk['Timestamp'])
        chunk['Price'] = (chunk['Bid'] + chunk['Ask']) / 2
        
        # 買い・売りの方向（前回のティック比）
        chunk['Direction'] = np.sign(chunk['Price'].diff()).fillna(0)
        
        # ティック間隔（秒）
        chunk['Gap'] = chunk['Timestamp'].diff().dt.total_seconds()

        # --- 1分単位で集計 ---
        # freq='1min' で1分ごとにデータをまとめる
        stats = chunk.groupby(pd.Grouper(key='Timestamp', freq='1min')).agg(
            Tick_Count=('Price', 'count'),          # 1分間のティック数（密度）
            Avg_Gap=('Gap', 'mean'),                # ティック間の平均秒数
            Buy_Ticks=('Direction', lambda x: (x==1).sum()),  # 買いティック数
            Sell_Ticks=('Direction', lambda x: (x==-1).sum()), # 売りティック数
            Price_Open=('Price', 'first'),
            Price_Close=('Price', 'last')
        ).dropna()

        # CSVに追記保存
        stats.to_csv(output_path, mode='a', header=not os.path.exists(output_path))

    print(f"\n✅ 分析完了！")
    print(f"出力ファイル: {output_path}")

# ==========================================
# 設定エリア
# ==========================================
INPUT_PATH = r'C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025.csv'

if __name__ == "__main__":
    try:
        analyze_tick_density_1min(INPUT_PATH)
    except Exception as e:
        print(f"❌ エラー: {e}")