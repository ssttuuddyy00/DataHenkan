import pandas as pd
import numpy as np

import pandas as pd
import numpy as np

def analyze_tick_data_fast(file_path, tick_window=1000):
    # 1. 読み込み（必要な列だけに絞ってメモリ節約）
    df = pd.read_csv(file_path, usecols=['Timestamp', 'Bid', 'Ask'])
    
    # 型変換の高速化
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Price'] = (df['Bid'] + df['Ask']) / 2
    
    # 不要な列を削除してメモリ解放
    df = df[['Timestamp', 'Price']].copy()

    # 2. 基本指標の計算（ベクトル演算）
    df['Diff'] = df['Price'].diff()
    df['Direction'] = np.sign(df['Diff']).fillna(0)
    df['Abs_Diff'] = df['Diff'].abs()

    # 3. ティック・バーのインデックス計算
    # 1000ティックごとに番号を振る
    n = len(df)
    groups = np.arange(n) // tick_window
    
    # 4. 集計（NumPy/Pandasの集計関数を直接使用）
    # これによりapplyのループを回避
    agg_df = pd.DataFrame()
    
    # 4本値
    grouped = df.groupby(groups)
    agg_df['Open'] = grouped['Price'].first()
    agg_df['High'] = grouped['Price'].max()
    agg_df['Low'] = grouped['Price'].min()
    agg_df['Close'] = grouped['Price'].last()
    
    # 5. 特徴量の計算（一気に計算）
    # Duration: 各グループの最後と最初のTimestampの差
    agg_df['Duration_Sec'] = (grouped['Timestamp'].last() - grouped['Timestamp'].first()).dt.total_seconds()
    
    # Buy/Sell Count
    # Directionが1（買い）と-1（売り）をカウント
    agg_df['Buy_Count'] = df['Direction'].where(df['Direction'] == 1).groupby(groups).count()
    agg_df['Sell_Count'] = df['Direction'].where(df['Direction'] == -1).groupby(groups).count()
    
    # Efficiency: |終値-始値| / 合計移動距離
    net_move = (agg_df['Close'] - agg_df['Open']).abs()
    total_path = df.groupby(groups)['Abs_Diff'].sum()
    agg_df['Efficiency'] = net_move / total_path
    
    # 最初のTime
    agg_df['StartTime'] = grouped['Timestamp'].first()

    return agg_df
res = analyze_tick_data(r"C:\Users\81803\OneDrive\ドキュメント\EURUSD_tick_2004_2025.csv")