import pandas as pd
import os

def load_csv(path):
   # キャッシュファイル名を作成 (例: M1_data.csv -> M1_data.pkl)
    cache_path = path.replace(".csv", ".pkl")
    
    # 1. キャッシュが存在すれば、それを読み込む（超高速）
    if os.path.exists(cache_path):
        return pd.read_pickle(cache_path)
    
    # 2. キャッシュがない場合のみ、元のCSVを読み込む
    print(f"CSVから初回読み込み中...: {os.path.basename(path)}")
    df = pd.read_csv(path)
    df.columns = [c.capitalize() for c in df.columns]
    
    # 日時変換
    t = df.copy()
    t["Day"] = t.get("Day", 1)
    t["Hour"] = t.get("Hour", 0)
    t["Minute"] = t.get("Minute", 0)
    df["Date"] = pd.to_datetime(t[["Year", "Month", "Day", "Hour", "Minute"]])
    
    # 重複削除とソート
    df = df.drop_duplicates(subset="Date", keep="last")
    df.set_index("Date", inplace=True)
    df = df[["Open", "High", "Low", "Close"]].sort_index()
    
    # 3. 次回のためにキャッシュとして保存
    df.to_pickle(cache_path)
    return df

DFS = {}
try:
    print("データをロード中... (2回目以降は高速化されます)")
    for tf, path in PATHS.items():
        if os.path.exists(path):
            DFS[tf] = load_csv(path)
        else:
            print(f"Warning: {tf} ファイルが見つかりません: {path}")
    
    # M1を基準足にする
    df_base = DFS["M1"]
    
    # 価格単位の判定
    PIPS_UNIT, ONE_LOT_PIPS_VALUE = (0.01, 1000) if df_base['Close'].iloc[0] > 50 else (0.0001, 1500)
    
    # 最初の表示位置を決定
    # WINDOW_SIZES["M1"] 分の余白を持たせて開始
    start_margin = WINDOW_SIZES["M1"] + 50
    st = StartupSettings(df_base.index[start_margin])
    
    if not st.confirmed: exit()
    
    lot_mode = st.lot_mode
    fixed_lot_size = st.fixed_lot
    # 指定した日時に最も近いインデックスを探す（method='pad'で過去方向の近似値）
    idx_base = df_base.index.get_indexer([st.dt_result], method='pad')[0]
    
    # 範囲外エラー対策
    idx_base = max(start_margin, idx_base)
    
    current_view = "H1"
except Exception as e:
    print(f"Init Error: {e}")
    import traceback
    traceback.print_exc() # 詳細なエラー場所を表示
    exit()
