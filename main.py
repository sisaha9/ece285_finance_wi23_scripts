from lib.sessions import CachedLimiterSession
from requests_cache import BaseCache
from requests_ratelimiter import MemoryListBucket
from settings import (
    POLYGON_API_CALL_LIMIT,
    TRADE_HISTORY,
    TZ_PRESENT,
    PORTFOLIO_VALUATION_DATES,
    PORTFOLIO_VALUATION_LABELS,
    RESULTS_DIR,
    BANK_INITIAL_MONEY,
    ROUND_TO,
)
from lib.portfolio_valuator import PortfolioHandler
from lib.viz import generate_valuations_barplot
from lib.utils import save_evaluation, make_zip_file
from lib.discord_bot_handler import send_message
import datetime
import pandas as pd
import sys
from pathlib import Path


def main(session: CachedLimiterSession, ci=False):
    if RESULTS_DIR:
        Path(RESULTS_DIR).mkdir(exist_ok=False)
    trade_history = pd.read_csv(TRADE_HISTORY)
    trade_history["Date Bought"] = pd.to_datetime(trade_history["Date Bought"])
    tickers = list(
        set(["BANK"] + (trade_history["Ticker"] + "-" + trade_history["ID"].astype(str)).tolist())
    )
    dates = None
    labels = None
    portfolio_valuation_results = {}
    plot_list = {"Labels": []}
    message = ""
    if ci:
        date = pd.to_datetime(datetime.datetime.now(TZ_PRESENT))
        dates = [date]
        labels = [f"End of {date.month}/{date.day}/{date.year}"]
    else:
        dates = [pd.to_datetime(date) for date in PORTFOLIO_VALUATION_DATES]
        labels = PORTFOLIO_VALUATION_LABELS
    for idx in range(len(dates)):
        portfolio = PortfolioHandler(session)
        portfolio_valuation_results[labels[idx]] = portfolio.evaluate_portfolio(
            trade_history, dates[idx]
        )
        message = f"{message}Valuation for {dates[idx].date()}\n"
        message = (
            f"{message}{portfolio_valuation_results[labels[idx]].round(ROUND_TO).to_string()}\n"
        )
        message = f"{message}The total portfolio value is {round(portfolio_valuation_results[labels[idx]]['Total'].sum(), ROUND_TO)}\n"
        message = f"{message}The total profit is {round(portfolio_valuation_results[labels[idx]]['Total'].sum() - BANK_INITIAL_MONEY, ROUND_TO)}\n"
        plot_list["Labels"].append(labels[idx])
        for ticker in tickers:
            val = 0
            try:
                val = (
                    portfolio_valuation_results[labels[idx]]
                    .set_index("Ticker")
                    .loc[ticker]["Total"]
                )
            except:
                val = 0
            if ticker in plot_list:
                plot_list[ticker].append(val)
            else:
                plot_list[ticker] = [val]
        save_evaluation(portfolio_valuation_results[labels[idx]], dates[idx])
        print(f"Evaluation done for {labels[idx]}")
    plot_df = pd.DataFrame(plot_list)
    generate_valuations_barplot(plot_df)
    make_zip_file()
    print(message.strip())
    send_message(message.strip())


if __name__ == "__main__":
    session = CachedLimiterSession(
        per_minute=POLYGON_API_CALL_LIMIT, backend=BaseCache, bucket_class=MemoryListBucket
    )
    if len(sys.argv) <= 1:
        main(session)
    else:
        main(session, ci=True)
