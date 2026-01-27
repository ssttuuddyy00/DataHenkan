import pandas as pd
import os
import config  # ← これを追加

def load_csv(path):
    # (既存の load_csv の中身はそのままでOK)
    cache_path = path.replace(".csv", ".pkl")
    if os.path.exists(cache_path):
        return pd.read_pickle(cache_path)
    
    print(f"CSVから初回読み込み中...: {os.path.basename(path)}")
    df = pd.read_csv(path)
    df.columns = [c.capitalize() for c in df.columns]
    
    t = df.copy()
    t["Day"] = t.get("Day", 1)
    t["Hour"] = t.get("Hour", 0)
    t["Minute"] = t.get("Minute", 0)
    df["Date"] = pd.to_datetime(t[["Year", "Month", "Day", "Hour", "Minute"]])
    
    df = df.drop_duplicates(subset="Date", keep="last")
    df.set_index("Date", inplace=True)
    df = df[["Open", "High", "Low", "Close"]].sort_index()
    
    df.to_pickle(cache_path)
    return df