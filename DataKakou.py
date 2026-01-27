import pandas as pd
import os
from datetime import datetime, timedelta

# 入力ファイルパス
input_file = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/EURUSD/UTC9/output_M1_UTC+9.csv"

# 出力ディレクトリ
output_dir = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData"

# 出力ディレクトリが存在しない場合は作成
os.makedirs(output_dir, exist_ok=True)

# データ読み込み（メモリ効率化）
print("データを読み込んでいます...")

# 型を指定してメモリ使用量を削減
dtype_dict = {
    'Date': str,
    'Timestamp': str,
    'Open': 'float32',
    'High': 'float32',
    'Low': 'float32',
    'Close': 'float32',
    'Volume': 'float32'
}

# チャンクサイズを指定して読み込み（メモリ節約）
try:
    df = pd.read_csv(input_file, dtype=dtype_dict)
    print(f"データ読み込み完了: {len(df):,} 行")
except Exception as e:
    print(f"エラー: データの読み込みに失敗しました - {e}")
    exit()

# 日時カラムの処理（データはUTC+9、日本時間）
print("日時データを処理中...")
df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'], format='%Y%m%d %H:%M:%S')

# 元のDate, Timestampカラムを削除してメモリ節約
df = df.drop(['Date', 'Timestamp'], axis=1)

# 月、日、曜日、時間、分の抽出（UTC+9基準）
print("時間情報を抽出中...")
df['Year'] = df['DateTime'].dt.year.astype('int16')
df['Month'] = df['DateTime'].dt.month.astype('int8')
df['Day'] = df['DateTime'].dt.day.astype('int8')
df['DayOfWeek'] = df['DateTime'].dt.dayofweek.astype('int8')  # 0=月曜日
df['Minute'] = df['DateTime'].dt.minute.astype('int8')

# 曜日の日本語名を取得
df['Weekday'] = df['DayOfWeek'].map({
    0: '月曜日',
    1: '火曜日',
    2: '水曜日',
    3: '木曜日',
    4: '金曜日',
    5: '土曜日',
    6: '日曜日'
})

df['Hour'] = df['DateTime'].dt.hour.astype('int8')

# セッション判定関数（UTC+9 / 日本時間基準）
print("セッション情報を計算中...")
def get_session(hour):
    if 9 <= hour < 16:
        return '日本'
    elif 16 <= hour < 24 or 0 <= hour < 1:
        return 'ロンドン'
    elif 22 <= hour < 24 or 0 <= hour < 6:
        return 'NY'
    else:
        return 'オセアニア'

df['Session'] = df['Hour'].apply(get_session)

# 時間範囲の計算
print("時間範囲を計算中...")

