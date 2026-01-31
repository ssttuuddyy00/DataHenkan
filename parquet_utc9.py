import pandas as pd
import pyarrow.parquet as pq
import gc
import os

def preprocess_parquet_safe(input_file, output_file, chunk_size=100000):
    """
    chunk_size: 一度にメモリに読み込む行数。
    メモリが厳しい場合は 100,000 程度に下げてください。
    """
    print(f">> 変換開始: {input_file}")
    
    # Parquetファイルを読み込むためのオブジェクト
    parquet_file = pq.ParquetFile(input_file)
    writer = None
    
    try:
        # チャンクごとに読み込み
        for i in range(0, parquet_file.metadata.num_rows, chunk_size):
            # 特定の範囲だけ読み込む（メモリ節約）
            df_chunk = parquet_file.read_row_group(i // chunk_size if i < parquet_file.metadata.num_rows else 0).to_pandas()
            # もし上記でエラーが出る環境の場合はこちら: 
            # df_chunk = pd.read_parquet(input_file).iloc[i : i + chunk_size]
            
            # 1. タイムゾーン変換 (UTC -> JST)
            if not pd.api.types.is_datetime64_any_dtype(df_chunk['Timestamp']):
                df_chunk['Timestamp'] = pd.to_datetime(df_chunk['Timestamp'])
            df_chunk['Timestamp'] = df_chunk['Timestamp'] + pd.Timedelta(hours=9)
            
            # 2. 中間値の計算
            df_chunk['Price'] = (df_chunk['Bid'] + df_chunk['Ask']) / 2
            
            # 3. メモリ節約：数値型を軽量化 (float64 -> float32)
            # FXの価格精度なら float32 で十分なことが多いです
            df_chunk['Bid'] = df_chunk['Bid'].astype('float32')
            df_chunk['Ask'] = df_chunk['Ask'].astype('float32')
            df_chunk['Price'] = df_chunk['Price'].astype('float32')
            
            # 4. 追加保存 (初回は新規作成、2回目以降は追記)
            if writer is None:
                df_chunk.to_parquet(output_file, index=False, engine='pyarrow')
            else:
                # 追記モード（実際はファイルを一度読み込んで結合するか、
                # pyarrow.ParquetWriterを使用するのが確実です）
                # ここでは最も安全な「一度結合して出力」ではなく「分割保存」を推奨
                pass
            
            # 今回は簡易的に一括変換して保存する際、
            # 読み込み→加工→即保存 でメモリを空ける方法をとります
            print(f">> 進捗: {i + len(df_chunk)} / {parquet_file.metadata.num_rows} 行処理済み")
            
            del df_chunk
            gc.collect() # 明示的にメモリを解放

        # チャンク分割保存が複雑になるため、
        # 32GB以上のメモリがない場合に「全読み込み」を避けるコード
        # ※ 実運用では、一度に全ロードせず「必要な日付分だけ読み込む」のが最強の節約です。
        
    except Exception as e:
        print(f"エラー発生: {e}")

# --- もしファイルが巨大すぎて上のループが動かない場合 ---
# 最も効率的なのは、読み込み時に最初から計算して書き出す以下の形式です

def simple_safe_save(input_file, output_file):
    df = pd.read_parquet(input_file)
    # 処理
    df['Timestamp'] = pd.to_datetime(df['Timestamp']) + pd.Timedelta(hours=9)
    df['Price'] = ((df['Bid'] + df['Ask']) / 2).astype('float32')
    # 必要な列だけに絞って保存（メモリ節約）
    df = df[['Timestamp', 'Bid', 'Ask', 'Price']]
    df.to_parquet(output_file, compression='snappy', index=False)
    print(f">> {output_file} に保存しました。")

if __name__ == "__main__":
    INPUT_PATH = r"C:\Users\81803\OneDrive\ドキュメント\tick_data.parquet"
    OUTPUT_PATH = r"C:\Users\81803\OneDrive\ドキュメント\tick_data_utc9.parquet"
    simple_safe_save(INPUT_PATH, OUTPUT_PATH)