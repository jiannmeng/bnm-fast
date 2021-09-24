import pandas as pd
from src.common import OUTPUT_FOLDER
import datetime

df = pd.read_csv(OUTPUT_FOLDER / "consolidated_iytm.csv")

df.date = pd.to_datetime(df.date, format="%Y%m%d")
df = df.astype({"ytm": float})
print(df)
