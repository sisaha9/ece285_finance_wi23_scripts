from settings import BANK_INITIAL_MONEY, POLYGON_VALUATION_INDICATOR
from lib.polygon_api_handler import (
    get_closest_date_to_date,
    get_price,
    is_purchase_stock,
    is_purchase_call,
    is_purchase_put,
)
import pandas as pd
from lib.sessions import CachedLimiterSession


class PortfolioHandler:
    def __init__(self, session: CachedLimiterSession):
        self.current_bank_account = BANK_INITIAL_MONEY
        self.trade_history = {}
        self.session = session

    def evaluate_portfolio(
        self, trade_history: pd.DataFrame, evaluation_date: pd.Timestamp
    ) -> pd.DataFrame:
        date_threshold = get_closest_date_to_date(evaluation_date.to_pydatetime())
        for _, trade in trade_history.iterrows():
            if trade["Date Bought"].to_pydatetime().date() <= date_threshold.date():
                self.record_trade(trade)
        portfolio_valuation_result = {}
        portfolio_valuation_result["BANK"] = {
            "Num Shares": 1,
            "Bought At": BANK_INITIAL_MONEY,
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
                    "Bought At": self.trade_history[ticker][id]["Price"],
                    "Value Per Share": current_value_per_share,
                }
                portfolio_valuation_result[f"{ticker}-{id}"]["Total"] = (
                    portfolio_valuation_result[f"{ticker}-{id}"]["Num Shares"]
                    * portfolio_valuation_result[f"{ticker}-{id}"]["Value Per Share"]
                )
                if self.trade_history[ticker][id]["Type"] == "long":
                    portfolio_valuation_result[f"{ticker}-{id}"]["Profit"] = (
                        current_value_per_share - self.trade_history[ticker][id]["Price"]
                    ) * self.trade_history[ticker][id]["Shares"]
                elif self.trade_history[ticker][id]["Type"] == "short":
                    portfolio_valuation_result[f"{ticker}-{id}"]["Profit"] = (
                        self.trade_history[ticker][id]["Price"] - current_value_per_share
                    ) * self.trade_history[ticker][id]["Shares"]
                else:
                    print(
                        "Invalid trade history type found", self.trade_history[ticker][id]["Type"]
                    )
                    exit()
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
                    "Bought At": "float64",
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
        elif trade["Purchase Type"].lower() not in ["long", "short"]:
            print("Ignoring trade with invalid purchase type", trade)
        elif is_purchase_stock(trade["Ticker"]):
            if trade["Purchase Type"].lower() == "long":
                self.record_long_stock(trade)
            elif trade["Purchase Type"].lower() == "short":
                self.record_short_stock(trade)
        elif is_purchase_call(trade["Ticker"]):
            if trade["Purchase Type"].lower() == "long":
                self.record_long_call(trade)
            elif trade["Purchase Type"].lower() == "short":
                self.record_short_call(trade)
        elif is_purchase_put(trade["Ticker"]):
            if trade["Purchase Type"].lower() == "long":
                self.record_long_put(trade)
            elif trade["Purchase Type"].lower() == "short":
                self.record_short_put(trade)

    def record_long_stock(self, trade: pd.Series):
        if trade["Shares Bought"] > 0:
            if (
                trade["Ticker"] in self.trade_history
                and trade["ID"] in self.trade_history[trade["Ticker"]]
            ):
                print("This trade ID already exists for this ticker")
                exit()
            else:
                self.trade_history[trade["Ticker"]] = {}
                self.trade_history[trade["Ticker"]][trade["ID"]] = {
                    "Shares": trade["Shares Bought"],
                    "Price": trade["Purchase Price"],
                    "Sells": [],
                    "Type": "long",
                }
                self.current_bank_account -= trade["Shares Bought"] * trade["Purchase Price"]
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
                else:
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] -= abs(
                        trade["Shares Bought"]
                    )
                    sell = {
                        "Shares": abs(trade["Shares Bought"]),
                        "Price": trade["Purchase Price"],
                    }
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                    self.current_bank_account += (
                        abs(trade["Shares Bought"]) * trade["Purchase Price"]
                    )
            else:
                print("This trade ID does not exist for this ticker")
                exit()

    def record_short_stock(self, trade: pd.Series):
        if trade["Shares Bought"] > 0:
            if (
                trade["Ticker"] in self.trade_history
                and trade["ID"] in self.trade_history[trade["Ticker"]]
            ):
                print("This trade ID already exists for this ticker")
                exit()
            else:
                self.trade_history[trade["Ticker"]] = {}
                self.trade_history[trade["Ticker"]][trade["ID"]] = {
                    "Shares": trade["Shares Bought"],
                    "Price": trade["Purchase Price"],
                    "Sells": [],
                    "Type": "short",
                }
                self.current_bank_account += trade["Shares Bought"] * trade["Purchase Price"]
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
                else:
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] -= abs(
                        trade["Shares Bought"]
                    )
                    sell = {
                        "Shares": abs(trade["Shares Bought"]),
                        "Price": trade["Purchase Price"],
                    }
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                    self.current_bank_account -= (
                        abs(trade["Shares Bought"]) * trade["Purchase Price"]
                    )
            else:
                print("This trade ID does not exist for this ticker")
                exit()

    def record_long_call(self, trade: pd.Series):
        print("We don't support long calls")
        exit()

    def record_long_put(self, trade: pd.Series):
        print("We don't support long puts")
        exit()

    def record_short_call(self, trade: pd.Series):
        if trade["Shares Bought"] > 0:
            if (
                trade["Ticker"] in self.trade_history
                and trade["ID"] in self.trade_history[trade["Ticker"]]
            ):
                print("This trade ID already exists for this ticker")
                exit()
            else:
                self.trade_history[trade["Ticker"]] = {}
                self.trade_history[trade["Ticker"]][trade["ID"]] = {
                    "Shares": trade["Shares Bought"],
                    "Price": trade["Purchase Price"],
                    "Sells": [],
                    "Type": "long",
                }
                self.current_bank_account -= trade["Shares Bought"] * trade["Purchase Price"]
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
                else:
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] -= abs(
                        trade["Shares Bought"]
                    )
                    sell = {
                        "Shares": abs(trade["Shares Bought"]),
                        "Price": trade["Purchase Price"],
                    }
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                    self.current_bank_account += (
                        abs(trade["Shares Bought"]) * trade["Purchase Price"]
                    )
            else:
                print("This trade ID does not exist for this ticker")
                exit()

    def record_short_put(self, trade: pd.Series):
        if trade["Shares Bought"] > 0:
            if (
                trade["Ticker"] in self.trade_history
                and trade["ID"] in self.trade_history[trade["Ticker"]]
            ):
                print("This trade ID already exists for this ticker")
                exit()
            else:
                self.trade_history[trade["Ticker"]] = {}
                self.trade_history[trade["Ticker"]][trade["ID"]] = {
                    "Shares": trade["Shares Bought"],
                    "Price": trade["Purchase Price"],
                    "Sells": [],
                    "Type": "long",
                }
                self.current_bank_account -= trade["Shares Bought"] * trade["Purchase Price"]
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
                else:
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Shares"] -= abs(
                        trade["Shares Bought"]
                    )
                    sell = {
                        "Shares": abs(trade["Shares Bought"]),
                        "Price": trade["Purchase Price"],
                    }
                    self.trade_history[trade["Ticker"]][trade["ID"]]["Sells"].append(sell)
                    self.current_bank_account += (
                        abs(trade["Shares Bought"]) * trade["Purchase Price"]
                    )
            else:
                print("This trade ID does not exist for this ticker")
                exit()
