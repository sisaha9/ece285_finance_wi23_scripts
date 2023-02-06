import shutil
import pandas as pd
from settings import RESULTS_DIR, ROUND_TO
from pathlib import Path


def make_zip_file(file_name=Path(RESULTS_DIR).name):
    shutil.make_archive(file_name, "zip", RESULTS_DIR)


def save_evaluation(df: pd.DataFrame, evaluation_date: pd.Timestamp):
    file_name = f"valuation_{evaluation_date.month}-{evaluation_date.day}-{evaluation_date.year}"
    total_portfolio_value = df["Total"].sum()
    df.round(ROUND_TO).to_csv(Path(RESULTS_DIR) / f"{file_name}.csv", index=False, float_format=f'%.{ROUND_TO}f')
    with open(Path(RESULTS_DIR) / f"{file_name}.txt", "w") as fp:
        fp.write(str(round(total_portfolio_value, ROUND_TO)))
