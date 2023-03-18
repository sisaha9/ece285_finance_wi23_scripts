import os
import pytz
import datetime
import pandas as pd

TZ_LOOKUP = pytz.timezone("America/New_York")
TZ_PRESENT = pytz.timezone("America/Los_Angeles")
current_dt = pd.to_datetime(datetime.datetime.now())
DT_TO_PRESENT = TZ_LOOKUP.localize(current_dt) - TZ_PRESENT.localize(current_dt)
DT_TO_LOOKUP = TZ_PRESENT.localize(current_dt) - TZ_LOOKUP.localize(current_dt)
del current_dt
TRADE_HISTORY = "data/TradeHistory.csv"
BANK_INITIAL_MONEY = 10000.0
PORTFOLIO_VALUATION_DATES = [
    "1/13/2023",
    "1/20/2023",
    "1/27/2023",
    "2/3,2023",
    "2/10/2023",
    "2/17/2023",
    "2/24/2023",
    "3/3/2023",
    "3/10/2023",
    "3/17/2023",
]
PORTFOLIO_VALUATION_LABELS = [
    "End of Week 1",
    "End of Week 2",
    "End of Week 3",
    "End of Week 4",
    "End of Week 5",
    "End of Week 6",
    "End of Week 7",
    "End of Week 8",
    "End of Week 9",
    "End of Week 10",
]
RESULTS_DIR = "results"
ROUND_TO = 2

# Plots
XROT = 45
Y_OFFSET = 8
FIGSIZE = (20, 20)
BBOX_ANCHOR = (1.04, 1.0)

# YFinance
END_OF_TRADE_DAY = 17
START_OF_TRADE_DAY = 8

# Discord
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Polygon
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
POLYGON_API_CALL_PERIOD = 65
POLYGON_API_CALL_LIMIT = 5
POLYGON_STOCK_PRICE_URL = (
    "https://api.polygon.io/v1/open-close/{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"
)
POLYGON_OPTION_PRICE_URL = "https://api.polygon.io/v1/open-close/O:{ticker}/{YYYY}-{MM}-{DD}?adjusted=true&apiKey={apiKey}"
STOCK_TICKER_LENGTH = 3
POLYGON_HOUR_THRESHOLD = 21
POLYGON_VALUATION_INDICATOR = "close"
SEND_MESSAGE = False
