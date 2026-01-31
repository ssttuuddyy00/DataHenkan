import os
# =========================
# 1. 設定・パス
# =========================
# --- config.py ---
PATHS = {
    "MN":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv",
    "D1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/C_data.csv",
    "H4":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/E_data.csv",
    "H1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/F_data.csv",
    "M15": r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/G_data.csv",
    "M5":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/H_data.csv",
    "M1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/I_data.csv"
}

# H4を追加し、各足の表示本数を調整
WINDOW_SIZES = {
    "MN": 60, "D1": 100, "H4": 120, "H1": 120, "M15": 40, "M5": 40, "M1": 20
}

# 番号指定を「月足(1) 〜 M1(7)」に変更
VIEW_MAP = {
    "1": "MN", 
    "2": "D1", 
    "3": "H4", 
    "4": "H1", 
    "5": "M15", 
    "6": "M5", 
    "7": "M1"
}
INITIAL_BALANCE = 1500000.0
RISK_PER_TRADE = 10000.0
# 自分の好きなフォルダを指定
RESULT_SAVE_DIR = r"C:\Users\81803\OneDrive\画像\リプレイ画像"