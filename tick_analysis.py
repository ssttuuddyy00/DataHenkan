import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def analyze_tick_data_fast(file_path, tick_window=1000):
    print(f"読み込み中: {file_path}")
    
    # 1. データの読み込み (必要な列に絞る)
    df = pd.read_csv(file_path, usecols=['Timestamp', 'Bid', 'Ask'])
    
    # 型変換の高速化
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Price'] = (df['Bid'] + df['Ask']) / 2
    
    # 2. 基本指標の事前計算
    df['Diff'] = df['Price'].diff()
    df['Direction'] = np.sign(df['Diff']).fillna(0)
    df['Abs_Diff'] = df['Diff'].abs()

    # 3. 1000ティックごとのグループID作成
    groups = np.arange(len(df)) // tick_window
    grouped = df.groupby(groups)
    
    print("集計処理中...")
    
    # 4. 集計（4本値と各指標）
    agg_df = pd.DataFrame()
    agg_df['StartTime'] = grouped['Timestamp'].first()
    agg_df['Open'] = grouped['Price'].first()
    agg_df['High'] = grouped['Price'].max()
    agg_df['Low'] = grouped['Price'].min()
    agg_df['Close'] = grouped['Price'].last()
    
    # 密度（完成時間）
    agg_df['Duration_Sec'] = (grouped['Timestamp'].last() - grouped['Timestamp'].first()).dt.total_seconds()
    
    # 買いvs売りの数
    # Direction: 1=買い, -1=売り
    agg_df['Buy_Count'] = df['Direction'].where(df['Direction'] == 1).groupby(groups).count()
    agg_df['Sell_Count'] = df['Direction'].where(df['Direction'] == -1).groupby(groups).count()
    
    # 一直線度 (Efficiency Ratio)
    net_move = (agg_df['Close'] - agg_df['Open']).abs()
    total_path = grouped['Abs_Diff'].sum()
    agg_df['Efficiency'] = net_move / total_path
    
    return agg_df

# ==========================================
# 設定エリア：ここを書き換えてください
# ==========================================
# Windowsの人は r'C:\Users\Name\Desktop\EURUSD.csv' のように書く
FILE_PATH = 'ここにファイルのパスを入力してください.csv' 
TICK_NUM = 1000 # 何ティックごとに足をまとめるか

# --- 実行 ---
if __name__ == "__main__":
    try:
        # 分析実行
        res = analyze_tick_data_fast(FILE_PATH, TICK_NUM)
        
        # 結果の表示
        print("\n--- 分析完了 ---")
        print(res.head(10)) # 最初の10行を表示
        
        # 面白いデータの抽出例：一直線度が0.8以上の「本気トレンド」足
        super_trends = res[res['Efficiency'] > 0.8]
        print(f"\n一直線度が高い足の数: {len(super_trends)}")
        
        # CSVに保存する場合
        # res.to_csv('tick_analysis_result.csv')
        
    except FileNotFoundError:
        print("エラー: ファイルが見つかりません。パスが正しいか確認してください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")