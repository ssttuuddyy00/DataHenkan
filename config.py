import os
# =========================
# 1. 設定・パス
# =========================
PATHS = {
    "MN":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/A_data.csv",
    "D1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/C_data.csv",
    "H1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/F_data.csv",
    "M15": r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/G_data.csv",
    "M5":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/H_data.csv",
    "M1":  r"C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData/I_data.csv"
}

WINDOW_SIZES = {"MN": 60, "D1": 100, "H1": 150, "M15": 200, "M5": 250, "M1": 300}
VIEW_MAP = {"1": "H1", "2": "D1", "3": "MN", "4": "M15", "5": "M5", "6": "M1"}
INITIAL_BALANCE = 1500000.0
RISK_PER_TRADE = 10000.0
# 自分の好きなフォルダを指定
RESULT_SAVE_DIR = r"C:\Users\81803\OneDrive\画像\リプレイ画像"