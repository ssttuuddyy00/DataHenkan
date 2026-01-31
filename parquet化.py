import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import timedelta

csv_file = r"C:\Users\81803\OneDrive\ドキュメント\EURUSD_tick_2004_2025.csv"
parquet_file = r"C:\Users\81803\OneDrive\ドキュメント\tick_data.parquet"
chunk_size = 500000 

print("変換とJSTへの時差修正を開始します...")

# chunksizeを指定して読み込み
reader = pd.read_csv(csv_file, chunksize=chunk_size, parse_dates=['Timestamp'], low_memory=False)

writer = None

try:
    for i, chunk in enumerate(reader):
        # --- 時間を UTC+9 に変換 ---
        # 1. もしTimestampがまだ「TimeZone無し」ならUTCとして明示し、JST(+9)に変換
        # もしくは単純に 9時間を加算する（こちらの方が高速な場合が多いです）
        chunk['Timestamp'] = chunk['Timestamp'] + pd.Timedelta(hours=9)
        
        # 2. 型の最適化 (オプション: メモリ節約)
        # chunk['Bid'] = chunk['Bid'].astype('float32')
        # chunk['Ask'] = chunk['Ask'].astype('float32')

        table = pa.Table.from_pandas(chunk)
        
        if writer is None:
            # 最初のチャンクでスキーマ（列構成）を決定
            writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
        
        writer.write_table(table)
        
        processed_rows = (i + 1) * chunk_size
        print(f"処理済み: {processed_rows:,} 行...")

finally:
    if writer:
        writer.close()

print("完了！全てのデータが日本時間（UTC+9）で保存されました。")