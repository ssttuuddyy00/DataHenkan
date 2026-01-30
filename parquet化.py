import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

csv_file = "your_tick_data.csv"
parquet_file = "tick_data.parquet"
chunk_size = 500000  # 50万行ずつ処理（メモリに合わせて調整）

print("変換を開始します...")

# 1. CSVを分割読み込みするイテレータを作成
reader = pd.read_csv(csv_file, chunksize=chunk_size, parse_dates=['Datetime'])

writer = None

for i, chunk in enumerate(reader):
    # 型を最適化してさらにメモリを節約（float64 -> float32など）
    # chunk['Price'] = chunk['Price'].astype('float32') 
    
    # 初回ループ時に書き込み用オブジェクトを作成
    table = pa.Table.from_pandas(chunk)
    if writer is None:
        writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
    
    writer.write_table(table)
    print(f"処理済み: { (i+1) * chunk_size } 行...")

if writer:
    writer.close()

print("完了！メモリを汚さず変換できました。")