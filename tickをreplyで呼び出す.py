import sqlite3

class TickAnalyzer:
    def __init__(self, db_path='tick_analysis.db'):
        self.conn = sqlite3.connect(db_path)

    def get_market_context(self, current_time):
        """
        リプレイ中の時刻(current_time)を渡すと、
        その1分間の需給バランスや逆行の有無を返す
        """
        # 秒を切り捨てて1分単位に合わせる
        query_time = current_time.replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        query = f"SELECT * FROM stats_1min WHERE Timestamp = '{query_time}'"
        res = pd.read_sql(query, self.conn)
        
        if res.empty:
            return None
            
        data = res.iloc[0]
        # 分析ロジックをリターン
        return {
            "Buy_Ratio": data['Buy_Ticks'] / data['Tick_Count'],
            "Density": data['Tick_Count'],
            "Is_Absorption": (data['Buy_Ticks'] / data['Tick_Count'] > 0.6) and (data['Price_Close'] < data['Price_Open'])
        }

# --- リプレイスクリプト内での使用例 ---
# analyzer = TickAnalyzer()
# context = analyzer.get_market_context(current_replay_time)
# if context and context['Is_Absorption']:
#     print(f"警告：このエントリーポイントでは大口の吸収（売り壁）が発生しています！")