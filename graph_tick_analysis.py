import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_hybrid_tick_chart(csv_path):
    # 1. データの読み込み
    df = pd.read_csv(csv_path)
    df['StartTime'] = pd.to_datetime(df['StartTime'])
    
    # 巨大すぎる場合は直近1000件程度に絞る（全体を見たい場合はここをコメントアウト）
    df = df.tail(1000)

    # グラフの作成（3段構成）
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True, 
                                       gridspec_kw={'height_ratios': [3, 1, 1]})

    # --- 上段：価格（実時間プロット） ---
    # 散布図と線で「取引の密集度」を表現
    ax1.plot(df['StartTime'], df['Close'], color='blue', alpha=0.6, label='Price (Close)')
    ax1.scatter(df['StartTime'], df['Close'], c=df['Efficiency'], cmap='YlOrRd', s=20, label='Tick Bars')
    ax1.set_title('Hybrid Tick Chart (Dense dots = High Volatility)')
    ax1.legend()

    # --- 中段：ティック密度（Duration） ---
    # 1000ティック溜まるのが「速い」ほど高く表示（1/Duration）
    ax2.bar(df['StartTime'], 1/df['Duration_Sec'], color='green', alpha=0.5, width=0.01)
    ax2.set_title('Tick Density (Spikes = High Activity / News)')
    ax2.set_ylabel('1 / Duration')

    # --- 下段：一直線度（Efficiency） ---
    ax3.fill_between(df['StartTime'], df['Efficiency'], color='orange', alpha=0.3)
    ax3.plot(df['StartTime'], df['Efficiency'], color='orange', linewidth=1)
    ax3.set_title('Efficiency Ratio (1.0 = Laser Straight)')
    ax3.set_ylim(0, 1)

    # 時間軸の設定
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.show()

# 実行
# plot_hybrid_tick_chart('C:/Users/81803/OneDrive/ドキュメント/EURUSD_tick_2004_2025_analyzed_1000tick.csv')