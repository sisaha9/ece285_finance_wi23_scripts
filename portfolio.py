import numpy as np
import pandas as pd
import requests
import yaml
import time
from pathlib import Path
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import os

metadata_fp = "portfolio.yaml"

STOCK_TICKER_LENGTH = 3
SLEEP_TIME = 60 + 10
STOCK_PRICE_PURCHASE_INDICATOR = "low"
STOCK_PRICE_VALUATION_INDICATOR = "high"
OPTION_PRICE_PURCHASE_INDICATOR = "low"
OPTION_PRICE_VALUATION_INDICATOR = "high"
RESULTS_DIR = "results"
ROUND_TO = 2
MIN_HEIGHT = 0
XROT = 45
FIGSIZE=(20,20)

API_KEY = os.environ['API_KEY']

@dataclass
class HoldingItem:
    ticker: str
    quantity: int
    purchase_price: float
    current_price: float
    total_price: float = 0.0
    profit: float = 0.0

    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}

get_open_close_price_url = "https://api.polygon.io/v1/open-close/{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"
get_option_price_url = "https://api.polygon.io/v1/open-close/O:{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"

with open(metadata_fp) as metadata_f:
    metadata_dict = yaml.safe_load(metadata_f)

def is_purchase_stock(ticker):
    return len(ticker) == STOCK_TICKER_LENGTH

def generate_url_request(url, ticker, year, month, day):
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", API_KEY))
    if not response.ok:
        for i in range(SLEEP_TIME):
            print(f"Sleeping for {SLEEP_TIME - i}")
            time.sleep(1)
    else:
        return response.json()
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", API_KEY))
    if not response.ok:
        print("Something went wrong", url, ticker, year, month, day)
        exit()
    else:
        return response.json()
    
def get_price(ticker, year, month, day, indicator):
    if is_purchase_stock(ticker):
        response = generate_url_request(get_open_close_price_url, ticker, year, month, day)
        return float(response[indicator])
    else:
        response = generate_url_request(get_option_price_url, ticker, year, month, day)
        return float(response[indicator])

def main():
    valuations = {
        "Labels": []
    }
    trade_history = pd.read_csv(metadata_dict["DATA"]["TRADE_HISTORY"])
    trade_history["Date Bought"] = pd.to_datetime(trade_history["Date Bought"])
    identifiers = ['BANK'] + trade_history['Ticker'].values.tolist()
    for identifier in identifiers:
        valuations[identifier] = []
    if RESULTS_DIR:
        Path(RESULTS_DIR).mkdir(exist_ok=False)
    for portfolio_idx, portfolio_valuation_date in enumerate(metadata_dict["PORTFOLIO_VALUATION"]["DATES"]):
        holdings = {
            "BANK": HoldingItem("BANK", 1, metadata_dict["BANK"]["INITIAL_MONEY"], metadata_dict["BANK"]["INITIAL_MONEY"]),
        }
        portfolio_valuation_datetime = pd.to_datetime(portfolio_valuation_date)
        valuation_year = '{:04}'.format(portfolio_valuation_datetime.year)
        valuation_month = '{:02}'.format(portfolio_valuation_datetime.month)
        valuation_day = '{:02}'.format(portfolio_valuation_datetime.day)
        relevant_trade_history = trade_history[trade_history["Date Bought"] <= portfolio_valuation_datetime].copy()
        for _, row in relevant_trade_history.iterrows():
            ticker = row["Ticker"]
            purchase_year = '{:04}'.format(row["Date Bought"].year)
            purchase_month = '{:02}'.format(row["Date Bought"].month)
            purchase_day = '{:02}'.format(row["Date Bought"].day)
            if is_purchase_stock(ticker):
                purchase_price = get_price(ticker, purchase_year, purchase_month, purchase_day, STOCK_PRICE_PURCHASE_INDICATOR)
                current_price = get_price(ticker, valuation_year, valuation_month, valuation_day, STOCK_PRICE_VALUATION_INDICATOR)
            else:
                if OPTION_PRICE_PURCHASE_INDICATOR == "listed":
                    purchase_price = float(row["Purchase Price"])
                else:
                    purchase_price = get_price(ticker, purchase_year, purchase_month, purchase_day, OPTION_PRICE_PURCHASE_INDICATOR)
                current_price = get_price(ticker, valuation_year, valuation_month, valuation_day, OPTION_PRICE_VALUATION_INDICATOR)
            total_price = purchase_price * row["Shares Bought"]
            holdings['BANK'].current_price -= total_price
            holdings[ticker] = HoldingItem(ticker, int(row["Shares Bought"]), purchase_price, current_price)
        holdings_processed = []
        new_holding_infos = {}
        for holding_name, holding_info in holdings.items():
            holding_info.total_price = holding_info.current_price * holding_info.quantity
            holding_info.profit = (holding_info.current_price - holding_info.purchase_price) * holding_info.quantity
            holdings_processed.append(holding_info.dict())
            new_holding_infos[holding_name] = holding_info.dict()
        df = pd.DataFrame(holdings_processed)
        df["total_price"] = df["total_price"].astype(float)
        total_portfolio_value = df["total_price"].sum()
        print(df)
        print(total_portfolio_value)
        label_name = metadata_dict["PORTFOLIO_VALUATION"]["LABELS"][portfolio_idx]
        valuations["Labels"].append(f"{label_name}-{int(total_portfolio_value)}")
        for identifier in identifiers:
            if identifier in new_holding_infos:
                valuations[identifier].append(new_holding_infos[identifier]["total_price"])
            else:
                valuations[identifier].append(0.0)
        if RESULTS_DIR:
            df.to_csv(Path(RESULTS_DIR) / f"valuation_{valuation_year}_{valuation_month}_{valuation_day}.csv", index=None)
            with open(Path(RESULTS_DIR) / f"valuation_{valuation_year}_{valuation_month}_{valuation_day}.txt", "w") as fp:
                fp.write(str(total_portfolio_value))
            print(f"Valuation at {valuation_year}/{valuation_month}/{valuation_day} saved")
    df = pd.DataFrame(valuations)
    for identifier in identifiers:
        df[identifier] = df[identifier].astype(float)
    fig = df.set_index('Labels').plot(kind='bar', stacked=True, xlabel="Time", ylabel="Portfolio value in USD", title="Valuations of Portfolio", rot=XROT, figsize=FIGSIZE)
    for c in fig.containers:
        labels = [np.round(v.get_height(), ROUND_TO) if v.get_height() > MIN_HEIGHT else '' for v in c]
        fig.bar_label(c, labels=labels, label_type='center')
    if RESULTS_DIR:
        plt.savefig(Path(RESULTS_DIR) / "valuations.png")
        print("Plot generated")
    plt.show()

if __name__ == "__main__":
    main()