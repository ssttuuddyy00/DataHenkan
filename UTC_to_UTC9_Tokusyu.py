import pandas as pd
import re
from pathlib import Path

TARGET_DIR = Path("C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData")


for input_path in TARGET_DIR.glob("*.csv"):
    df = pd.read_csv(input_path)
    cols = df.columns.tolist()

    suffix = "_NOCHANGE"
    dt = None

    # ===== Minute / Hour Range 検出 =====
    range_col = None
    unit = None
    span = None

    for c in cols:
        m = re.match(r"(Minute|Hour)(\d+)Range", c)
        if m:
            unit = m.group(1)      # Minute / Hour
            span = int(m.group(2))
            range_col = c
            break

    # ===== 1. Minute 列あり =====
    if {"Year","Month","Day","Hour","Minute"}.issubset(cols):
        dt = pd.to_datetime(df[["Year","Month","Day","Hour","Minute"]])

    # ===== 2. Hour 列あり（H1など） =====
    elif {"Year","Month","Day","Hour"}.issubset(cols):
        dt = pd.to_datetime(df[["Year","Month","Day","Hour"]])

    # ===== 3. Range から時刻復元（H4など） =====
    elif {"Year","Month","Day"}.issubset(cols) and range_col:
        # "02:00-06:00" → 02:00
        start_time = df[range_col].str.split("-").str[0]
        dt = pd.to_datetime(
            df["Year"].astype(str) + "-" +
            df["Month"].astype(str) + "-" +
            df["Day"].astype(str) + " " +
            start_time
        )

    # ===== 4. Session 足（明示的にスキップ） =====
    elif "SessionOverlap" in cols:
        print(f"セッション足スキップ: {input_path.name}")

    # ===== 変換実行 =====
    if dt is not None:
        dt = dt + pd.Timedelta(hours=9)

        df["Year"]  = dt.dt.year
        df["Month"] = dt.dt.month
        df["Day"]   = dt.dt.day

        if "Hour" in cols:
            df["Hour"] = dt.dt.hour
        if "Minute" in cols:
            df["Minute"] = dt.dt.minute

        # ---- Range 再生成 ----
        if range_col and unit:
            if unit == "Minute":
                end = dt + pd.to_timedelta(span, unit="m")
                df[range_col] = (
                    dt.dt.strftime("%H:%M") + "-" +
                    end.dt.strftime("%H:%M")
                )
            elif unit == "Hour":
                end = dt + pd.to_timedelta(span, unit="h")
                df[range_col] = (
                    dt.dt.strftime("%H:00") + "-" +
                    end.dt.strftime("%H:00")
                )

        suffix = "_UTC+9"
        print(f"変換: {input_path.name}")

    output_path = input_path.with_name(
        input_path.stem + suffix + input_path.suffix
    )
    df.to_csv(output_path, index=False)
