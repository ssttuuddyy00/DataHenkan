import pandas as pd
import os

# --- 設定 ---
input_file = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/EURUSD/UTC9/output_M1_UTC+9.csv"
output_dir = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData"
os.makedirs(output_dir, exist_ok=True)

def get_session(hour):
    if 9 <= hour < 16: return '日本'
    elif 16 <= hour < 24 or 0 <= hour < 1: return 'ロンドン'
    elif 22 <= hour < 24 or 0 <= hour < 6: return 'NY'
    else: return 'オセアニア'

def add_time_info(df_resampled, freq_label):
    """集計後のデータに対して時間情報を付与"""
    dt = df_resampled.index
    df_resampled['Year'] = dt.year.astype('int16')
    df_resampled['Month'] = dt.month.astype('int8')
    df_resampled['Day'] = dt.day.astype('int8')
    df_resampled['Hour'] = dt.hour.astype('int8')
    df_resampled['Minute'] = dt.minute.astype('int8')
    df_resampled['Weekday'] = dt.dayofweek.map({0:'月', 1:'火', 2:'水', 3:'木', 4:'金', 5:'土', 6:'日'})
    
    # タイムレンジ生成（分足・時間足のみ）
    if any(x in freq_label for x in ['min', 'H', 'T']):
        m_delta = pd.Timedelta(minutes=30 if freq_label=='30min' else 15 if freq_label=='15min' else 5 if freq_label=='5min' else 1 if freq_label=='1min' else 0)
        h_delta = pd.Timedelta(hours=4 if freq_label=='4H' else 1 if freq_label=='1H' else 0)
        delta = m_delta if m_delta.seconds > 0 else h_delta
        df_resampled['TimeRange'] = dt.strftime('%H:%M') + '-' + (dt + delta).strftime('%H:%M')
    
    return df_resampled

# 1. データの読み込み
print("データを読み込んでいます...")
df = pd.read_csv(
    input_file, 
    usecols=['Date', 'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    dtype={'Date': str, 'Timestamp': str}
)
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'], format='%Y%m%d %H:%M:%S')
df.set_index('DateTime', inplace=True)
df.drop(['Date', 'Timestamp'], axis=1, inplace=True)

agg_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}

# 時間足の定義
timeframes = {
    'A': 'ME',     # 月
    'B': 'W-MON',  # 週
    'C': 'D',      # 日
    'E': '4H',     # 4H
    'F': '1H',     # 1H
    'G': '15min',  # 15M
    'H': '5min',   # 5M
    'I': '1min',   # 1M
    'J': '30min'   # 30M
}

base_data = {}

# 単独ファイル作成
print("\n=== 単独ファイル作成 ===")
for key, freq in timeframes.items():
    print(f"処理中: {key} ({freq})...")
    resampled = df.resample(freq).agg(agg_dict).dropna()
    resampled = add_time_info(resampled, freq)
    resampled.to_csv(os.path.join(output_dir, f"{key}_data.csv"), encoding='utf-8-sig')
    base_data[key] = resampled

# D (セッション足) の作成
print("処理中: D (Session)...")
df_d = df.copy()
df_d['Hour'] = df_d.index.hour
df_d['Session'] = df_d['Hour'].apply(get_session)
session_data = df_d.groupby([df_d.index.date, 'Session']).agg(agg_dict).reset_index()
session_data.to_csv(os.path.join(output_dir, "D_data.csv"), index=False, encoding='utf-8-sig')
base_data['D'] = session_data

# 組み合わせファイルの作成 (例: A-C 月別の日足 など)
print("\n=== 組み合わせファイル作成 ===")
# A(月), B(週), C(日) をベースに他の足を組み合わせる
combos = [('A', 'C'), ('A', 'D'), ('B', 'F'), ('C', 'F'), ('C', 'I')] # 必要に応じて追加

for parent, child in combos:
    filename = f"{parent}-{child}_data.csv"
    print(f"作成中: {filename}")
    # すでに集計済みの child データがあるので、それをそのまま流用して保存
    base_data[child].to_csv(os.path.join(output_dir, filename), encoding='utf-8-sig')

print("\nすべて完了しました！")