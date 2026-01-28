import pandas as pd
import numpy as np

def analyze_tick_data(file_path, tick_window=1000):
    # 1. データの読み込み
    # Timestamp, Bid, Ask, BidVolume, AskVolume の形式に対応
    df = pd.read_csv(file_path)
    
    # 型変換：Timestampをdatetime型に、価格をfloat型に
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Price'] = (df['Bid'] + df['Ask']) / 2
    
    # --- 指標計算 ---
    # A. ティック間隔 (秒)
    df['Gap'] = df['Timestamp'].diff().dt.total_seconds()
    
    # B. ティック・インバランス (前のティックより上がったか下がったか)
    df['Direction'] = np.sign(df['Price'].diff()).fillna(0)
    
    # --- 1000ティック・バーの生成 ---
    df['Group_ID'] = np.arange(len(df)) // tick_window
    
    def calculate_tick_metrics(group):
        open_p = group['Price'].iloc[0]
        high_p = group['Price'].max()
        low_p = group['Price'].min()
        close_p = group['Price'].iloc[-1]
        
        # 1. 買いティック数 vs 売りティック数
        buy_count = (group['Direction'] == 1).sum()
        sell_count = (group['Direction'] == -1).sum()
        
        # 2. 一直線度 (Efficiency Ratio)
        net_move = abs(close_p - open_p)
        total_path = group['Price'].diff().abs().sum()
        efficiency = net_move / total_path if total_path != 0 else 0
        
        # 3. 足の完成にかかった時間（秒）
        duration = (group['Timestamp'].iloc[-1] - group['Timestamp'].iloc[0]).total_seconds()
        
        return pd.Series({
            'Open': open_p, 'High': high_p, 'Low': low_p, 'Close': close_p,
            'Duration_Sec': duration,    # 密度：短いほど高密度
            'Buy_Count': buy_count,      # 買いの勢い
            'Sell_Count': sell_count,    # 売りの勢い
            'Efficiency': efficiency,    # 直線性：1に近いほど強いトレンド
            'StartTime': group['Timestamp'].iloc[0]
        })

    # 集計実行
    tick_bars = df.groupby('Group_ID').apply(calculate_tick_metrics)
    
    return tick_bars

# res = analyze_tick_data('your_data.csv')