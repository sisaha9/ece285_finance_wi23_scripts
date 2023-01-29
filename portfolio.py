import pandas as pd
import yaml

metadata_fp = "portfolio.yaml"

with open(metadata_fp) as metadata_f:
    metadata_dict = yaml.safe_load(metadata_f)

stock_prices = pd.read_csv(metadata_dict["DATA"]["GLD_PRICES"])
log_book = pd.read_csv(metadata_dict["DATA"]["LOGBOOK"])
for idx, row in log_book.iterrows():
    print(row["Purchase Price"], type(row["Strike Price"]))