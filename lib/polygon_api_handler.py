import time
import pandas as pd
import datetime
from lib.sessions import CachedLimiterSession
from settings import (
    POLYGON_API_KEY,
    POLYGON_STOCK_PRICE_URL,
    POLYGON_OPTION_PRICE_URL,
    STOCK_TICKER_LENGTH,
    TZ_PRESENT,
    POLYGON_HOUR_THRESHOLD,
    POLYGON_API_CALL_PERIOD,
)


def generate_url_request(
    url: str, ticker: str, year: str, month: str, day: str, session: CachedLimiterSession
):
    response = session.get(
        url.replace("{ticker}", ticker)
        .replace("{YYYY}", year)
        .replace("{MM}", month)
        .replace("{DD}", day)
        .replace("{apiKey}", POLYGON_API_KEY)
    )
    if not response.ok:
        for i in range(POLYGON_API_CALL_PERIOD):
            print(f"Sleeping for {POLYGON_API_CALL_PERIOD - i}")
            time.sleep(1)
    else:
        return response.json()
    response = session.get(
        url.replace("{ticker}", ticker)
        .replace("{YYYY}", year)
        .replace("{MM}", month)
        .replace("{DD}", day)
        .replace("{apiKey}", POLYGON_API_KEY)
    )
    if not response.ok:
        print("Something went wrong with the Polygon call", url, ticker, year, month, day)
        exit()
    else:
        return response.json()


def get_price_polygon(
    ticker: str, year: str, month: str, day: str, indicator: str, session: CachedLimiterSession
):
    if is_purchase_stock(ticker):
        response = generate_url_request(POLYGON_STOCK_PRICE_URL, ticker, year, month, day, session)
        return float(response[indicator])
    else:
        response = generate_url_request(
            POLYGON_OPTION_PRICE_URL, ticker, year, month, day, session
        )
        return float(response[indicator])


def extract_option_expiration(ticker: str):
    relevant_portion = ticker[3:9]
    new_date = datetime.datetime(
        year=int("20" + relevant_portion[:2]),
        month=int(relevant_portion[2:4]),
        day=int(relevant_portion[4:]),
    )
    return new_date


def limit_date_option(ticker: str, date: datetime.datetime):
    new_date = date
    if not is_purchase_stock(ticker):
        new_date = extract_option_expiration(ticker)
    return new_date


def get_price(ticker: str, date: datetime.datetime, indicator: str, session: CachedLimiterSession):
    new_date = limit_date_option(ticker, date)
    new_date = get_closest_date_to_date(new_date)
    year = "{:04}".format(new_date.year)
    month = "{:02}".format(new_date.month)
    day = "{:02}".format(new_date.day)
    return get_price_polygon(ticker, year, month, day, indicator, session), pd.to_datetime(
        new_date
    )


def is_purchase_stock(ticker: str):
    return len(ticker) == STOCK_TICKER_LENGTH


def get_closest_date_to_date(date: datetime.datetime):
    new_date = date
    if date.date() > datetime.datetime.now(TZ_PRESENT).date():
        new_date = datetime.datetime.now(TZ_PRESENT)
    if (
        new_date.date() == datetime.datetime.now(TZ_PRESENT).date()
        and new_date.hour < POLYGON_HOUR_THRESHOLD
    ):
        new_date = new_date - datetime.timedelta(days=1)
    if new_date.weekday() == 6:
        new_date = new_date - datetime.timedelta(days=2)
    elif new_date.weekday() == 5:
        new_date = new_date - datetime.timedelta(days=1)
    return new_date
