import yfinance as yf
import pandas as pd
import datetime
from settings import START_OF_TRADE_DAY, END_OF_TRADE_DAY, TZ_LOOKUP


def get_current_price(ticker: str, indicator: str):
    return get_price_at(ticker, datetime.datetime.now(TZ_LOOKUP), indicator)


def get_price_at(ticker: str, date: datetime.datetime, indicator: str):
    new_date = get_nearest_datetime_match(date)
    start_interval = pd.to_datetime(new_date.replace(hour=START_OF_TRADE_DAY, minute=0, second=0))
    end_interval = pd.to_datetime(new_date.replace(hour=END_OF_TRADE_DAY, minute=0, second=0))
    print(
        f"Requested data starting from {start_interval.month}/{start_interval.day}/{start_interval.year} {start_interval.hour}-{start_interval.minute}-{start_interval.second} and ending at {end_interval.month}/{end_interval.day}/{end_interval.year} {end_interval.hour}-{end_interval.minute}-{end_interval.second}"
    )
    relevant_prices = get_price_between_intervals(ticker, start_interval, end_interval)
    print(
        f"Received data starting from {relevant_prices.index[0].month}/{relevant_prices.index[0].day}/{relevant_prices.index[0].year} {relevant_prices.index[0].hour}-{relevant_prices.index[0].minute}-{relevant_prices.index[0].second} and ending at {relevant_prices.index[-1].month}/{relevant_prices.index[-1].day}/{relevant_prices.index[-1].year} {relevant_prices.index[-1].hour}-{relevant_prices.index[-1].minute}-{relevant_prices.index[-1].second}"
    )
    selected_price = relevant_prices.iloc[
        relevant_prices.index.get_indexer([new_date], method="nearest")
    ][indicator]
    print(
        f"Selecting price from {selected_price.index[0].month}/{selected_price.index[0].day}/{selected_price.index[0].year} {selected_price.index[0].hour}-{selected_price.index[0].minute}-{selected_price.index[0].second}"
    )
    return selected_price.iloc[0]


def get_price_between_intervals(
    ticker: str, start_interval: pd.Timestamp, end_interval: pd.Timestamp
):
    relevant_prices = yf.download(ticker, start=start_interval, end=end_interval, interval="1m")
    return relevant_prices


def get_nearest_datetime_match(date: datetime.datetime):
    delta = 0
    if date.weekday() == 6:
        delta = 2
    elif date.weekday() == 5:
        delta = 1
    new_date = date - datetime.timedelta(days=delta)
    if delta > 0:
        new_date = new_date.replace(hour=END_OF_TRADE_DAY, minute=0, second=0)
    else:
        new_date = new_date.replace(second=0)
    return new_date
