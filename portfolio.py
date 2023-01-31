import numpy as np
import pandas as pd
import requests
import yaml
import time
from pathlib import Path
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import os
import sys
import datetime
import pytz

metadata_fp = "portfolio.yaml"
pst = pytz.timezone("America/Los_Angeles")

STOCK_TICKER_LENGTH = 3
SLEEP_TIME = 60 + 10
STOCK_PRICE_PURCHASE_INDICATOR = "low"
STOCK_PRICE_VALUATION_INDICATOR = "close"
OPTION_PRICE_PURCHASE_INDICATOR = "low"
OPTION_PRICE_VALUATION_INDICATOR = "close"
RESULTS_DIR = "results"
ROUND_TO = 2
MIN_HEIGHT = 0
XROT = 45
Y_OFFSET = 4
FIGSIZE=(20,20)
HOUR_THRESHOLD=23

POLYGON_API_KEY = os.environ['POLYGON_API_KEY']
try:
    DISCORD_API_KEY = os.environ['DISCORD_API_KEY']
    DISCORD_CHANNEL_ID = os.environ['DISCORD_CHANNEL_ID']
except:
    DISCORD_API_KEY = None
    DISCORD_CHANNEL_ID = None

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
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", POLYGON_API_KEY))
    if not response.ok:
        for i in range(SLEEP_TIME):
            print(f"Sleeping for {SLEEP_TIME - i}")
            time.sleep(1)
    else:
        return response.json()
    response = requests.get(url.replace("{ticker}", ticker).replace("{YYYY}", year).replace("{MM}", month).replace("{DD}", day).replace("{apiKey}", POLYGON_API_KEY))
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

def main(ci=False):
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
    if ci:
        today_date = datetime.datetime.now(pst).replace(tzinfo=None)
        if today_date.hour < HOUR_THRESHOLD:
            today_date = today_date - datetime.timedelta(days=1)
        metadata_dict["PORTFOLIO_VALUATION"]["DATES"] = [today_date]
        metadata_dict["PORTFOLIO_VALUATION"]["LABELS"] = [f"Valuation for {today_date.month}/{today_date.day}/{today_date.year}"]
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
        valuations["Labels"].append(f"{label_name}")
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
    print(valuations)
    df = pd.DataFrame(valuations)
    for identifier in identifiers:
        df[identifier] = df[identifier].astype(float)
    fig = df.set_index('Labels').plot(kind='bar', stacked=True, xlabel="Time", ylabel="Portfolio value in USD", title="Valuations of Portfolio", rot=XROT, figsize=FIGSIZE)
    for label, total_price in df.set_index('Labels').sum(axis=1).reset_index(drop=True).items():
        fig.text(label, total_price + Y_OFFSET, round(total_price), ha='center', weight='bold')
    for bar in fig.patches:
        fig.text(
            # Put the text in the middle of each bar. get_x returns the start
            # so we add half the width to get to the middle.
            bar.get_x() + (bar.get_width() / 2),
            # Vertically, add the height of the bar to the start of the bar,
            # along with the offset.
            bar.get_y() + (bar.get_height() / 2),
            # This is actual value we'll show.
            round(bar.get_height()),
            # Center the labels and style them a bit.
            ha='center',
            color='w',
            weight='bold',
        )
    # for c in fig.containers:
    #     labels = [np.round(v.get_height(), ROUND_TO) if v.get_height() > MIN_HEIGHT else '' for v in c]
    #     fig.bar_label(c, labels=labels, label_type='center')
    if RESULTS_DIR:
        plt.savefig(Path(RESULTS_DIR) / "valuations.png")
        print("Plot generated")
    if ci:
        message = metadata_dict["PORTFOLIO_VALUATION"]["LABELS"][0] + " is"
        total = 0
        for identifier in identifiers:
            total += float(valuations[identifier][0])
            message = f"{message} {identifier}: {valuations[identifier][0]},"
        message = f"{message} TOTAL: {total}"
        print(message)
        if DISCORD_API_KEY and DISCORD_CHANNEL_ID:
            import discord
            intents = discord.Intents.default()
            client = discord.Client(intents=intents)
            @client.event
            async def on_ready():
                channel = client.get_channel(int(DISCORD_CHANNEL_ID))
                await channel.send(message)
                await client.close()
            client.run(DISCORD_API_KEY)
    else:
        plt.show()
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        main()
    else:
        main(True)