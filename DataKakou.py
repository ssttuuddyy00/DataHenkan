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
    """集計後の小さなデータに対して時間情報を付与する（効率的）"""
    dt = df_resampled.index
    df_resampled['Year'] = dt.year.astype('int16')
    df_resampled['Month'] = dt.month.astype('int8')
    df_resampled['Day'] = dt.day.astype('int8')
    df_resampled['Hour'] = dt.hour.astype('int8')
    df_resampled['Minute'] = dt.minute.astype('int8')
    df_resampled['Weekday'] = dt.day_name() # または map で日本語化
    df_resampled['Session'] = df_resampled['Hour'].apply(get_session)
    
    # タイムレンジ文字列の生成（行数が減った後なので高速）
    if 'T' in freq_label or 'min' in freq_label or freq_label == '1min':
        m = int(freq_label.replace('min', '').replace('T', ''))
        df_resampled['TimeRange'] = dt.strftime('%H:%M') + '-' + (dt + pd.Timedelta(minutes=m)).strftime('%H:%M')
    elif 'H' in freq_label:
        h = int(freq_label.replace('H', ''))
        df_resampled['TimeRange'] = dt.strftime('%H:%M') + '-' + (dt + pd.Timedelta(hours=h)).strftime('%H:%M')
    
    return df_resampled

# 1. データの読み込み（DateTimeをインデックスとして読み込む）
print("データを読み込んでいます...")
df = pd.read_csv(input_file, usecols=['Date', 'Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'], format='%Y%m%d %H:%M:%S')
df.set_index('DateTime', inplace=True)
df.drop(['Date', 'Timestamp'], axis=1, inplace=True)

# 集計ルール
agg_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}

# 作成したい時間足リスト
timeframes = {
    'A': 'ME',    # 月次 (Month End)
    'B': 'D',     # 日次
    'D': '4H',    # 4時間
    'E': '1H',    # 1時間
    'I': '30min', # 30分
    'F': '15min', # 15分
    'G': '5min',  # 5分
    'H': '1min'   # 1分
}

# 各時間足のベースデータ作成と保存
base_data = {}
print("\n=== 各時間足のデータ作成 ===")
for key, freq in timeframes.items():
    print(f"処理中: {key} ({freq})...")
    resampled = df.resample(freq).agg(agg_dict).dropna()
    resampled = add_time_info(resampled, freq)
    
    filename = f"{key}_data.csv"
    resampled.to_csv(os.path.join(output_dir, filename), encoding='utf-8-sig')
    base_data[key] = resampled # 組み合わせ用に保持

# セッション別(C)は特殊なので個別作成（1分足ベースから集計）
print("処理中: C (Session)...")
df_c = df.copy()
df_c['Hour'] = df_c.index.hour
df_c['Session'] = df_c['Hour'].apply(get_session)
# 日付とセッションでグループ化
session_data = df_c.groupby([df_c.index.date, 'Session']).agg(agg_dict)
session_data.to_csv(os.path.join(output_dir, "C_data.csv"), encoding='utf-8-sig')
base_data['C'] = session_data

# 組み合わせファイルの作成
print("\n=== 組み合わせファイル作成 ===")
# 例: A-B (月ごとの日別データ) など。
# 既に base_data に各時間足があるので、それを利用して保存するだけ
# ユーザー元のコードにあるような複雑な組み合わせが必要な場合も、
# 巨大な df ではなく、作成済みの base_data['E'] (1H) などから抽出すると速いです。

# 例: A-B, A-C ... のループ（必要に応じて調整してください）
for target in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
    print(f"組み合わせ保存中: A-{target}...")
    # 既に集約済みのデータを使っているので、そのまま保存するか、必要な列で再構成
    base_data[target].to_csv(os.path.join(output_dir, f"A-{target}_data.csv"), encoding='utf-8-sig')

print("\nすべて完了しました！")