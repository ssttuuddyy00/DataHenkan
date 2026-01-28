import pandas as pd
import numpy as np

def analyze_tick_data(file_path, tick_window=1000):
    """
    ティックデータを読み込み、5つの主要指標を計算する関数
    """
    # 1. データの読み込み (Tickstoryの形式に合わせて調整してください)
    # Time, Bid, Ask, BidVolume, AskVolume を想定
    df = pd.read_csv(file_path, parse_dates=['Time'])
    
    # 中間価格の計算
    df['Price'] = (df['Bid'] + df['Ask']) / 2
    
    # --- アイデア1 & 2: ティック密度と間隔 (Time Gap) ---
    # 前のティックとの時間差（秒）
    df['Duration'] = df['Time'].diff().dt.total_seconds()
    
    # --- アイデア3: 買いvs売りインバランス (Tick Rule) ---
    # 前の価格より上がれば+1(買い)、下がれば-1(売り)
    df['Tick_Direction'] = np.sign(df['Price'].diff()).fillna(0)

    # --- アイデア4 & 5: 1000ティック・バーの生成と効率性分析 ---
    # tick_windowごとにグループ化するためのIDを作成
    df['Group_ID'] = np.arange(len(df)) // tick_window
    
    def calculate_metrics(group):
        # 4本値(OHLC)
        open_p = group['Price'].iloc[0]
        high_p = group['Price'].max()
        low_p = group['Price'].min()
        close_p = group['Price'].iloc[-1]
        
        # 1. 価格の上下勝負 (Buy/Sell Imbalance)
        buy_ticks = (group['Tick_Direction'] == 1).sum()
        sell_ticks = (group['Tick_Direction'] == -1).sum()
        
        # 2. 直線性 (Efficiency Ratio)
        net_move = abs(close_p - open_p)
        total_move = group['Price'].diff().abs().sum()
        efficiency = net_move / total_move if total_move != 0 else 0
        
        # 3. 足の完成にかかった時間 (Time Stretch)
        time_taken = (group['Time'].iloc[-1] - group['Time'].iloc[0]).total_seconds()
        
        return pd.Series({
            'Open': open_p, 'High': high_p, 'Low': low_p, 'Close': close_p,
            'StartTime': group['Time'].iloc[0],
            'Duration_Sec': time_taken,    # 足の完成時間
            'Buy_Ticks': buy_ticks,        # 買いティック数
            'Sell_Ticks': sell_ticks,      # 売りティック数
            'Efficiency': efficiency       # 一直線度(1に近いほど一直線)
        })

    # 1000ティックごとの統計量を算出
    tick_bars = df.groupby('Group_ID').apply(calculate_metrics)
    
    return tick_bars

# 実行例
# res = analyze_tick_data('eurusd_ticks.csv', tick_window=1000)
# print(res.head())