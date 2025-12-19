import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import json
from collections import Counter


class ChartAnalyzerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("チャートデータ分析")
        self.root.geometry("1200x900")  # ウィンドウサイズを拡大

        # データディレクトリ
        self.data_dir = "C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData"

        # 履歴ファイル
        self.history_file = (
            "C:/Users/81803/OneDrive/ドキュメント/TyuusyutuKekka_Chart/history.json"
        )
        self.target_history = []
        self.condition_history = []
        self.load_history()

        # タイムフレーム階層マッピング
        self.timeframe_map = {
            "月": "A",
            "日": "B",
            "セッション": "C",
            "H4": "D",
            "H1": "E",
            "M15": "F",
            "M5": "G",
            "M1": "H",
            "M30": "I",
        }

        # セッション時間定義
        self.sessions = {
            "オセアニア": (6, 9),
            "日本": (9, 16),
            "ロンドン": (16, 1),
            "NY": (22, 6),
        }

        self.setup_ui()

    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # カテゴリ1: 抽出内容
        cat1_frame = ttk.LabelFrame(
            main_frame, text="カテゴリ1: 抽出内容", padding="10"
        )
        cat1_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(cat1_frame, text="抽出内容:").grid(row=0, column=0, sticky=tk.W)
        self.extract_type = ttk.Combobox(
            cat1_frame, values=["幅", "陽線確率"], width=15, state="readonly"
        )
        self.extract_type.grid(row=0, column=1, padx=5)
        self.extract_type.current(0)
        self.extract_type.bind("<<ComboboxSelected>>", self.on_extract_type_change)

        ttk.Label(cat1_frame, text="抽出内容詳細:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.extract_detail = ttk.Combobox(
            cat1_frame,
            values=["上幅", "下幅", "実体", "上髭", "下髭"],
            width=15,
            state="readonly",
        )
        self.extract_detail.grid(row=1, column=1, padx=5, pady=5)
        self.extract_detail.current(2)

        # カテゴリ2: 対象
        cat2_frame = ttk.LabelFrame(main_frame, text="カテゴリ2: 対象", padding="10")
        cat2_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 次の足ボタン
        next_candle_frame = ttk.Frame(cat2_frame)
        next_candle_frame.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=5)
        ttk.Label(next_candle_frame, text="特殊:").pack(side=tk.LEFT)
        self.next_candle_btn = ttk.Button(
            next_candle_frame, text="次の足を設定", command=self.set_next_candle_target
        )
        self.next_candle_btn.pack(side=tk.LEFT, padx=5)

        # 上位
        ttk.Label(cat2_frame, text="月:").grid(row=1, column=0, sticky=tk.W)
        self.target_month = ttk.Combobox(
            cat2_frame,
            values=["なし", "全て", "個別全て"] + [f"{i}月" for i in range(1, 13)],
            width=12,
            state="readonly",
        )
        self.target_month.grid(row=1, column=1, padx=5)
        self.target_month.current(0)

        # 中位
        ttk.Label(cat2_frame, text="日:").grid(
            row=1, column=2, sticky=tk.W, padx=(10, 0)
        )
        self.target_day = ttk.Combobox(
            cat2_frame,
            values=["なし", "全て", "個別全て"] + [f"{i}日" for i in range(1, 32)],
            width=12,
            state="readonly",
        )
        self.target_day.grid(row=1, column=3, padx=5)
        self.target_day.current(0)

        # 下位
        ttk.Label(cat2_frame, text="セッション:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.target_session = ttk.Combobox(
            cat2_frame,
            values=["なし", "個別全て"] + list(self.sessions.keys()),
            width=12,
            state="readonly",
        )
        self.target_session.grid(row=2, column=1, padx=5, pady=5)
        self.target_session.current(0)
        self.target_session.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="H4:").grid(
            row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5
        )
        h4_values = ["なし", "個別全て"] + [
            f"{h:02d}:00-{(h+4)%24:02d}:00" for h in range(0, 24, 4)
        ]
        self.target_h4 = ttk.Combobox(
            cat2_frame, values=h4_values, width=15, state="readonly"
        )
        self.target_h4.grid(row=2, column=3, padx=5, pady=5)
        self.target_h4.current(0)
        self.target_h4.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="H1:").grid(row=3, column=0, sticky=tk.W)
        h1_values = ["なし", "個別全て"] + [
            f"{h:02d}:00-{(h+1)%24:02d}:00" for h in range(24)
        ]
        self.target_h1 = ttk.Combobox(
            cat2_frame, values=h1_values, width=15, state="readonly"
        )
        self.target_h1.grid(row=3, column=1, padx=5)
        self.target_h1.current(0)
        self.target_h1.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="M30:").grid(
            row=3, column=2, sticky=tk.W, padx=(10, 0)
        )
        m30_values = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+30:02d}" for h in range(24) for m in [0, 30]
        ]
        self.target_m30 = ttk.Combobox(
            cat2_frame, values=m30_values, width=15, state="readonly"
        )
        self.target_m30.grid(row=3, column=3, padx=5)
        self.target_m30.current(0)
        self.target_m30.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="M15:").grid(row=4, column=0, sticky=tk.W)
        m15_values = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+15:02d}"
            for h in range(24)
            for m in [0, 15, 30, 45]
        ]
        self.target_m15 = ttk.Combobox(
            cat2_frame, values=m15_values, width=15, state="readonly"
        )
        self.target_m15.grid(row=4, column=1, padx=5)
        self.target_m15.current(0)
        self.target_m15.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="M5:").grid(
            row=4, column=2, sticky=tk.W, padx=(10, 0)
        )
        m5_values = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+5:02d}"
            for h in range(24)
            for m in range(0, 60, 5)
        ]
        self.target_m5 = ttk.Combobox(
            cat2_frame, values=m5_values[:50], width=15, state="readonly"
        )
        self.target_m5.grid(row=4, column=3, padx=5)
        self.target_m5.current(0)
        self.target_m5.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        ttk.Label(cat2_frame, text="M1:").grid(row=5, column=0, sticky=tk.W)
        m1_values = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+1:02d}" for h in range(24) for m in range(60)
        ]
        self.target_m1 = ttk.Combobox(
            cat2_frame, values=m1_values[:50], width=15, state="readonly"
        )
        self.target_m1.grid(row=5, column=1, padx=5)
        self.target_m1.current(0)
        self.target_m1.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "target")
        )

        # カテゴリ3: 条件
        cat3_frame = ttk.LabelFrame(main_frame, text="カテゴリ3: 条件", padding="10")
        cat3_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # ★★★ 連続ローソク足条件を追加（最初の行に配置） ★★★
        ttk.Label(cat3_frame, text="連続条件:").grid(row=0, column=0, sticky=tk.W)
        self.cond_consecutive = ttk.Combobox(
            cat3_frame,
            values=["なし", "1", "2", "3", "4", "5", "6"],
            width=8,
            state="readonly",
        )
        self.cond_consecutive.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.cond_consecutive.current(0)

        ttk.Label(cat3_frame, text="本連続:").grid(
            row=0, column=2, sticky=tk.W, padx=(0, 0)
        )
        self.cond_consecutive_type = ttk.Combobox(
            cat3_frame, values=["陽線", "陰線"], width=8, state="readonly"
        )
        self.cond_consecutive_type.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.cond_consecutive_type.current(0)

        # 上位（行番号を1から2に変更）
        ttk.Label(cat3_frame, text="月:").grid(
            row=1, column=0, sticky=tk.W, pady=(10, 0)
        )
        self.cond_month = ttk.Combobox(
            cat3_frame,
            values=["なし", "全て", "個別全て"] + [f"{i}月" for i in range(1, 13)],
            width=12,
            state="readonly",
        )
        self.cond_month.grid(row=1, column=1, padx=5, pady=(10, 0))
        self.cond_month.current(0)

        # 中位
        ttk.Label(cat3_frame, text="日:").grid(
            row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 0)
        )
        self.cond_day = ttk.Combobox(
            cat3_frame,
            values=["なし", "全て", "個別全て"] + [f"{i}日" for i in range(1, 32)],
            width=12,
            state="readonly",
        )
        self.cond_day.grid(row=1, column=3, padx=5, pady=(10, 0))
        self.cond_day.current(0)

        # 下位（以降の行番号を1つずつ増やす）
        ttk.Label(cat3_frame, text="セッション:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.cond_session = ttk.Combobox(
            cat3_frame,
            values=["なし", "個別全て"] + list(self.sessions.keys()),
            width=12,
            state="readonly",
        )
        self.cond_session.grid(row=2, column=1, padx=5, pady=5)
        self.cond_session.current(0)
        self.cond_session.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="H4:").grid(
            row=2, column=2, sticky=tk.W, padx=(10, 0), pady=5
        )
        h4_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:00-{(h+4)%24:02d}:00" for h in range(0, 24, 4)
        ]
        self.cond_h4 = ttk.Combobox(
            cat3_frame, values=h4_values_cond, width=15, state="readonly"
        )
        self.cond_h4.grid(row=2, column=3, padx=5, pady=5)
        self.cond_h4.current(0)
        self.cond_h4.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="H1:").grid(row=3, column=0, sticky=tk.W)
        h1_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:00-{(h+1)%24:02d}:00" for h in range(24)
        ]
        self.cond_h1 = ttk.Combobox(
            cat3_frame, values=h1_values_cond, width=15, state="readonly"
        )
        self.cond_h1.grid(row=3, column=1, padx=5)
        self.cond_h1.current(0)
        self.cond_h1.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="M30:").grid(
            row=3, column=2, sticky=tk.W, padx=(10, 0)
        )
        m30_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+30:02d}" for h in range(24) for m in [0, 30]
        ]
        self.cond_m30 = ttk.Combobox(
            cat3_frame, values=m30_values_cond, width=15, state="readonly"
        )
        self.cond_m30.grid(row=3, column=3, padx=5)
        self.cond_m30.current(0)
        self.cond_m30.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="M15:").grid(row=4, column=0, sticky=tk.W)
        m15_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+15:02d}"
            for h in range(24)
            for m in [0, 15, 30, 45]
        ]
        self.cond_m15 = ttk.Combobox(
            cat3_frame, values=m15_values_cond, width=15, state="readonly"
        )
        self.cond_m15.grid(row=4, column=1, padx=5)
        self.cond_m15.current(0)
        self.cond_m15.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="M5:").grid(
            row=4, column=2, sticky=tk.W, padx=(10, 0)
        )
        m5_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+5:02d}"
            for h in range(24)
            for m in range(0, 60, 5)
        ]
        self.cond_m5 = ttk.Combobox(
            cat3_frame, values=m5_values_cond[:50], width=15, state="readonly"
        )
        self.cond_m5.grid(row=4, column=3, padx=5)
        self.cond_m5.current(0)
        self.cond_m5.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="M1:").grid(row=5, column=0, sticky=tk.W)
        m1_values_cond = ["なし", "個別全て"] + [
            f"{h:02d}:{m:02d}-{h:02d}:{m+1:02d}" for h in range(24) for m in range(60)
        ]
        self.cond_m1 = ttk.Combobox(
            cat3_frame, values=m1_values_cond[:50], width=15, state="readonly"
        )
        self.cond_m1.grid(row=5, column=1, padx=5)
        self.cond_m1.current(0)
        self.cond_m1.bind(
            "<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, "cond")
        )

        ttk.Label(cat3_frame, text="陽線・陰線:").grid(
            row=5, column=2, sticky=tk.W, padx=(10, 0)
        )
        self.cond_candle = ttk.Combobox(
            cat3_frame,
            values=["なし", "個別全て", "陽線", "陰線"],
            width=12,
            state="readonly",
        )
        self.cond_candle.grid(row=5, column=3, padx=5)
        self.cond_candle.current(0)

        # ★★★ カテゴリ4: 条件(もう一つ過去) を追加 ★★★
        cat4_frame = ttk.LabelFrame(main_frame, text="カテゴリ4: 条件(もう一つ過去)", padding="10")
        cat4_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 連続条件
        ttk.Label(cat4_frame, text="連続条件:").grid(row=0, column=0, sticky=tk.W)
        self.cond2_consecutive = ttk.Combobox(cat4_frame, values=["なし", "1", "2", "3", "4", "5", "6"], width=8, state="readonly")
        self.cond2_consecutive.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.cond2_consecutive.current(0)

        ttk.Label(cat4_frame, text="本連続:").grid(row=0, column=2, sticky=tk.W, padx=(0,0))
        self.cond2_consecutive_type = ttk.Combobox(cat4_frame, values=["陽線", "陰線"], width=8, state="readonly")
        self.cond2_consecutive_type.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.cond2_consecutive_type.current(0)

        # 上位
        ttk.Label(cat4_frame, text="月:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        self.cond2_month = ttk.Combobox(cat4_frame, values=["なし", "全て", "個別全て"] + [f"{i}月" for i in range(1, 13)], width=12, state="readonly")
        self.cond2_month.grid(row=1, column=1, padx=5, pady=(10,0))
        self.cond2_month.current(0)

        # 中位
        ttk.Label(cat4_frame, text="日:").grid(row=1, column=2, sticky=tk.W, padx=(10,0), pady=(10,0))
        self.cond2_day = ttk.Combobox(cat4_frame, values=["なし", "全て", "個別全て"] + [f"{i}日" for i in range(1, 32)], width=12, state="readonly")
        self.cond2_day.grid(row=1, column=3, padx=5, pady=(10,0))
        self.cond2_day.current(0)

        # 下位
        ttk.Label(cat4_frame, text="セッション:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cond2_session = ttk.Combobox(cat4_frame, values=["なし", "個別全て"] + list(self.sessions.keys()), width=12, state="readonly")
        self.cond2_session.grid(row=2, column=1, padx=5, pady=5)
        self.cond2_session.current(0)
        self.cond2_session.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="H4:").grid(row=2, column=2, sticky=tk.W, padx=(10,0), pady=5)
        h4_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:00-{(h+4)%24:02d}:00" for h in range(0, 24, 4)]
        self.cond2_h4 = ttk.Combobox(cat4_frame, values=h4_values_cond2, width=15, state="readonly")
        self.cond2_h4.grid(row=2, column=3, padx=5, pady=5)
        self.cond2_h4.current(0)
        self.cond2_h4.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="H1:").grid(row=3, column=0, sticky=tk.W)
        h1_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:00-{(h+1)%24:02d}:00" for h in range(24)]
        self.cond2_h1 = ttk.Combobox(cat4_frame, values=h1_values_cond2, width=15, state="readonly")
        self.cond2_h1.grid(row=3, column=1, padx=5)
        self.cond2_h1.current(0)
        self.cond2_h1.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="M30:").grid(row=3, column=2, sticky=tk.W, padx=(10,0))
        m30_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:{m:02d}-{h:02d}:{m+30:02d}" for h in range(24) for m in [0, 30]]
        self.cond2_m30 = ttk.Combobox(cat4_frame, values=m30_values_cond2, width=15, state="readonly")
        self.cond2_m30.grid(row=3, column=3, padx=5)
        self.cond2_m30.current(0)
        self.cond2_m30.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="M15:").grid(row=4, column=0, sticky=tk.W)
        m15_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:{m:02d}-{h:02d}:{m+15:02d}" for h in range(24) for m in [0, 15, 30, 45]]
        self.cond2_m15 = ttk.Combobox(cat4_frame, values=m15_values_cond2, width=15, state="readonly")
        self.cond2_m15.grid(row=4, column=1, padx=5)
        self.cond2_m15.current(0)
        self.cond2_m15.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="M5:").grid(row=4, column=2, sticky=tk.W, padx=(10,0))
        m5_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:{m:02d}-{h:02d}:{m+5:02d}" for h in range(24) for m in range(0, 60, 5)]
        self.cond2_m5 = ttk.Combobox(cat4_frame, values=m5_values_cond2[:50], width=15, state="readonly")
        self.cond2_m5.grid(row=4, column=3, padx=5)
        self.cond2_m5.current(0)
        self.cond2_m5.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="M1:").grid(row=5, column=0, sticky=tk.W)
        m1_values_cond2 = ["なし", "個別全て"] + [f"{h:02d}:{m:02d}-{h:02d}:{m+1:02d}" for h in range(24) for m in range(60)]
        self.cond2_m1 = ttk.Combobox(cat4_frame, values=m1_values_cond2[:50], width=15, state="readonly")
        self.cond2_m1.grid(row=5, column=1, padx=5)
        self.cond2_m1.current(0)
        self.cond2_m1.bind("<<ComboboxSelected>>", lambda e: self.on_target_lower_change(e, 'cond2'))

        ttk.Label(cat4_frame, text="陽線・陰線:").grid(row=5, column=2, sticky=tk.W, padx=(10,0))
        self.cond2_candle = ttk.Combobox(cat4_frame, values=["なし", "個別全て", "陽線", "陰線"], width=12, state="readonly")
        self.cond2_candle.grid(row=5, column=3, padx=5)
        self.cond2_candle.current(0)

        # 分析ボタンとCSV保存ボタン（rowを3から4に変更）
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        analyze_btn = ttk.Button(button_frame, text="データ分析実行", command=self.analyze_data)
        analyze_btn.grid(row=0, column=0, padx=5)

        save_btn = ttk.Button(button_frame, text="CSVに保存", command=self.save_to_csv)
        save_btn.grid(row=0, column=1, padx=5)

        # 分析結果を保存するための変数
        self.analysis_results = []
        self.current_analysis_info = {}

        # 結果表示エリア（rowを4から5に変更）
        result_frame = ttk.LabelFrame(main_frame, text="分析結果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
       
        self.result_text = tk.Text(result_frame, height=10, width=105)  # 高さを10に縮小
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text['yscrollcommand'] = scrollbar.set
        

        # 履歴表示エリア（rowを5から6に変更）
        history_frame = ttk.LabelFrame(main_frame, text="履歴", padding="10")
        history_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 対象履歴
        target_hist_frame = ttk.Frame(history_frame)
        target_hist_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        ttk.Label(target_hist_frame, text="対象履歴:", font=("", 9, "bold")).pack(
            anchor=tk.W
        )

        self.target_history_listbox = tk.Listbox(
            target_hist_frame, height=8, width=45
        )  # 高さを8に増加
        self.target_history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.target_history_listbox.bind(
            "<<ListboxSelect>>", self.on_target_history_select
        )

        target_scroll = ttk.Scrollbar(
            target_hist_frame,
            orient=tk.VERTICAL,
            command=self.target_history_listbox.yview,
        )
        target_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.target_history_listbox["yscrollcommand"] = target_scroll.set

        # 条件履歴
        cond_hist_frame = ttk.Frame(history_frame)
        cond_hist_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        ttk.Label(cond_hist_frame, text="条件履歴:", font=("", 9, "bold")).pack(
            anchor=tk.W
        )

        self.cond_history_listbox = tk.Listbox(
            cond_hist_frame, height=8, width=45
        )  # 高さを8に増加
        self.cond_history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.cond_history_listbox.bind("<<ListboxSelect>>", self.on_cond_history_select)

        cond_scroll = ttk.Scrollbar(
            cond_hist_frame, orient=tk.VERTICAL, command=self.cond_history_listbox.yview
        )
        cond_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.cond_history_listbox["yscrollcommand"] = cond_scroll.set

        # グリッドの重み付けを設定
        history_frame.columnconfigure(0, weight=1)
        history_frame.columnconfigure(1, weight=1)

        # 履歴を表示
        self.update_history_display()

    def load_history(self):
        """履歴をファイルから読み込む"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.target_history = data.get("target_history", [])
                    self.condition_history = data.get("condition_history", [])
            except Exception as e:
                print(f"履歴読み込みエラー: {e}")
                self.target_history = []
                self.condition_history = []
        else:
            self.target_history = []
            self.condition_history = []

    def save_history(self):
        """履歴をファイルに保存"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'target_history': self.target_history,
                    'condition_history': self.condition_history,
                    'condition2_history': getattr(self, 'condition2_history', [])  # ★追加
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"履歴保存エラー: {e}")

    def add_to_history(self):
        """現在の設定を履歴に追加"""
        # 対象履歴（変更なし）
        target_info = {
            'month': self.target_month.get(),
            'day': self.target_day.get(),
            'session': self.target_session.get(),
            'h4': self.target_h4.get(),
            'h1': self.target_h1.get(),
            'm30': self.target_m30.get(),
            'm15': self.target_m15.get(),
            'm5': self.target_m5.get(),
            'm1': self.target_m1.get()
        }
        
        target_parts = []
        if target_info['month'] != "なし":
            target_parts.append(target_info['month'])
        if target_info['day'] != "なし":
            target_parts.append(target_info['day'])
        for key in ['session', 'h4', 'h1', 'm30', 'm15', 'm5', 'm1']:
            if target_info[key] != "なし":
                target_parts.append(target_info[key])
        
        target_str = " / ".join(target_parts) if target_parts else "未設定"
        
        if target_info not in self.target_history:
            self.target_history.insert(0, target_info)
            self.target_history = self.target_history[:20]
        
        # 条件履歴
        cond_info = {
            'consecutive': self.cond_consecutive.get(),
            'consecutive_type': self.cond_consecutive_type.get(),
            'month': self.cond_month.get(),
            'day': self.cond_day.get(),
            'session': self.cond_session.get(),
            'h4': self.cond_h4.get(),
            'h1': self.cond_h1.get(),
            'm30': self.cond_m30.get(),
            'm15': self.cond_m15.get(),
            'm5': self.cond_m5.get(),
            'm1': self.cond_m1.get(),
            'candle': self.cond_candle.get()
        }
        
        cond_parts = []
        if cond_info['consecutive'] != "なし":
            cond_parts.append(f"{cond_info['consecutive']}本連続{cond_info['consecutive_type']}")
        
        if cond_info['month'] != "なし":
            cond_parts.append(cond_info['month'])
        if cond_info['day'] != "なし":
            cond_parts.append(cond_info['day'])
        for key in ['session', 'h4', 'h1', 'm30', 'm15', 'm5', 'm1']:
            if cond_info[key] != "なし":
                cond_parts.append(cond_info[key])
        if cond_info['candle'] != "なし":
            cond_parts.append(cond_info['candle'])
        
        cond_str = " / ".join(cond_parts) if cond_parts else "未設定"
        
        if cond_info not in self.condition_history:
            self.condition_history.insert(0, cond_info)
            self.condition_history = self.condition_history[:20]
        
        # ★★★ 条件2履歴を追加 ★★★
        if not hasattr(self, 'condition2_history'):
            self.condition2_history = []
        
        cond2_info = {
            'consecutive': self.cond2_consecutive.get(),
            'consecutive_type': self.cond2_consecutive_type.get(),
            'month': self.cond2_month.get(),
            'day': self.cond2_day.get(),
            'session': self.cond2_session.get(),
            'h4': self.cond2_h4.get(),
            'h1': self.cond2_h1.get(),
            'm30': self.cond2_m30.get(),
            'm15': self.cond2_m15.get(),
            'm5': self.cond2_m5.get(),
            'm1': self.cond2_m1.get(),
            'candle': self.cond2_candle.get()
        }
        
        if cond2_info not in self.condition2_history:
            self.condition2_history.insert(0, cond2_info)
            self.condition2_history = self.condition2_history[:20]
        
        self.save_history()
        self.update_history_display()

    def update_history_display(self):
        """履歴表示を更新"""
        # 対象履歴（変更なし）
        self.target_history_listbox.delete(0, tk.END)
        for item in self.target_history:
            parts = []
            if item.get("next_candle", "なし") != "なし":
                parts.append(item["next_candle"])
            if item.get("month", "なし") != "なし":
                parts.append(item["month"])
            if item.get("day", "なし") != "なし":
                parts.append(item["day"])
            for key in ["session", "h4", "h1", "m30", "m15", "m5", "m1"]:
                if item.get(key, "なし") != "なし":
                    parts.append(item[key])
            display_str = " / ".join(parts) if parts else "未設定"
            self.target_history_listbox.insert(tk.END, display_str)

        # 条件履歴 ★連続条件を追加
        self.cond_history_listbox.delete(0, tk.END)
        for item in self.condition_history:
            parts = []
            # ★連続条件を最初に表示
            if item.get("consecutive", "なし") != "なし":
                parts.append(
                    f"{item['consecutive']}本連続{item.get('consecutive_type', '陽線')}"
                )

            if item.get("month", "なし") != "なし":
                parts.append(item["month"])
            if item.get("day", "なし") != "なし":
                parts.append(item["day"])
            for key in ["session", "h4", "h1", "m30", "m15", "m5", "m1"]:
                if item.get(key, "なし") != "なし":
                    parts.append(item[key])
            if item.get("candle", "なし") != "なし":
                parts.append(item["candle"])
            display_str = " / ".join(parts) if parts else "未設定"
            self.cond_history_listbox.insert(tk.END, display_str)

    def on_target_history_select(self, event):
        """対象履歴が選択された時の処理"""
        selection = self.target_history_listbox.curselection()
        if selection:
            idx = selection[0]
            item = self.target_history[idx]

            # プルダウンに反映
            self.set_combobox_value(self.target_month, item.get("month", "なし"))
            self.set_combobox_value(self.target_day, item.get("day", "なし"))
            self.set_combobox_value(self.target_session, item.get("session", "なし"))
            self.set_combobox_value(self.target_h4, item.get("h4", "なし"))
            self.set_combobox_value(self.target_h1, item.get("h1", "なし"))
            self.set_combobox_value(self.target_m30, item.get("m30", "なし"))
            self.set_combobox_value(self.target_m15, item.get("m15", "なし"))
            self.set_combobox_value(self.target_m5, item.get("m5", "なし"))
            self.set_combobox_value(self.target_m1, item.get("m1", "なし"))

    def on_cond_history_select(self, event):
        """条件履歴が選択された時の処理"""
        selection = self.cond_history_listbox.curselection()
        if selection:
            idx = selection[0]
            item = self.condition_history[idx]

            # プルダウンに反映
            self.set_combobox_value(
                self.cond_consecutive, item.get("consecutive", "なし")
            )  # ★追加
            self.set_combobox_value(
                self.cond_consecutive_type, item.get("consecutive_type", "陽線")
            )  # ★追加
            self.set_combobox_value(self.cond_month, item.get("month", "なし"))
            self.set_combobox_value(self.cond_day, item.get("day", "なし"))
            self.set_combobox_value(self.cond_session, item.get("session", "なし"))
            self.set_combobox_value(self.cond_h4, item.get("h4", "なし"))
            self.set_combobox_value(self.cond_h1, item.get("h1", "なし"))
            self.set_combobox_value(self.cond_m30, item.get("m30", "なし"))
            self.set_combobox_value(self.cond_m15, item.get("m15", "なし"))
            self.set_combobox_value(self.cond_m5, item.get("m5", "なし"))
            self.set_combobox_value(self.cond_m1, item.get("m1", "なし"))
            self.set_combobox_value(self.cond_candle, item.get("candle", "なし"))

    def set_combobox_value(self, combobox, value):
        """Comboboxに値を設定"""
        if value in combobox["values"]:
            combobox.set(value)
        else:
            combobox.current(0)

    def set_next_candle_target(self):
        """条件の次の足を対象に自動設定"""
        # 全て・個別全てが選択されていないか確認
        if (
            self.cond_month.get() in ["全て", "個別全て"]
            or self.cond_day.get() in ["全て", "個別全て"]
            or self.cond_session.get() == "個別全て"
            or self.cond_h4.get() == "個別全て"
            or self.cond_h1.get() == "個別全て"
            or self.cond_m30.get() == "個別全て"
            or self.cond_m15.get() == "個別全て"
            or self.cond_m5.get() == "個別全て"
            or self.cond_m1.get() == "個別全て"
            or self.cond_candle.get() == "個別全て"
        ):
            messagebox.showwarning(
                "警告",
                "条件で「全て」または「個別全て」が選択されている場合、\n「次の足」は使用できません。",
            )
            return

        # 条件の選択を取得
        cond_month = self.cond_month.get()
        cond_day = self.cond_day.get()
        cond_lower = self.get_selected_lower_time("cond")

        # 対象を条件の次に設定
        if cond_month != "なし" and cond_month not in ["全て", "個別全て"]:
            # 月の次は翌月
            month_num = int(cond_month.replace("月", ""))
            next_month = (month_num % 12) + 1  # 12月の次は1月
            next_month_str = f"{next_month}月"
            if next_month_str in self.target_month["values"]:
                idx = self.target_month["values"].index(next_month_str)
                self.target_month.current(idx)
        else:
            self.target_month.current(0)

        if cond_day != "なし" and cond_day not in ["全て", "個別全て"]:
            # 日の次は翌日
            day_num = int(cond_day.replace("日", ""))
            next_day = (day_num % 31) + 1  # 31日の次は1日
            next_day_str = f"{next_day}日"
            if next_day_str in self.target_day["values"]:
                idx = self.target_day["values"].index(next_day_str)
                self.target_day.current(idx)
        else:
            self.target_day.current(0)

        # 下位時間の次の足を設定
        if cond_lower:
            time_type, time_value = cond_lower
            if time_value != "個別全て":
                self.set_next_lower_time(time_type, time_value)

    def set_next_lower_time(self, time_type, time_value):
        """下位時間の次の足を設定"""
        if time_type == "セッション":
            sessions = list(self.sessions.keys())
            if time_value in sessions:
                idx = sessions.index(time_value)
                next_idx = (idx + 1) % len(sessions)
                next_session = sessions[next_idx]
                target_idx = self.target_session["values"].index(next_session)
                self.target_session.current(target_idx)

        elif time_type == "H4":
            # H4の次を計算
            match = time_value.split("-")[0]
            hour = int(match.split(":")[0])
            next_hour = (hour + 4) % 24
            next_value = f"{next_hour:02d}:00-{(next_hour+4)%24:02d}:00"
            if next_value in self.target_h4["values"]:
                idx = self.target_h4["values"].index(next_value)
                self.target_h4.current(idx)

        elif time_type == "H1":
            match = time_value.split("-")[0]
            hour = int(match.split(":")[0])
            next_hour = (hour + 1) % 24
            next_value = f"{next_hour:02d}:00-{next_hour:02d}:59"
            # H1のフォーマット修正
            next_value = f"{next_hour:02d}:00-{(next_hour+1)%24:02d}:00"
            if next_value in self.target_h1["values"]:
                idx = self.target_h1["values"].index(next_value)
                self.target_h1.current(idx)

        elif time_type == "M30":
            parts = time_value.split("-")[0].split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            next_minute = (minute + 30) % 60
            next_hour = hour if minute + 30 < 60 else (hour + 1) % 24
            next_value = f"{next_hour:02d}:{next_minute:02d}-{next_hour:02d}:{next_minute+30:02d}"
            if next_value in self.target_m30["values"]:
                idx = self.target_m30["values"].index(next_value)
                self.target_m30.current(idx)

        elif time_type == "M15":
            parts = time_value.split("-")[0].split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            next_minute = (minute + 15) % 60
            next_hour = hour if minute + 15 < 60 else (hour + 1) % 24
            next_value = f"{next_hour:02d}:{next_minute:02d}-{next_hour:02d}:{next_minute+15:02d}"
            if next_value in self.target_m15["values"]:
                idx = self.target_m15["values"].index(next_value)
                self.target_m15.current(idx)

        elif time_type == "M5":
            parts = time_value.split("-")[0].split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            next_minute = (minute + 5) % 60
            next_hour = hour if minute + 5 < 60 else (hour + 1) % 24
            next_value = (
                f"{next_hour:02d}:{next_minute:02d}-{next_hour:02d}:{next_minute+5:02d}"
            )
            if next_value in self.target_m5["values"]:
                idx = self.target_m5["values"].index(next_value)
                self.target_m5.current(idx)

        elif time_type == "M1":
            parts = time_value.split("-")[0].split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            next_minute = (minute + 1) % 60
            next_hour = hour if minute + 1 < 60 else (hour + 1) % 24
            next_value = (
                f"{next_hour:02d}:{next_minute:02d}-{next_hour:02d}:{next_minute+1:02d}"
            )
            if next_value in self.target_m1["values"]:
                idx = self.target_m1["values"].index(next_value)
                self.target_m1.current(idx)

    def on_extract_type_change(self, event=None):
        if self.extract_type.get() == "陽線確率":
            self.extract_detail.config(state="disabled")
        else:
            self.extract_detail.config(state="readonly")

    def on_target_lower_change(self, event, category):
         # 下位で一つ選択されたら他を「なし」にする
        sender = event.widget if event else None
        
        if category == 'target':
            lower_combos = [self.target_session, self.target_h4, self.target_h1, 
                        self.target_m30, self.target_m15, self.target_m5, self.target_m1]
        elif category == 'cond':
            lower_combos = [self.cond_session, self.cond_h4, self.cond_h1, 
                        self.cond_m30, self.cond_m15, self.cond_m5, self.cond_m1]
        elif category == 'cond2':  # ★追加
            lower_combos = [self.cond2_session, self.cond2_h4, self.cond2_h1, 
                        self.cond2_m30, self.cond2_m15, self.cond2_m5, self.cond2_m1]
        else:
            return
        
        for combo in lower_combos:
            if combo != sender and sender and sender.get() != "なし":
                combo.current(0)

    def get_file_path(self, month, day, lower_time):
        """選択された条件に基づいてファイルパスを決定"""
        parts = []
        
        # 月の判定
        if month != "なし":
            parts.append(self.timeframe_map["月"])
        
        # 日の判定
        if day != "なし":
            parts.append(self.timeframe_map["日"])
        
        # 下位時間の判定
        if lower_time:
            time_type = lower_time[0]  # ('セッション', value) のタプル
            parts.append(self.timeframe_map[time_type])
        
        if not parts:
            return None
        
        filename = "-".join(parts) + "_data.csv"
        return os.path.join(self.data_dir, filename)

    def load_chart_data(self, month, day, lower_time):
        """選択条件に基づいてチャートデータを読み込む"""
        file_path = self.get_file_path(month, day, lower_time)
        
        if not file_path or not os.path.exists(file_path):
            # ファイルが見つからない場合は None を返す
            return None
        
        try:
            df = pd.read_csv(file_path)
            return df
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    def get_appropriate_data_file(self, target_month, target_day, target_lower, 
                                cond_month, cond_day, cond_lower):
        """対象と条件から適切なデータファイルを決定"""
        # より詳細な時間足のファイルを優先的に読み込む
        
        # 時間足の優先順位（詳細 → 粗い）
        time_priority = {
            "M1": 8,
            "M5": 7,
            "M15": 6,
            "M30": 5,
            "H1": 4,
            "H4": 3,
            "セッション": 2,
            "日": 1,
            "月": 0
        }
        
        # 対象と条件の時間足を取得
        target_time = target_lower[0] if target_lower else None
        cond_time = cond_lower[0] if cond_lower else None
        
        # より詳細な方を選択
        selected_time = None
        if target_time and cond_time:
            if time_priority.get(target_time, -1) > time_priority.get(cond_time, -1):
                selected_time = target_lower
            else:
                selected_time = cond_lower
        elif target_time:
            selected_time = target_lower
        elif cond_time:
            selected_time = cond_lower
        
        # 月・日の判定（対象と条件の両方を考慮）
        selected_month = "なし"
        selected_day = "なし"
        
        if target_month != "なし" or cond_month != "なし":
            # どちらかが指定されていれば、より具体的な方を使用
            if target_month != "なし" and target_month not in ["全て", "個別全て"]:
                selected_month = target_month
            elif cond_month != "なし" and cond_month not in ["全て", "個別全て"]:
                selected_month = cond_month
            elif target_month in ["全て", "個別全て"] or cond_month in ["全て", "個別全て"]:
                selected_month = "全て"  # 全て or 個別全ての場合は全てとして扱う
        
        if target_day != "なし" or cond_day != "なし":
            if target_day != "なし" and target_day not in ["全て", "個別全て"]:
                selected_day = target_day
            elif cond_day != "なし" and cond_day not in ["全て", "個別全て"]:
                selected_day = cond_day
            elif target_day in ["全て", "個別全て"] or cond_day in ["全て", "個別全て"]:
                selected_day = "全て"
        
        # ファイルパスを決定
        file_path = self.get_file_path(selected_month, selected_day, selected_time)
        
        return file_path, selected_month, selected_day, selected_time

    def get_selected_lower_time(self, category):
        """選択された下位時間フィルタを取得"""
        if category == 'target':
            combos = [
                (self.target_session, "セッション"),
                (self.target_h4, "H4"),
                (self.target_h1, "H1"),
                (self.target_m30, "M30"),
                (self.target_m15, "M15"),
                (self.target_m5, "M5"),
                (self.target_m1, "M1")
            ]
        elif category == 'cond':
            combos = [
                (self.cond_session, "セッション"),
                (self.cond_h4, "H4"),
                (self.cond_h1, "H1"),
                (self.cond_m30, "M30"),
                (self.cond_m15, "M15"),
                (self.cond_m5, "M5"),
                (self.cond_m1, "M1")
            ]
        elif category == 'cond2':  # ★追加
            combos = [
                (self.cond2_session, "セッション"),
                (self.cond2_h4, "H4"),
                (self.cond2_h1, "H1"),
                (self.cond2_m30, "M30"),
                (self.cond2_m15, "M15"),
                (self.cond2_m5, "M5"),
                (self.cond2_m1, "M1")
            ]
        else:
            return None
        
        for combo, name in combos:
            value = combo.get()
            if value != "なし":
                return (name, value)
        return None

    def filter_data(self, df, month, day, lower_time, candle_type):
        """データをフィルタリング"""
        if df is None or df.empty:
            return df

        filtered = df.copy()

        # 月フィルタ
        if month != "なし" and "Month" in df.columns:
            if month == "全て":
                pass
            else:
                month_num = int(month.replace("月", ""))
                filtered = filtered[filtered["Month"] == month_num]

        # 日フィルタ
        if day != "なし" and "Day" in df.columns:
            if day == "全て":
                pass
            else:
                day_num = int(day.replace("日", ""))
                filtered = filtered[filtered["Day"] == day_num]

        # 下位時間フィルタ
        if lower_time:
            time_type, time_value = lower_time
            if time_type == "セッション" and "Session" in df.columns:
                filtered = filtered[filtered["Session"] == time_value]
            elif "TimeRange" in df.columns:
                filtered = filtered[filtered["TimeRange"] == time_value]

        # 陽線・陰線フィルタ
        if candle_type == "陽線":
            filtered = filtered[filtered["Close"] > filtered["Open"]]
        elif candle_type == "陰線":
            filtered = filtered[filtered["Close"] < filtered["Open"]]

        return filtered

    def get_individual_all_values(self, filter_type, combo_widget):
        """個別全ての場合に使用する全ての値のリストを取得"""
        values = []

        if filter_type == "月":
            values = [f"{i}月" for i in range(1, 13)]
        elif filter_type == "日":
            values = [f"{i}日" for i in range(1, 32)]
        elif filter_type == "セッション":
            values = list(self.sessions.keys())
        elif filter_type == "H4":
            values = [f"{h:02d}:00-{(h+4)%24:02d}:00" for h in range(0, 24, 4)]
        elif filter_type == "H1":
            values = [f"{h:02d}:00-{(h+1)%24:02d}:00" for h in range(24)]
        elif filter_type == "M30":
            values = [
                f"{h:02d}:{m:02d}-{h:02d}:{m+30:02d}"
                for h in range(24)
                for m in [0, 30]
            ]
        elif filter_type == "M15":
            values = [
                f"{h:02d}:{m:02d}-{h:02d}:{m+15:02d}"
                for h in range(24)
                for m in [0, 15, 30, 45]
            ]
        elif filter_type == "M5":
            values = [
                f"{h:02d}:{m:02d}-{h:02d}:{m+5:02d}"
                for h in range(24)
                for m in range(0, 60, 5)
            ]
        elif filter_type == "M1":
            values = [
                f"{h:02d}:{m:02d}-{h:02d}:{m+1:02d}"
                for h in range(24)
                for m in range(60)
            ]
        elif filter_type == "陽線・陰線":
            values = ["陽線", "陰線"]

        return values

    def analyze_data(self):
        """データ分析を実行"""
        self.result_text.delete(1.0, tk.END)
        self.analysis_results = []  # 結果をクリア
        self.current_analysis_info = {}  # 分析情報をクリア

        # 対象の選択を確認
        target_month = self.target_month.get()
        target_day = self.target_day.get()
        target_lower = self.get_selected_lower_time("target")

        if target_month == "なし" and target_day == "なし" and not target_lower:
            self.result_text.insert(tk.END, "カテゴリ2で対象を選択してください。\n")
            return

        # 分析情報を保存
        self.current_analysis_info = {
            'target_month': target_month,
            'target_day': target_day,
            'target_lower': target_lower,
            'cond_consecutive': self.cond_consecutive.get(),
            'cond_consecutive_type': self.cond_consecutive_type.get(),
            'cond_month': self.cond_month.get(),
            'cond_day': self.cond_day.get(),
            'cond_lower': self.get_selected_lower_time('cond'),
            'cond_candle': self.cond_candle.get(),
            'cond2_consecutive': self.cond2_consecutive.get(),  # ★追加
            'cond2_consecutive_type': self.cond2_consecutive_type.get(),  # ★追加
            'cond2_month': self.cond2_month.get(),  # ★追加
            'cond2_day': self.cond2_day.get(),  # ★追加
            'cond2_lower': self.get_selected_lower_time('cond2'),  # ★追加
            'cond2_candle': self.cond2_candle.get(),  # ★追加
            'extract_type': self.extract_type.get(),
            'extract_detail': self.extract_detail.get()
        }

        if target_month == "なし" and target_day == "なし" and not target_lower:
            self.result_text.insert(tk.END, "カテゴリ2で対象を選択してください。\n")
            return

        # 個別全ての処理
        target_individual_all = None
        if target_month == "個別全て":
            target_individual_all = (
                "月",
                self.get_individual_all_values("月", self.target_month),
            )
        elif target_day == "個別全て":
            target_individual_all = (
                "日",
                self.get_individual_all_values("日", self.target_day),
            )
        elif target_lower and target_lower[1] == "個別全て":
            target_individual_all = (
                target_lower[0],
                self.get_individual_all_values(target_lower[0], None),
            )

        cond_month = self.cond_month.get()
        cond_day = self.cond_day.get()
        cond_lower = self.get_selected_lower_time("cond")
        cond_candle = self.cond_candle.get()

        cond_individual_all = None
        if cond_month == "個別全て":
            cond_individual_all = (
                "月",
                self.get_individual_all_values("月", self.cond_month),
            )
        elif cond_day == "個別全て":
            cond_individual_all = (
                "日",
                self.get_individual_all_values("日", self.cond_day),
            )
        elif cond_lower and cond_lower[1] == "個別全て":
            cond_individual_all = (
                cond_lower[0],
                self.get_individual_all_values(cond_lower[0], None),
            )
        elif cond_candle == "個別全て":
            cond_individual_all = (
                "陽線・陰線",
                self.get_individual_all_values("陽線・陰線", self.cond_candle),
            )

        # 個別全ての場合、それぞれの値について分析を実行
        if target_individual_all:
            filter_type, values = target_individual_all
            for value in values:
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, f"【対象: {value}】\n")
                self.result_text.insert(tk.END, f"{'='*60}\n")

                # 一時的に値を設定
                temp_month = value if filter_type == "月" else target_month
                temp_day = value if filter_type == "日" else target_day
                temp_lower = (
                    (target_lower[0], value)
                    if target_lower and filter_type == target_lower[0]
                    else target_lower
                )

                self.analyze_single_condition(
                    temp_month,
                    temp_day,
                    temp_lower,
                    cond_month,
                    cond_day,
                    cond_lower,
                    cond_candle,
                    cond_individual_all,
                )
        elif cond_individual_all:
            filter_type, values = cond_individual_all
            for value in values:
                self.result_text.insert(tk.END, f"\n{'='*60}\n")
                self.result_text.insert(tk.END, f"【条件: {value}】\n")
                self.result_text.insert(tk.END, f"{'='*60}\n")

                # 一時的に値を設定
                temp_cond_month = value if filter_type == "月" else cond_month
                temp_cond_day = value if filter_type == "日" else cond_day
                temp_cond_lower = (
                    (cond_lower[0], value)
                    if cond_lower and filter_type == cond_lower[0]
                    else cond_lower
                )
                temp_cond_candle = value if filter_type == "陽線・陰線" else cond_candle

                self.analyze_single_condition(
                    target_month,
                    target_day,
                    target_lower,
                    temp_cond_month,
                    temp_cond_day,
                    temp_cond_lower,
                    temp_cond_candle,
                    None,
                )
        else:
            # 通常の単一条件分析
            self.analyze_single_condition(
                target_month,
                target_day,
                target_lower,
                cond_month,
                cond_day,
                cond_lower,
                cond_candle,
                None,
            )

        # 履歴に追加
        self.add_to_history()

    def analyze_single_condition(self, target_month, target_day, target_lower,
                             cond_month, cond_day, cond_lower, cond_candle,
                             cond_individual_all):
        """単一条件での分析を実行"""
        
        # 条件2を取得
        cond2_month = self.cond2_month.get()
        cond2_day = self.cond2_day.get()
        cond2_lower = self.get_selected_lower_time('cond2')
        
        # ★★★ 対象用のデータファイルを読み込む ★★★
        target_file_path = self.get_file_path(target_month, target_day, target_lower)
        
        if not target_file_path or not os.path.exists(target_file_path):
            self.result_text.insert(tk.END, f"対象データファイルが見つかりません。\n")
            self.result_text.insert(tk.END, f"予想ファイル名: {target_file_path}\n\n")
            return
        
        try:
            target_df = pd.read_csv(target_file_path)
            self.result_text.insert(tk.END, f"対象データ読み込み: {len(target_df)}行 (ファイル: {os.path.basename(target_file_path)})\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"対象データ読み込みエラー: {e}\n\n")
            return
        
        # ★★★ 条件1用のデータファイルを読み込む（条件が指定されている場合） ★★★
        cond_df = None
        if cond_month != "なし" or cond_day != "なし" or cond_lower:
            cond_file_path = self.get_file_path(cond_month, cond_day, cond_lower)
            
            if cond_file_path and os.path.exists(cond_file_path):
                try:
                    cond_df = pd.read_csv(cond_file_path)
                    self.result_text.insert(tk.END, f"条件1データ読み込み: {len(cond_df)}行 (ファイル: {os.path.basename(cond_file_path)})\n")
                except Exception as e:
                    self.result_text.insert(tk.END, f"条件1データ読み込みエラー: {e}\n\n")
                    return
            else:
                self.result_text.insert(tk.END, f"条件1データファイルが見つかりません。\n")
                self.result_text.insert(tk.END, f"予想ファイル名: {cond_file_path}\n\n")
                return
        
        # ★★★ 条件2用のデータファイルを読み込む（条件2が指定されている場合） ★★★
        cond2_df = None
        if cond2_month != "なし" or cond2_day != "なし" or cond2_lower:
            cond2_file_path = self.get_file_path(cond2_month, cond2_day, cond2_lower)
            
            if cond2_file_path and os.path.exists(cond2_file_path):
                try:
                    cond2_df = pd.read_csv(cond2_file_path)
                    self.result_text.insert(tk.END, f"条件2データ読み込み: {len(cond2_df)}行 (ファイル: {os.path.basename(cond2_file_path)})\n")
                except Exception as e:
                    self.result_text.insert(tk.END, f"条件2データ読み込みエラー: {e}\n\n")
                    return
            else:
                self.result_text.insert(tk.END, f"条件2データファイルが見つかりません。\n")
                self.result_text.insert(tk.END, f"予想ファイル名: {cond2_file_path}\n\n")
                return
        
        # 連続条件を取得
        cond_consecutive = self.cond_consecutive.get()
        cond_consecutive_type = self.cond_consecutive_type.get()
        
        # 条件2を取得
        cond2_consecutive = self.cond2_consecutive.get()
        cond2_consecutive_type = self.cond2_consecutive_type.get()
        cond2_candle = self.cond2_candle.get()
        
        # 個別全ての抽出項目を記録する変数を初期化
        if not hasattr(self, 'current_extracted_items'):
            self.current_extracted_items = []
        else:
            self.current_extracted_items.clear()
        
        # 条件個別全ての処理
        if cond_individual_all:
            filter_type, values = cond_individual_all
            for value in values:
                self.result_text.insert(tk.END, f"\n--- 条件: {value} ---\n")
                
                # 抽出項目を記録
                self.current_extracted_items.append(value)
                
                temp_cond_month = value if filter_type == "月" else cond_month
                temp_cond_day = value if filter_type == "日" else cond_day
                temp_cond_lower = (cond_lower[0], value) if cond_lower and filter_type == cond_lower[0] else cond_lower
                temp_cond_candle = value if filter_type == "陽線・陰線" else cond_candle
                
                self.process_with_separate_conditions(target_df, cond_df, cond2_df,
                                                    target_month, target_day, target_lower,
                                                    temp_cond_month, temp_cond_day, temp_cond_lower, temp_cond_candle,
                                                    cond_consecutive, cond_consecutive_type,
                                                    cond2_consecutive, cond2_consecutive_type, cond2_month, cond2_day, 
                                                    cond2_lower, cond2_candle)
        else:
            # 通常処理
            self.process_with_separate_conditions(target_df, cond_df, cond2_df,
                                                target_month, target_day, target_lower,
                                                cond_month, cond_day, cond_lower, cond_candle,
                                                cond_consecutive, cond_consecutive_type,
                                                cond2_consecutive, cond2_consecutive_type, cond2_month, cond2_day, 
                                                cond2_lower, cond2_candle)
        
    def process_with_separate_conditions(self, target_df, cond_df, cond2_df,
                                     target_month, target_day, target_lower,
                                     cond_month, cond_day, cond_lower, cond_candle,
                                     cond_consecutive, cond_consecutive_type,
                                     cond2_consecutive, cond2_consecutive_type, cond2_month, cond2_day,
                                     cond2_lower, cond2_candle):
        """条件と対象を別々のデータファイルから処理"""
        
        # ★★★ 条件2の処理 ★★★
        filtered_cond2_dates = None
        if cond2_df is not None:
            # 条件2の連続条件を適用
            if cond2_consecutive != "なし":
                consecutive_num = int(cond2_consecutive)
                is_bullish = (cond2_consecutive_type == "陽線")
                
                valid_indices = []
                for i in range(consecutive_num, len(cond2_df)):
                    past_candles = cond2_df.iloc[i-consecutive_num:i]
                    if is_bullish:
                        if all(past_candles['Close'] > past_candles['Open']):
                            valid_indices.append(i)
                    else:
                        if all(past_candles['Close'] < past_candles['Open']):
                            valid_indices.append(i)
                
                if not valid_indices:
                    self.result_text.insert(tk.END, f"条件2の連続条件（過去{consecutive_num}本{cond2_consecutive_type}）に合致するデータがありません。\n\n")
                    return
                
                cond2_df = cond2_df.iloc[valid_indices].reset_index(drop=True)
                self.result_text.insert(tk.END, f"条件2の連続条件に合致: {len(cond2_df)}行\n")
            
            # 条件2のフィルタを適用
            condition2_filtered = self.filter_data(cond2_df, cond2_month, cond2_day, cond2_lower, cond2_candle)
            
            if condition2_filtered.empty:
                self.result_text.insert(tk.END, "条件2に合致するデータがありません。\n\n")
                return
            
            self.result_text.insert(tk.END, f"条件2に合致: {len(condition2_filtered)}行\n")
            
            # 条件2の日時情報を保存（次の足を探すため）
            filtered_cond2_dates = self.extract_datetime_info(condition2_filtered)
        
        # ★★★ 条件1の処理 ★★★
        filtered_cond_dates = None
        if cond_df is not None:
            # 条件2がある場合、条件2の次の足に該当する条件1のデータを探す
            if filtered_cond2_dates is not None:
                cond_df = self.filter_by_next_candle(cond_df, filtered_cond2_dates)
                if cond_df.empty:
                    self.result_text.insert(tk.END, "条件2の次の足（条件1対象）が見つかりません。\n\n")
                    return
                self.result_text.insert(tk.END, f"条件2の次の足: {len(cond_df)}行\n")
            
            # 条件1の連続条件を適用
            if cond_consecutive != "なし":
                consecutive_num = int(cond_consecutive)
                is_bullish = (cond_consecutive_type == "陽線")
                
                valid_indices = []
                for i in range(consecutive_num, len(cond_df)):
                    past_candles = cond_df.iloc[i-consecutive_num:i]
                    if is_bullish:
                        if all(past_candles['Close'] > past_candles['Open']):
                            valid_indices.append(i)
                    else:
                        if all(past_candles['Close'] < past_candles['Open']):
                            valid_indices.append(i)
                
                if not valid_indices:
                    self.result_text.insert(tk.END, f"条件1の連続条件（過去{consecutive_num}本{cond_consecutive_type}）に合致するデータがありません。\n\n")
                    return
                
                cond_df = cond_df.iloc[valid_indices].reset_index(drop=True)
                self.result_text.insert(tk.END, f"条件1の連続条件に合致: {len(cond_df)}行\n")
            
            # 条件1のフィルタを適用
            condition_filtered = self.filter_data(cond_df, cond_month, cond_day, cond_lower, cond_candle)
            
            if condition_filtered.empty:
                self.result_text.insert(tk.END, "条件1に合致するデータがありません。\n\n")
                return
            
            self.result_text.insert(tk.END, f"条件1に合致: {len(condition_filtered)}行\n")
            
            # 条件1の日時情報を保存（次の足を探すため）
            filtered_cond_dates = self.extract_datetime_info(condition_filtered)
        
        # ★★★ 対象の処理 ★★★
        # 条件1がある場合、条件1の次の足に該当する対象のデータを探す
        if filtered_cond_dates is not None:
            result_df = self.filter_by_next_candle(target_df, filtered_cond_dates)
            if result_df.empty:
                self.result_text.insert(tk.END, "条件1の次の足（対象）が見つかりません。\n\n")
                return
            self.result_text.insert(tk.END, f"条件1の次の足: {len(result_df)}行\n")
        elif filtered_cond2_dates is not None:
            # 条件1がなく条件2だけある場合
            result_df = self.filter_by_next_candle(target_df, filtered_cond2_dates)
            if result_df.empty:
                self.result_text.insert(tk.END, "条件2の次の足（対象）が見つかりません。\n\n")
                return
            self.result_text.insert(tk.END, f"条件2の次の足: {len(result_df)}行\n")
        else:
            # 条件がない場合は対象データをそのまま使用
            result_df = target_df
        
        # 対象フィルタを適用
        result_df = self.filter_data(result_df, target_month, target_day, target_lower, "なし")
        
        if result_df.empty:
            self.result_text.insert(tk.END, "フィルタ後の対象データが見つかりません。\n\n")
            return
        
        self.result_text.insert(tk.END, f"最終対象データ: {len(result_df)}行\n")
        self.result_text.insert(tk.END, "-" * 50 + "\n")
        
        # 抽出内容に応じて分析
        extract_type = self.extract_type.get()
        
        if extract_type == "陽線確率":
            self.analyze_bullish_probability(result_df)
        else:
            extract_detail = self.extract_detail.get()
            self.analyze_width(result_df, extract_detail)
        
        self.result_text.insert(tk.END, "\n")
    
    def extract_datetime_info(self, df):
        """DataFrameから日時情報を抽出"""
        datetime_info = []
        
        for _, row in df.iterrows():
            info = {}
            if 'Year' in df.columns:
                info['Year'] = row['Year']
            if 'Month' in df.columns:
                info['Month'] = row['Month']
            if 'Day' in df.columns:
                info['Day'] = row['Day']
            if 'TimeRange' in df.columns:
                info['TimeRange'] = row['TimeRange']
            if 'Session' in df.columns:
                info['Session'] = row['Session']
            
            datetime_info.append(info)
        
        return datetime_info

    def filter_by_next_candle(self, df, prev_datetime_info):
        """前の足の日時情報に基づいて次の足を抽出"""
        result_rows = []
        
        for prev_info in prev_datetime_info:
            # 同じ日付のデータを絞り込み
            filtered = df.copy()
            
            if 'Year' in prev_info and 'Year' in df.columns:
                filtered = filtered[filtered['Year'] == prev_info['Year']]
            if 'Month' in prev_info and 'Month' in df.columns:
                filtered = filtered[filtered['Month'] == prev_info['Month']]
            if 'Day' in prev_info and 'Day' in df.columns:
                filtered = filtered[filtered['Day'] == prev_info['Day']]
            
            # TimeRangeがある場合、前の足の終了時刻以降を探す
            if 'TimeRange' in prev_info and 'TimeRange' in df.columns:
                prev_end_time = prev_info['TimeRange'].split('-')[1]
                
                for _, row in filtered.iterrows():
                    curr_start_time = row['TimeRange'].split('-')[0]
                    
                    # 前の足の終了時刻以降の最初の足を取得
                    if curr_start_time >= prev_end_time:
                        result_rows.append(row)
                        break
            else:
                # TimeRangeがない場合は、フィルタ後の最初の行を取得
                if not filtered.empty:
                    result_rows.append(filtered.iloc[0])
        
        if result_rows:
            return pd.DataFrame(result_rows).reset_index(drop=True)
        else:
            return pd.DataFrame()

    def process_with_condition(self, df, target_month, target_day, target_lower,
                          cond_month, cond_day, cond_lower, cond_candle,
                          cond_consecutive, cond_consecutive_type,
                          cond2_consecutive, cond2_consecutive_type, cond2_month, cond2_day,
                          cond2_lower, cond2_candle):
        """条件適用後のデータ処理"""
        original_df = df.copy()
        
        # 条件2を最初に適用（既存のコードはそのまま）
        if (cond2_consecutive != "なし" or cond2_month != "なし" or cond2_day != "なし" or 
            cond2_lower or cond2_candle != "なし"):
            
            if cond2_consecutive != "なし":
                consecutive_num = int(cond2_consecutive)
                is_bullish = (cond2_consecutive_type == "陽線")
                
                valid_indices = []
                for i in range(consecutive_num, len(df)):
                    past_candles = df.iloc[i-consecutive_num:i]
                    if is_bullish:
                        if all(past_candles['Close'] > past_candles['Open']):
                            valid_indices.append(i)
                    else:
                        if all(past_candles['Close'] < past_candles['Open']):
                            valid_indices.append(i)
                
                if not valid_indices:
                    self.result_text.insert(tk.END, f"条件2の連続条件（過去{consecutive_num}本{cond2_consecutive_type}）に合致するデータがありません。\n\n")
                    return
                
                df = df.iloc[valid_indices].reset_index(drop=True)
                original_df = df.copy()
                self.result_text.insert(tk.END, f"条件2の連続条件に合致: {len(df)}行\n")
            
            condition2_df = self.filter_data(df, cond2_month, cond2_day, cond2_lower, cond2_candle)
            
            if condition2_df.empty:
                self.result_text.insert(tk.END, "条件2に合致するデータがありません。\n\n")
                return
            
            self.result_text.insert(tk.END, f"条件2に合致: {len(condition2_df)}行\n")
            
            condition2_indices = condition2_df.index.tolist()
            next_indices = [i + 1 for i in condition2_indices if i + 1 < len(original_df)]
            
            if not next_indices:
                self.result_text.insert(tk.END, "条件2後のデータがありません。\n\n")
                return
            
            df = original_df.iloc[next_indices].reset_index(drop=True)
            original_df = df.copy()
            self.result_text.insert(tk.END, f"条件2後のデータ: {len(df)}行\n")
        
        # 条件1の連続条件を適用
        if cond_consecutive != "なし":
            consecutive_num = int(cond_consecutive)
            is_bullish = (cond_consecutive_type == "陽線")
            
            valid_indices = []
            for i in range(consecutive_num, len(df)):
                past_candles = df.iloc[i-consecutive_num:i]
                if is_bullish:
                    if all(past_candles['Close'] > past_candles['Open']):
                        valid_indices.append(i)
                else:
                    if all(past_candles['Close'] < past_candles['Open']):
                        valid_indices.append(i)
            
            if not valid_indices:
                self.result_text.insert(tk.END, f"条件1の連続条件（過去{consecutive_num}本{cond_consecutive_type}）に合致するデータがありません。\n\n")
                return
            
            df = df.iloc[valid_indices].reset_index(drop=True)
            original_df = df.copy()
            self.result_text.insert(tk.END, f"条件1の連続条件に合致: {len(df)}行\n")
        
        # ★★★ 条件1のフィルタを適用（時間粒度の違いに対応） ★★★
        if cond_month != "なし" or cond_day != "なし" or cond_lower or cond_candle != "なし":
            
            # 条件と対象の時間粒度が異なる場合の処理
            target_time = target_lower[0] if target_lower else None
            cond_time = cond_lower[0] if cond_lower else None
            
            # 時間粒度の階層を定義
            time_hierarchy = {
                "M1": 1, "M5": 5, "M15": 15, "M30": 30, 
                "H1": 60, "H4": 240, "セッション": 360
            }
            
            # 条件の時間粒度が対象より粗い場合（例: 条件H1、対象M30）
            if (target_time and cond_time and 
                time_hierarchy.get(cond_time, 0) > time_hierarchy.get(target_time, 0)):
                
                # 条件の時間範囲内にある対象の足を抽出
                condition_df = self.filter_data(df, cond_month, cond_day, cond_lower, cond_candle)
                
                if condition_df.empty:
                    self.result_text.insert(tk.END, "条件1に合致するデータがありません。\n\n")
                    return
                
                self.result_text.insert(tk.END, f"条件1に合致: {len(condition_df)}行\n")
                
                # ★★★ 条件の時間範囲から対象の時間範囲を特定 ★★★
                if 'TimeRange' in condition_df.columns and 'TimeRange' in original_df.columns:
                    target_rows = []
                    
                    for _, cond_row in condition_df.iterrows():
                        # 条件の時間範囲を取得（例: "00:00-01:00"）
                        cond_time_range = cond_row['TimeRange']
                        cond_start = cond_time_range.split('-')[0]
                        cond_end = cond_time_range.split('-')[1]
                        
                        # 同じ日付で条件の時間範囲以降の対象時間を探す
                        same_date_df = original_df.copy()
                        
                        # Year, Month, Dayが一致するものを絞り込み
                        if 'Year' in condition_df.columns:
                            same_date_df = same_date_df[same_date_df['Year'] == cond_row['Year']]
                        if 'Month' in condition_df.columns:
                            same_date_df = same_date_df[same_date_df['Month'] == cond_row['Month']]
                        if 'Day' in condition_df.columns:
                            same_date_df = same_date_df[same_date_df['Day'] == cond_row['Day']]
                        
                        # 対象の時間範囲が条件の終了時刻以降のものを取得
                        for _, target_row in same_date_df.iterrows():
                            target_time_range = target_row['TimeRange']
                            target_start = target_time_range.split('-')[0]
                            
                            # 条件の終了時刻以降かチェック
                            if target_start >= cond_end:
                                # 対象の時間範囲と一致するか確認
                                if target_lower and target_lower[1] != "個別全て":
                                    if target_time_range == target_lower[1]:
                                        target_rows.append(target_row)
                                        break  # 最初の一致で終了
                                else:
                                    # 対象が指定されていない場合は条件の次の足
                                    target_rows.append(target_row)
                                    break
                    
                    if target_rows:
                        df = pd.DataFrame(target_rows)
                        self.result_text.insert(tk.END, f"条件1に基づく対象データ: {len(df)}行\n")
                    else:
                        self.result_text.insert(tk.END, "条件1に対応する対象データがありません。\n\n")
                        return
                else:
                    # TimeRangeカラムがない場合は通常の次の足処理
                    condition_indices = condition_df.index.tolist()
                    target_indices = [i + 1 for i in condition_indices if i + 1 < len(original_df)]
                    
                    if not target_indices:
                        self.result_text.insert(tk.END, "条件後の対象データがありません。\n\n")
                        return
                    
                    df = original_df.iloc[target_indices]
                    self.result_text.insert(tk.END, f"条件後の対象: {len(df)}行\n")
            
            # 条件と対象が同じ粒度、または対象が粗い場合（既存の処理）
            else:
                condition_df = self.filter_data(df, cond_month, cond_day, cond_lower, cond_candle)
                
                if condition_df.empty:
                    self.result_text.insert(tk.END, "条件1に合致するデータがありません。\n\n")
                    return
                
                self.result_text.insert(tk.END, f"条件1に合致: {len(condition_df)}行\n")
                
                # 月足データの特別処理
                if 'Month' in original_df.columns and 'Year' in original_df.columns and 'Day' not in original_df.columns:
                    if cond_month != "なし" and cond_month != "全て" and target_month != "なし" and target_month != "全て":
                        cond_month_num = int(cond_month.replace("月", ""))
                        target_month_num = int(target_month.replace("月", ""))
                        
                        condition_years = condition_df[condition_df['Month'] == cond_month_num]['Year'].unique()
                        
                        target_rows = []
                        for year in condition_years:
                            if target_month_num > cond_month_num:
                                target_row = original_df[(original_df['Year'] == year) & 
                                                        (original_df['Month'] == target_month_num)]
                            else:
                                target_row = original_df[(original_df['Year'] == year + 1) & 
                                                        (original_df['Month'] == target_month_num)]
                            
                            if not target_row.empty:
                                target_rows.append(target_row)
                        
                        if target_rows:
                            df = pd.concat(target_rows, ignore_index=True)
                            self.result_text.insert(tk.END, f"条件月に基づく対象月データ: {len(df)}行\n")
                        else:
                            self.result_text.insert(tk.END, "条件に対応する対象月のデータがありません。\n\n")
                            return
                    else:
                        condition_indices = condition_df.index.tolist()
                        target_indices = [i + 1 for i in condition_indices if i + 1 < len(original_df)]
                        
                        if not target_indices:
                            self.result_text.insert(tk.END, "条件後の対象データがありません。\n\n")
                            return
                        
                        df = original_df.iloc[target_indices]
                        self.result_text.insert(tk.END, f"条件後の対象: {len(df)}行\n")
                
                # 日足データの特別処理
                elif 'Day' in original_df.columns and 'Month' in original_df.columns and 'Year' in original_df.columns:
                    if (cond_month != "なし" and cond_month != "全て" and 
                        cond_day != "なし" and cond_day != "全て" and
                        target_month != "なし" and target_month != "全て" and
                        target_day != "なし" and target_day != "全て"):
                        
                        cond_month_num = int(cond_month.replace("月", ""))
                        cond_day_num = int(cond_day.replace("日", ""))
                        target_month_num = int(target_month.replace("月", ""))
                        target_day_num = int(target_day.replace("日", ""))
                        
                        condition_dates = condition_df[['Year', 'Month', 'Day']].values
                        
                        target_rows = []
                        for year, month, day in condition_dates:
                            target_year = year
                            target_month_calc = target_month_num
                            
                            if target_month_num < cond_month_num:
                                target_year += 1
                            elif target_month_num == cond_month_num:
                                if target_day_num < cond_day_num:
                                    target_year += 1
                            
                            target_row = original_df[
                                (original_df['Year'] == target_year) & 
                                (original_df['Month'] == target_month_calc) &
                                (original_df['Day'] == target_day_num)
                            ]
                            
                            if not target_row.empty:
                                target_rows.append(target_row)
                        
                        if target_rows:
                            df = pd.concat(target_rows, ignore_index=True)
                            self.result_text.insert(tk.END, f"条件に基づく対象データ: {len(df)}行\n")
                        else:
                            self.result_text.insert(tk.END, "条件に対応する対象のデータがありません。\n\n")
                            return
                    
                    elif (cond_month == "なし" and cond_day != "なし" and cond_day != "全て" and
                        target_month == "なし" and target_day != "なし" and target_day != "全て"):
                        
                        cond_day_num = int(cond_day.replace("日", ""))
                        target_day_num = int(target_day.replace("日", ""))
                        
                        condition_dates = condition_df[['Year', 'Month', 'Day']].values
                        
                        target_rows = []
                        for year, month, day in condition_dates:
                            target_year = year
                            target_month_num = month
                            
                            if target_day_num < cond_day_num:
                                target_month_num += 1
                                if target_month_num > 12:
                                    target_month_num = 1
                                    target_year += 1
                            
                            target_row = original_df[
                                (original_df['Year'] == target_year) & 
                                (original_df['Month'] == target_month_num) &
                                (original_df['Day'] == target_day_num)
                            ]
                            
                            if not target_row.empty:
                                target_rows.append(target_row)
                        
                        if target_rows:
                            df = pd.concat(target_rows, ignore_index=True)
                            self.result_text.insert(tk.END, f"条件日に基づく対象日データ: {len(df)}行\n")
                        else:
                            self.result_text.insert(tk.END, "条件に対応する対象日のデータがありません。\n\n")
                            return
                    
                    else:
                        condition_indices = condition_df.index.tolist()
                        target_indices = [i + 1 for i in condition_indices if i + 1 < len(original_df)]
                        
                        if not target_indices:
                            self.result_text.insert(tk.END, "条件後の対象データがありません。\n\n")
                            return
                        
                        df = original_df.iloc[target_indices]
                        self.result_text.insert(tk.END, f"条件後の対象: {len(df)}行\n")
                
                else:
                    condition_indices = condition_df.index.tolist()
                    target_indices = [i + 1 for i in condition_indices if i + 1 < len(original_df)]
                    
                    if not target_indices:
                        self.result_text.insert(tk.END, "条件後の対象データがありません。\n\n")
                        return
                    
                    df = original_df.iloc[target_indices]
                    self.result_text.insert(tk.END, f"条件後の対象: {len(df)}行\n")
        
        # 対象フィルタを適用
        df = self.filter_data(df, target_month, target_day, target_lower, "なし")
        
        if df.empty:
            self.result_text.insert(tk.END, "フィルタ後の対象データが見つかりません。\n\n")
            return
        
        self.result_text.insert(tk.END, f"最終対象データ: {len(df)}行\n")
        self.result_text.insert(tk.END, "-" * 50 + "\n")
        
        # 抽出内容に応じて分析
        extract_type = self.extract_type.get()
        
        if extract_type == "陽線確率":
            self.analyze_bullish_probability(df)
        else:
            extract_detail = self.extract_detail.get()
            self.analyze_width(df, extract_detail)
        
        self.result_text.insert(tk.END, "\n")

    def analyze_bullish_probability(self, df):
        """陽線確率を分析"""
        total = len(df)
        bullish = len(df[df["Close"] > df["Open"]])
        probability = (bullish / total * 100) if total > 0 else 0

        result = f"【陽線確率分析】\n"
        result += f"総ローソク足数: {total}本\n"
        result += f"陽線の数: {bullish}本\n"
        result += f"陰線の数: {total - bullish}本\n"
        result += f"陽線確率: {probability:.2f}%\n"

        self.result_text.insert(tk.END, result)

        # 結果を保存
        self.analysis_results.append(
            {
                "総ローソク足数": total,
                "陽線の数": bullish,
                "陰線の数": total - bullish,
                "陽線確率(%)": round(probability, 2),
            }
        )

    def analyze_width(self, df, detail):
        """幅の出現頻度を分析"""
        if detail == "実体":
            widths = df['Close'] - df['Open']  # ★マイナスを保持
        elif detail == "上幅":
            widths = df['High'] - df[['Open', 'Close']].max(axis=1)
        elif detail == "下幅":
            widths = df[['Open', 'Close']].min(axis=1) - df['Low']
        elif detail == "上髭":
            widths = df['High'] - df[['Open', 'Close']].max(axis=1)
        elif detail == "下髭":
            widths = df[['Open', 'Close']].min(axis=1) - df['Low']
        else:
            widths = df['Close'] - df['Open']  # ★マイナスを保持
        
        # 幅を小数点5桁で丸める
        widths = widths.round(5)
        
        # 出現頻度をカウント
        counter = Counter(widths)
        total = len(widths)
        
        # ★プラスとマイナスの集計
        positive_count = len(widths[widths > 0])
        negative_count = len(widths[widths < 0])
        zero_count = len(widths[widths == 0])
        
        result = f"【幅の出現頻度分析】\n"
        result += f"分析対象: {detail}\n"
        result += f"総データ数: {total}\n"
        result += f"プラス幅: {positive_count}件 ({positive_count/total*100:.2f}%)\n"
        result += f"マイナス幅: {negative_count}件 ({negative_count/total*100:.2f}%)\n"
        result += f"ゼロ幅: {zero_count}件 ({zero_count/total*100:.2f}%)\n"
        result += f"最小幅: {widths.min():.5f}\n"
        result += f"最大幅: {widths.max():.5f}\n"
        result += f"平均幅: {widths.mean():.5f}\n"
        result += f"\n--- 出現頻度 (上位30件) ---\n"
        result += f"{'幅':<12} {'回数':<8} {'確率'}\n"
        result += "-" * 40 + "\n"
        
        # ★マイナスの値も含めて頻度順にソート
        for width, count in sorted(counter.items(), key=lambda x: x[1], reverse=True)[:30]:
            probability = count / total * 100
            result += f"{width:<12.5f} {count:<8} {probability:>6.2f}%\n"
            
            # 結果を保存
            self.analysis_results.append({
                '幅': round(width, 5),
                '回数': count,
                '確率(%)': round(probability, 2)
            })
        
        self.result_text.insert(tk.END, result)

    def save_to_csv(self):
        """分析結果をCSVに保存"""
        if not self.analysis_results:
            messagebox.showwarning("警告", "保存する分析結果がありません。先にデータ分析を実行してください。")
            return
        
        # 保存先ディレクトリ
        save_dir = "C:/Users/81803/OneDrive/ドキュメント/TyuusyutuKekka_Chart"
        
        # ディレクトリが存在しない場合は作成
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                messagebox.showerror("エラー", f"ディレクトリの作成に失敗しました: {e}")
                return
        
        # ファイル名を生成
        info = self.current_analysis_info
        
        # 対象部分（プルダウン名:値の形式）
        target_parts = []
        if info['target_month'] != "なし":
            target_parts.append(f"月:{info['target_month']}")
        if info['target_day'] != "なし":
            target_parts.append(f"日:{info['target_day']}")
        if info['target_lower']:
            time_type, time_value = info['target_lower']
            target_parts.append(f"{time_type}:{time_value}")
        target_str = "_".join(target_parts) if target_parts else "対象なし"
        
        # 条件2部分（プルダウン名:値の形式）
        cond2_parts = []
        if info.get('cond2_consecutive', 'なし') != "なし":
            cond2_parts.append(f"連続条件:{info['cond2_consecutive']}本{info.get('cond2_consecutive_type', '陽線')}")
        if info.get('cond2_month', 'なし') != "なし":
            cond2_parts.append(f"月:{info['cond2_month']}")
        if info.get('cond2_day', 'なし') != "なし":
            cond2_parts.append(f"日:{info['cond2_day']}")
        if info.get('cond2_lower'):
            time_type, time_value = info['cond2_lower']
            cond2_parts.append(f"{time_type}:{time_value}")
        if info.get('cond2_candle', 'なし') != "なし":
            cond2_parts.append(f"陽線陰線:{info['cond2_candle']}")
        
        # 条件1部分（プルダウン名:値の形式）
        cond_parts = []
        if info.get('cond_consecutive', 'なし') != "なし":
            cond_parts.append(f"連続条件:{info['cond_consecutive']}本{info.get('cond_consecutive_type', '陽線')}")
        if info['cond_month'] != "なし":
            cond_parts.append(f"月:{info['cond_month']}")
        if info['cond_day'] != "なし":
            cond_parts.append(f"日:{info['cond_day']}")
        if info['cond_lower']:
            time_type, time_value = info['cond_lower']
            cond_parts.append(f"{time_type}:{time_value}")
        if info['cond_candle'] != "なし":
            cond_parts.append(f"陽線陰線:{info['cond_candle']}")
        
        # 条件2と条件1を結合
        all_cond_parts = []
        if cond2_parts:
            all_cond_parts.append("条件2[" + "_".join(cond2_parts) + "]")
        if cond_parts:
            all_cond_parts.append("条件1[" + "_".join(cond_parts) + "]")
        
        cond_str = "_".join(all_cond_parts) if all_cond_parts else "条件なし"
        
        # 抽出内容部分
        if info['extract_type'] == "陽線確率":
            extract_str = "陽線確率"
        else:
            extract_str = f"幅_{info['extract_detail']}"
        
        # ファイル名に使えない文字を置換
        target_str = target_str.replace(":", "-").replace("/", "-").replace("\\", "-")
        cond_str = cond_str.replace(":", "-").replace("/", "-").replace("\\", "-").replace("[", "(").replace("]", ")")
        
        filename = f"{target_str}_{cond_str}_{extract_str}.csv"
        filepath = os.path.join(save_dir, filename)
        
        try:
            # 個別全ての場合、抽出した時間情報を追加
            df_results = pd.DataFrame(self.analysis_results)
            
            # 個別全てで抽出された項目を特定
            extracted_item = None
            extracted_type = None
            
            # 対象で個別全てが使われているか確認
            if info['target_month'] == "個別全て":
                extracted_type = "対象月"
            elif info['target_day'] == "個別全て":
                extracted_type = "対象日"
            elif info['target_lower'] and info['target_lower'][1] == "個別全て":
                extracted_type = f"対象{info['target_lower'][0]}"
            
            # 条件1で個別全てが使われているか確認
            elif info['cond_month'] == "個別全て":
                extracted_type = "条件1_月"
            elif info['cond_day'] == "個別全て":
                extracted_type = "条件1_日"
            elif info['cond_lower'] and info['cond_lower'][1] == "個別全て":
                extracted_type = f"条件1_{info['cond_lower'][0]}"
            elif info['cond_candle'] == "個別全て":
                extracted_type = "条件1_陽線陰線"
            
            # 条件2で個別全てが使われているか確認
            elif info.get('cond2_month') == "個別全て":
                extracted_type = "条件2_月"
            elif info.get('cond2_day') == "個別全て":
                extracted_type = "条件2_日"
            elif info.get('cond2_lower') and info['cond2_lower'][1] == "個別全て":
                extracted_type = f"条件2_{info['cond2_lower'][0]}"
            elif info.get('cond2_candle') == "個別全て":
                extracted_type = "条件2_陽線陰線"
            
            # 個別全ての場合、抽出項目列を先頭に追加
            if extracted_type and hasattr(self, 'current_extracted_items') and self.current_extracted_items:
                # 各結果に対応する抽出項目を追加
                if len(self.current_extracted_items) == len(df_results):
                    df_results.insert(0, extracted_type, self.current_extracted_items)
                else:
                    # 結果行数と抽出項目数が一致しない場合の処理
                    # 各結果グループごとに抽出項目を割り当て
                    extracted_items_expanded = []
                    result_idx = 0
                    for item in self.current_extracted_items:
                        # 各項目の結果数を推定（陽線確率なら1行、幅なら複数行）
                        if info['extract_type'] == "陽線確率":
                            extracted_items_expanded.append(item)
                            result_idx += 1
                        else:
                            # 幅の場合、次の項目まで or 最後まで同じ値を使用
                            next_idx = result_idx
                            # 次の結果グループの開始位置を探す
                            while next_idx < len(df_results):
                                extracted_items_expanded.append(item)
                                next_idx += 1
                                # 適切な区切りで判断（実装依存）
                                if next_idx < len(df_results):
                                    # ここでは最大30件（上位表示件数）を目安に区切る
                                    if (next_idx - result_idx) >= 30:
                                        break
                            result_idx = next_idx
                    
                    # リストの長さを結果数に合わせる
                    if len(extracted_items_expanded) >= len(df_results):
                        extracted_items_expanded = extracted_items_expanded[:len(df_results)]
                    else:
                        # 不足分を最後の値で埋める
                        if extracted_items_expanded:
                            extracted_items_expanded.extend([extracted_items_expanded[-1]] * (len(df_results) - len(extracted_items_expanded)))
                    
                    if extracted_items_expanded:
                        df_results.insert(0, extracted_type, extracted_items_expanded)
            
            df_results.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("保存完了", f"分析結果を保存しました:\n{filepath}")
        except Exception as e:
            messagebox.showerror("エラー", f"CSV保存中にエラーが発生しました: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChartAnalyzerUI(root)
    root.mainloop()
