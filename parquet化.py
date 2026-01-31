import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

csv_file = r"C:\Users\81803\OneDrive\ドキュメント\EURUSD_tick_2004_2025.csv"
parquet_file = r"C:\Users\81803\OneDrive\ドキュメント\tick_data.parquet"
chunk_size = 500000 

print("変換を開始します...")

# 1. parse_dates を 'Timestamp' に修正
# low_memory=False を追加すると、型推論による警告を回避できます
reader = pd.read_csv(csv_file, chunksize=chunk_size, parse_dates=['Timestamp'], low_memory=False)

writer = None

try:
    for i, chunk in enumerate(reader):
        # メモリ節約のため、価格データを float32 に変換（必要に応じて）
        # chunk['Bid'] = chunk['Bid'].astype('float32')
        # chunk['Ask'] = chunk['Ask'].astype('float32')

        table = pa.Table.from_pandas(chunk)
        
        if writer is None:
            # 初回にスキーマを定義して書き込み開始
            writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
        
        writer.write_table(table)
        print(f"処理済み: { (i+1) * chunk_size } 行...")

finally:
    if writer:
        writer.close()

print("完了！正常に変換されました。")