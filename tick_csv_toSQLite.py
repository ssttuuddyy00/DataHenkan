import sqlite3
import pandas as pd

def create_lookup_db(stats_1min_path, db_path='tick_analysis.db'):
    """1分足統計CSVを高速検索用のDBに変換する"""
    df = pd.read_csv(stats_1min_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # SQLiteに保存
    conn = sqlite3.connect(db_path)
    df.to_sql('stats_1min', conn, if_exists='replace', index=False)
    
    # 高速化のために「時間」にインデックスを貼る（これが最重要）
    conn.execute("CREATE INDEX idx_timestamp ON stats_1min(Timestamp)")
    conn.close()
    print("高速検索用データベースの作成が完了しました。")

# 一度だけ実行
create_lookup_db('EURUSD_tick_2004_2025_tick_stats_1min.csv')