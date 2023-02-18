import shutil
import pandas as pd
from settings import RESULTS_DIR, ROUND_TO, BANK_INITIAL_MONEY
from pathlib import Path


def make_zip_file(file_name=Path(RESULTS_DIR).name):
    shutil.make_archive(file_name, "zip", RESULTS_DIR)


def save_evaluation(df: pd.DataFrame, evaluation_date: pd.Timestamp):
    file_name = f"valuation_{evaluation_date.month}-{evaluation_date.day}-{evaluation_date.year}"
    total_portfolio_value = df["Total"].sum()
    total_profit = total_portfolio_value - BANK_INITIAL_MONEY
    df.round(ROUND_TO).to_csv(
        Path(RESULTS_DIR) / f"{file_name}.csv", index=False, float_format=f"%.{ROUND_TO}f"
    )
    save_text = f"The total porfolio value is {round(total_portfolio_value, ROUND_TO)}\nThe total profit is {round(total_profit, ROUND_TO)}"
    with open(Path(RESULTS_DIR) / f"{file_name}.txt", "w") as fp:
        fp.write(save_text)
