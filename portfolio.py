import pandas as pd
import requests
import yaml
import time
from pathlib import Path
from dataclasses import dataclass

metadata_fp = "portfolio.yaml"

STOCK_TICKER_LENGTH = 3
SLEEP_TIME = 60 + 10
STOCK_PRICE_INDICATOR = "open"
OPTION_PRICE_INDICATOR = "open"
RESULTS_DIR = "results"

@dataclass
class HoldingItem:
    ticker: str
    quantity: int
    purchase_price: float
    current_price: float

get_open_close_price_url = "https://api.polygon.io/v1/open-close/{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"
get_option_price_url = "https://api.polygon.io/v1/open-close/O:{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"

with open(metadata_fp) as metadata_f:
    metadata_dict = yaml.safe_load(metadata_f)

def is_purchase_stock(ticker):
    return len(ticker) == STOCK_TICKER_LENGTH

def generate_url_request(url, ticker, year, month, day):
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", metadata_dict["ACCOUNT"]["API_KEY"]))
    if not response.ok:
        for i in range(SLEEP_TIME):
            print(f"Sleeping for {SLEEP_TIME - i}")
            time.sleep(1)
    else:
        return response.json()
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", metadata_dict["ACCOUNT"]["API_KEY"]))
    if not response.ok:
        print("Something went wrong", url, ticker, year, month, day)
        exit()
    else:
        return response.json()
    
def get_price(ticker, year, month, day):
    if is_purchase_stock(ticker):
        response = generate_url_request(get_open_close_price_url, ticker, year, month, day)
        return response[STOCK_PRICE_INDICATOR]
    else:
        response = generate_url_request(get_option_price_url, ticker, year, month, day)
        return response[OPTION_PRICE_INDICATOR]

trade_history = pd.read_csv(metadata_dict["DATA"]["TRADE_HISTORY"])
trade_history["Date Bought"] = pd.to_datetime(trade_history["Date Bought"])
Path(RESULTS_DIR).mkdir(exist_ok=False)

def main():
    for portfolio_valuation_date in metadata_dict["PORTFOLIO_VALUATION"]["DATES"]:
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
                purchase_price = get_price(ticker, purchase_year, purchase_month, purchase_day)
            else:
                purchase_price = float(row["Purchase Price"])
            current_price = get_price(ticker, valuation_year, valuation_month, valuation_day)
            total_price = purchase_price * row["Shares Bought"]
            holdings['BANK'].current_price -= total_price
            holdings[ticker] = HoldingItem(ticker, row["Shares Bought"], purchase_price, current_price)
        print(f"Valuation at {valuation_year}/{valuation_month}/{valuation_day}")
        for holding, holding_info in holdings.items():
            print(holding, holding_info)
        break

if __name__ == "__main__":
    main()