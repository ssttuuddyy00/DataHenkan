import pandas as pd
from pathlib import Path

TARGET_DIR = Path("C:/Users/81803/OneDrive/ドキュメント/ChartKei/ChartData/FX/ChartData/KakouData")

for input_path in TARGET_DIR.glob("*.csv"):
    output_path = input_path.with_name(
        input_path.stem + "_UTC+9" + input_path.suffix
    )

    df = pd.read_csv(input_path)

    dt = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Timestamp"],
        format="%Y%m%d %H:%M:%S"
    ) + pd.Timedelta(hours=9)

    df["Date"] = dt.dt.strftime("%Y%m%d")
    df["Timestamp"] = dt.dt.strftime("%H:%M:%S"

    )

    df.to_csv(output_path, index=False)

    print(f"作成完了: {output_path.name}")

print("全ファイル処理完了")
