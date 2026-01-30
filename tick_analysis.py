import pandas as pd
import numpy as np
import os

def analyze_huge_tick_data(input_path, tick_window=1000, chunk_size=1000000):
    """
    30GB超のデータを分割読み込みし、メモリ消費を抑えて分析する
    """
    print(f"--- 巨大ファイル処理開始 ---")
    output_path = input_path.replace('.csv', '_analyzed.csv')
    
    # 既存の出力ファイルがあれば削除（追記モードのため）
    if os.path.exists(output_path):
        os.remove(output_path)

    # 1. 100万行ずつ読み込み（chunk表示で進捗を確認）
    reader = pd.read_csv(
        input_path, 
        usecols=['Timestamp', 'Bid', 'Ask'], 
        dtype={'Bid': np.float32, 'Ask': np.float32},
        chunksize=chunk_size
    )

    remaining_data = pd.DataFrame()
    chunk_count = 0

    for chunk in reader:
        chunk_count += 1
        print(f"処理中: {chunk_count * chunk_size / 1000000:.0f} 百万行目...")

        # 前回のループで余ったティックを今回の先頭に結合
        if not remaining_data.empty:
            chunk = pd.concat([remaining_data, chunk])

        # 今回のチャンクで「1000ティック」で割り切れる分だけ計算
        n = len(chunk)
        num_bars = n // tick_window
        
        if num_bars == 0:
            remaining_data = chunk
            continue
            
        # 割り切れる分と、次回のループに回す余り（1000未満）に分ける
        calc_size = num_bars * tick_window
        current_data = chunk.iloc[:calc_size]
        remaining_data = chunk.iloc[calc_size:]

        # --- NumPyによる高速計算 ---
        prices = ((current_data['Bid'] + current_data['Ask']) / 2).values
        times = pd.to_datetime(current_data['Timestamp']).values
        
        # 行列化 [足の数, 1000]
        prices_matrix = prices.reshape(-1, tick_window)
        times_matrix = times.reshape(-1, tick_window)

        # 指標計算
        opens = prices_matrix[:, 0]
        closes = prices_matrix[:, -1]
        
        # 一直線度 (Efficiency)
        net_move = np.abs(closes - opens)
        total_path = np.sum(np.abs(np.diff(prices_matrix, axis=1)), axis=1)
        efficiency = np.divide(net_move, total_path, out=np.zeros_like(net_move), where=total_path!=0)

        # 密度 (Duration)
        durations = (times_matrix[:, -1] - times_matrix[:, 0]).astype('timedelta64[s]').astype(np.int32)

        # 結果をデータフレーム化
        res_chunk = pd.DataFrame({
            'StartTime': times_matrix[:, 0],
            'Open': opens,
            'High': np.max(prices_matrix, axis=1),
            'Low': np.min(prices_matrix, axis=1),
            'Close': closes,
            'Duration_Sec': durations,
            'Efficiency': efficiency
        })

        # 2. 結果をCSVに「追記」していく
        res_chunk.to_csv(output_path, mode='a', index=False, header=not os.path.exists(output_path))

    print(f"\n✅ すべての処理が完了しました！")
    print(f"出力ファイル: {output_path}")

# ==========================================
# 設定エリア
# ==========================================
INPUT_PATH = r'C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025.csv'

if __name__ == "__main__":
    try:
        analyze_huge_tick_data(INPUT_PATH, tick_window=1000, chunk_size=2000000)
    except Exception as e:
        print(f"❌ エラー: {e}")