# 4時間ごとの時間帯
df['Hour4Group'] = (df['Hour'] // 4) * 4
df['Hour4End'] = (df['Hour4Group'] + 4) % 24
df['Hour4Range'] = df['Hour4Group'].astype(str).str.zfill(2) + ':00-' + df['Hour4End'].astype(str).str.zfill(2) + ':00'

# 1時間ごとの時間帯
df['Hour1End'] = (df['Hour'] + 1) % 24
df['Hour1Range'] = df['Hour'].astype(str).str.zfill(2) + ':00-' + df['Hour1End'].astype(str).str.zfill(2) + ':00'

# 15分ごとの時間帯
df['Minute15Group'] = (df['Minute'] // 15) * 15
df['Minute15End'] = (df['Minute15Group'] + 15) % 60
df['Hour15End'] = df['Hour'] + ((df['Minute15Group'] + 15) // 60)
df['Hour15End'] = df['Hour15End'] % 24
df['Minute15Range'] = (df['Hour'].astype(str).str.zfill(2) + ':' + 
                        df['Minute15Group'].astype(str).str.zfill(2) + '-' +
                        df['Hour15End'].astype(str).str.zfill(2) + ':' + 
                        df['Minute15End'].astype(str).str.zfill(2))

# 5分ごとの時間帯
df['Minute5Group'] = (df['Minute'] // 5) * 5
df['Minute5End'] = (df['Minute5Group'] + 5) % 60
df['Hour5End'] = df['Hour'] + ((df['Minute5Group'] + 5) // 60)
df['Hour5End'] = df['Hour5End'] % 24
df['Minute5Range'] = (df['Hour'].astype(str).str.zfill(2) + ':' + 
                       df['Minute5Group'].astype(str).str.zfill(2) + '-' +
                       df['Hour5End'].astype(str).str.zfill(2) + ':' + 
                       df['Minute5End'].astype(str).str.zfill(2))

# 1分ごとの時間帯
df['Minute1End'] = (df['Minute'] + 1) % 60
df['Hour1MinEnd'] = df['Hour'] + ((df['Minute'] + 1) // 60)
df['Hour1MinEnd'] = df['Hour1MinEnd'] % 24
df['Minute1Range'] = (df['Hour'].astype(str).str.zfill(2) + ':' + 
                       df['Minute'].astype(str).str.zfill(2) + '-' +
                       df['Hour1MinEnd'].astype(str).str.zfill(2) + ':' + 
                       df['Minute1End'].astype(str).str.zfill(2))

# 30分ごとの時間帯
df['Minute30Group'] = (df['Minute'] // 30) * 30
df['Minute30End'] = (df['Minute30Group'] + 30) % 60
df['Hour30End'] = df['Hour'] + ((df['Minute30Group'] + 30) // 60)
df['Hour30End'] = df['Hour30End'] % 24
df['Minute30Range'] = (df['Hour'].astype(str).str.zfill(2) + ':' + 
                        df['Minute30Group'].astype(str).str.zfill(2) + '-' +
                        df['Hour30End'].astype(str).str.zfill(2) + ':' + 
                        df['Minute30End'].astype(str).str.zfill(2))

# 不要な中間カラムを削除してメモリ節約
print("不要なデータを削除中...")
df = df.drop(['DateTime', 'DayOfWeek', 'Hour4End', 'Hour1End', 'Hour15End', 'Hour5End', 
              'Hour1MinEnd', 'Hour30End', 'Minute15End', 'Minute5End', 'Minute1End', 
              'Minute30End', 'Hour4Group', 'Minute15Group', 'Minute5Group', 'Minute30Group'], 
             axis=1, errors='ignore')

# 集約関数
agg_dict = {
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}

# 列名を統一するための関数
def standardize_columns(data):
    """列名を統一されたフォーマットに変換"""
    rename_dict = {
        'Year': 'Year',
        'Month': 'Month',
        'Day': 'Day',
        'Weekday': 'Weekday',
        'Session': 'Session',
        'Hour4Range': 'TimeRange',
        'Hour1Range': 'TimeRange',
        'Minute15Range': 'TimeRange',
        'Minute5Range': 'TimeRange',
        'Minute1Range': 'TimeRange',
        'Minute30Range': 'TimeRange',
        'Hour': 'Hour',
        'Minute': 'Minute',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    }
    
    # 存在する列のみリネーム
    cols_to_rename = {k: v for k, v in rename_dict.items() if k in data.columns}
    return data.rename(columns=cols_to_rename)

# グループ化のキー定義
group_keys = {
    'A': ['Year', 'Month'],  # 月
    'B': ['Year', 'Month', 'Day', 'Weekday'],  # 日
    'C': ['Year', 'Month', 'Day', 'Weekday', 'Session'],  # セッション
    'D': ['Year', 'Month', 'Day', 'Weekday', 'Hour4Range'],  # 4時間
    'E': ['Year', 'Month', 'Day', 'Weekday', 'Hour', 'Hour1Range'],  # 1時間
    'F': ['Year', 'Month', 'Day', 'Weekday', 'Hour', 'Minute15Range'],  # 15分
    'G': ['Year', 'Month', 'Day', 'Weekday', 'Hour', 'Minute5Range'],  # 5分
    'H': ['Year', 'Month', 'Day', 'Weekday', 'Hour', 'Minute', 'Minute1Range'],  # 1分
    'I': ['Year', 'Month', 'Day', 'Weekday', 'Hour', 'Minute30Range']  # 30分
}

print("\nデータファイルを作成しています...")

# 単独ファイル作成（A～H）
print("\n=== 単独ファイル作成 ===")
for key, groups in group_keys.items():
    filename = f"{key}_data.csv"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"{key}. {filename} は既に存在します。スキップします。")
        continue
    
    print(f"{key}. {key}のデータを作成中...")
    data = df.groupby(groups).agg(agg_dict).reset_index()
    data = standardize_columns(data)
    data.to_csv(filepath, index=False, encoding='utf-8-sig')

# 組み合わせファイル作成
print("\n=== 組み合わせファイル作成 ===")

# A と B~I の組み合わせ
print("\n--- A と B~I の組み合わせ ---")
for target_key in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
    filename = f"A-{target_key}_data.csv"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"{filename} は既に存在します。スキップします。")
        continue
    
    print(f"A-{target_key}のデータを作成中...")
    combined_keys = group_keys['A'] + [k for k in group_keys[target_key] if k not in group_keys['A']]
    data = df.groupby(combined_keys).agg(agg_dict).reset_index()
    data = standardize_columns(data)
    data.to_csv(filepath, index=False, encoding='utf-8-sig')

# B と C~I の組み合わせ
print("\n--- B と C~I の組み合わせ ---")
for target_key in ['C', 'D', 'E', 'F', 'G', 'H', 'I']:
    filename = f"B-{target_key}_data.csv"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"{filename} は既に存在します。スキップします。")
        continue
    
    print(f"B-{target_key}のデータを作成中...")
    combined_keys = group_keys['B'] + [k for k in group_keys[target_key] if k not in group_keys['B']]
    data = df.groupby(combined_keys).agg(agg_dict).reset_index()
    data = standardize_columns(data)
    data.to_csv(filepath, index=False, encoding='utf-8-sig')

# A-B と C~I の組み合わせ
print("\n--- A-B と C~I の組み合わせ ---")
ab_keys = group_keys['A'] + [k for k in group_keys['B'] if k not in group_keys['A']]
for target_key in ['C', 'D', 'E', 'F', 'G', 'H', 'I']:
    filename = f"A-B-{target_key}_data.csv"
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        print(f"{filename} は既に存在します。スキップします。")
        continue
    
    print(f"A-B-{target_key}のデータを作成中...")
    combined_keys = ab_keys + [k for k in group_keys[target_key] if k not in ab_keys]
    data = df.groupby(combined_keys).agg(agg_dict).reset_index()
    data = standardize_columns(data)
    data.to_csv(filepath, index=False, encoding='utf-8-sig')

print("\n" + "="*60)
print("完了しました！")
print(f"すべてのファイルが {output_dir} に保存されました。")
print("="*60)
print("\n作成されたファイルの例:")
print("【単独】")
print("- A_data.csv (月別)")
print("- B_data.csv (日別)")
print("- C_data.csv (セッション別)")
print("- D_data.csv (4時間別)")
print("- E_data.csv (1時間別)")
print("- F_data.csv (15分別)")
print("- G_data.csv (5分別)")
print("- H_data.csv (1分別)")
print("- I_data.csv (30分別)")
print("\n【A と B~I の組み合わせ】")
print("- A-B_data.csv (12月の1日データなど)")
print("- A-C_data.csv (12月のロンドン時間のデータなど)")
print("など...")
print("\n【B と C~I の組み合わせ】")
print("- B-C_data.csv (5日のロンドン時間のデータなど)")
print("- B-H_data.csv (5日の23:00~23:01のデータなど)")
print("など...")
print("\n【A-B と C~I の組み合わせ】")
print("- A-B-C_data.csv (10月3日のロンドン時間のデータなど)")
print("- A-B-D_data.csv (10月3日の0:00~4:00のデータなど)")
print("など...")
print(f"\n合計 {len([f for f in os.listdir(output_dir) if f.endswith('.csv')])} 個のCSVファイルが作成されました。")