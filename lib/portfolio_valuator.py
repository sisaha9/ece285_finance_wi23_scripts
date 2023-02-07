from settings import BANK_INITIAL_MONEY, POLYGON_VALUATION_INDICATOR
from lib.polygon_api_handler import get_closest_date_to_date, get_price
import pandas as pd
from lib.sessions import CachedLimiterSession


class PortfolioHandler:
    def __init__(self, session: CachedLimiterSession):
        self.current_bank_account = BANK_INITIAL_MONEY
        self.trade_history = {}
        self.session = session

    def evaluate_portfolio(self, trade_history: pd.DataFrame, evaluation_date: pd.Timestamp):
        date_threshold = get_closest_date_to_date(evaluation_date.to_pydatetime())
        for idx, trade in trade_history.iterrows():
            if trade["Date Bought"].to_pydatetime().date() <= date_threshold.date():
                self.record_trade(trade)
        portfolio_valuation_result = {}
        portfolio_valuation_result["BANK"] = {
            "Num Shares": 1,
            "Value Per Share": self.current_bank_account,
            "Total": self.current_bank_account,
            "Profit": self.current_bank_account - BANK_INITIAL_MONEY,
            "Evaluation Date": evaluation_date.to_pydatetime().date(),
        }
        for ticker in self.trade_history.keys():
            current_value_per_share, date_evaluated = get_price(
                ticker, evaluation_date.to_pydatetime(), POLYGON_VALUATION_INDICATOR, self.session
            )
            for id in self.trade_history[ticker].keys():
                portfolio_valuation_result[f"{ticker}-{id}"] = {
                    "Num Shares": self.trade_history[ticker][id]["Shares"],
                    "Value Per Share": current_value_per_share,
                }
                portfolio_valuation_result[f"{ticker}-{id}"]["Total"] = (
                    portfolio_valuation_result[f"{ticker}-{id}"]["Num Shares"]
                    * portfolio_valuation_result[f"{ticker}-{id}"]["Value Per Share"]
                )
                portfolio_valuation_result[f"{ticker}-{id}"]["Profit"] = (
                    current_value_per_share - self.trade_history[ticker][id]["Price"]
                ) * self.trade_history[ticker][id]["Shares"]
                portfolio_valuation_result[f"{ticker}-{id}"][
                    "Evaluation Date"
                ] = date_evaluated.to_pydatetime().date()
        evaluation_result_df = (
            pd.DataFrame(portfolio_valuation_result)
            .transpose()
            .reset_index()
            .rename({"index": "Ticker"}, axis=1)
            .astype(
                {
                    "Ticker": "string",
                    "Num Shares": "int64",
                    "Value Per Share": "float64",
                    "Total": "float64",
                    "Profit": "float64",
                    "Evaluation Date": "datetime64[ns]",
                }
            )
        )
        return evaluation_result_df

    def record_trade(self, trade: pd.Series):
        if trade["Shares Bought"] == 0:
            print("Ignoring trade with 0 purchases", trade)
            return
        if trade["Purchase Type"].lower() not in ["long", "short"]:
            print("Ignoring trade with invalid purchase type", trade)
            return
        if trade["Purchase Type"].lower() == "long":
            if trade["Shares Bought"] > 0:
                if (
                    trade["Ticker"] in self.trade_history
                    and trade["ID"] in self.trade_history[trade["Ticker"]]
                ):
                    if (
                        trade["Purchase Price"]
                        != self.trade_history[trade["Ticker"]][trade["ID"]]["Price"]
                    ):
                        print(
                            "Found a different purchase price for the same ID. Something's wrong",
                            trade,
                        )
                        exit()
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] += trade[
                        "Shares Bought"
                    ]
                else:
                    self.trade_history[trade["Ticker"]] = {}
                    self.trade_history[trade["Ticker"]][trade["ID"]] = {
                        "Shares": trade["Shares Bought"],
                        "Price": trade["Purchase Price"],
                        "Sells": [],
                        "Type": "Long",
                    }
            elif trade["Shares Bought"] < 0:
                if (
                    trade["Ticker"] in self.trade_history
                    and trade["ID"] in self.trade_history[trade["Ticker"]]
                ):
                    if (
                        abs(trade["Shares Bought"])
                        > self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"]
                    ):
                        print("Trying to sell more then you have. Trade invalid", trade)
                        exit()
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] += trade[
                        "Shares Bought"
                    ]
                    sell = {"Shares": trade["Shares Bought"], "Price": trade["Purchase Price"]}
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                else:
                    print("Invalid sell as trade ID and ticker combination does not exist", trade)
                    exit()
            self.current_bank_account -= trade["Purchase Price"] * trade["Shares Bought"]
        else:
            if trade["Shares Bought"] < 0:
                if (
                    trade["Ticker"] in self.trade_history
                    and trade["ID"] in self.trade_history[trade["Ticker"]]
                ):
                    if (
                        trade["Purchase Price"]
                        != self.trade_history[trade["Ticker"]][trade["ID"]]["Price"]
                    ):
                        print(
                            "Found a different purchase price for the same ID. Something's wrong",
                            trade,
                        )
                        exit()
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] += trade[
                        "Shares Bought"
                    ]
                else:
                    self.trade_history[trade["Ticker"]] = {}
                    self.trade_history[trade["Ticker"]][trade["ID"]] = {
                        "Shares": trade["Shares Bought"],
                        "Price": trade["Purchase Price"],
                        "Sells": [],
                        "Type": "Short",
                    }
            elif trade["Shares Bought"] > 0:
                if (
                    trade["Ticker"] in self.trade_history
                    and trade["ID"] in self.trade_history[trade["Ticker"]]
                ):
                    if trade["Shares Bought"] > abs(
                        self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"]
                    ):
                        print("Trying to sell more then you have. Trade invalid", trade)
                        exit()
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] += trade[
                        "Shares Bought"
                    ]
                    sell = {
                        "Shares": self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"],
                        "Price": trade["Purchase Price"],
                    }
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                else:
                    print("Invalid sell as trade ID and ticker combination does not exist", trade)
                    exit()
            self.current_bank_account -= trade["Purchase Price"] * trade["Shares Bought"]
        return
