import sqlite3
import csv
from datetime import datetime

def create_lookup_db_lightweight(csv_path, db_path=r'C:\Users\81803\OneDrive\ドキュメント\tick_analysis.db', chunk_size=100000):
    """
    メモリを消費せずに巨大CSVをSQLiteに変換する
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. テーブルの作成（CSVのヘッダーに合わせて定義）
    # ※実際のCSVカラム名に合わせて微調整してください
    cursor.execute("DROP TABLE IF EXISTS stats_1min")
    cursor.execute("""
        CREATE TABLE stats_1min (
            Timestamp TEXT,
            Tick_Count INTEGER,
            Avg_Gap REAL,
            Buy_Ticks INTEGER,
            Sell_Ticks INTEGER,
            Price_Open REAL,
            Price_Close REAL
        )
    """)

    print(f"--- 変換開始: {csv_path} ---")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        batch = []
        count = 0

        for row in reader:
            # 必要なデータをタプルとしてまとめる
            batch.append((
                row['Timestamp'],
                int(row['Tick_Count']),
                float(row['Avg_Gap']),
                int(row['Buy_Ticks']),
                int(row['Sell_Ticks']),
                float(row['Price_Open']),
                float(row['Price_Close'])
            ))
            
            # chunk_sizeごとにまとめてDBへ書き込み（メモリ節約と速度の両立）
            if len(batch) >= chunk_size:
                cursor.executemany(
                    "INSERT INTO stats_1min VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    batch
                )
                conn.commit()
                batch = []
                count += chunk_size
                print(f"{count} 行 完了...")

        # 残りのデータを書き込み
        if batch:
            cursor.executemany("INSERT INTO stats_1min VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
            conn.commit()

    # 2. インデックス作成（検索速度のために必須）
    print("インデックスを作成中（これには数分かかる場合があります）...")
    cursor.execute("CREATE INDEX idx_timestamp ON stats_1min(Timestamp)")
    conn.commit()
    
    conn.close()
    print(f"--- すべて完了しました。保存先: {db_path} ---")

# 実行
create_lookup_db_lightweight('C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025_tick_stats_1min.csv')