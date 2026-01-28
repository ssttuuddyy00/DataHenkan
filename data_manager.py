import pandas as pd
import os
import config  # ← これを追加

def load_csv(path):
    # キャッシュ（Pickle）があれば高速読み込み
    cache_path = path.replace(".csv", ".pkl")
    if os.path.exists(cache_path):
        return pd.read_pickle(cache_path)

    print(f"データを解析中: {os.path.basename(path)}")
    # CSV読み込み
    df = pd.read_csv(path)
    
    # 1. 列名の正規化（先頭大文字、それ以外小文字）
    df.columns = [c.capitalize() for c in df.columns]
    
    # 2. 日時情報の合成
    # DateTime列(2004-01-01)とHour, Minuteを組み合わせて完全な日時を作る
    try:
        # DateTimeがすでに日付形式なら、その年月日を取得
        temp_date = pd.to_datetime(df["Datetime"])
        
        # 時・分を合成して新しいDate列を作成
        df["Date"] = pd.to_datetime({
            'year': temp_date.dt.year,
            'month': temp_date.dt.month,
            'day': temp_date.dt.day,
            'hour': df["Hour"],
            'minute': df["Minute"]
        })
    except Exception as e:
        print(f"日時変換エラー: {e}")
        # 予備の変換ロジック（DateTime列がない場合など）
        df["Date"] = pd.to_datetime(df[["Year", "Month", "Day", "Hour", "Minute"]])

    # 3. 必要な列だけに絞って整理
    df = df.drop_duplicates(subset="Date", keep="last")
    df.set_index("Date", inplace=True)
    
    # 必要な4本値だけを抽出してソート
    df = df[["Open", "High", "Low", "Close"]].sort_index()

    # 次回のためにキャッシュ保存
    df.to_pickle(cache_path)
    return df