import yfinance as yf
import pandas as pd # Added import for pandas

from constants import dividend_stocks, growth_stocks, index_funds
from io_utils import query_yes_no
from stock_utils import generate_portfolio

VERBOSE = False


def get_user_investment_preferences():
    """Gets user input for investment amount and preferences."""
    while True:
        try:
            amount = float(input("Enter amount of money ($) to invest: "))
        except ValueError:
            print("Not a number!")
            continue
        else:
            break
    dividend_investing = query_yes_no("Do you want to invest in high dividend stocks? ")
    growth_investing = query_yes_no("Do you want to invest in growth stocks? ")
    index_investing = query_yes_no("Do you want to invest in index funds? ")
    return amount, dividend_investing, growth_investing, index_investing


def prepare_stock_selection(dividend_investing, growth_investing, index_investing,
                            dividend_stocks, growth_stocks, index_funds):
    """Prepares the list of stock tickers based on user preferences."""
    optional_stocks = []
    if dividend_investing:
        optional_stocks.extend(dividend_stocks)
    if growth_investing:
        optional_stocks.extend(growth_stocks)
    if index_investing:
        optional_stocks.extend(index_funds)
    return list(set(optional_stocks))  # Remove duplicates


def fetch_stock_data(tickers, period):
    """Fetches stock data using yfinance and calculates mean and current prices."""
    if not tickers:
        return []
    stocks = yf.Tickers(tickers)
    # Fetching 'Close' prices, ensure it's a DataFrame even with one ticker
    stocks_data = stocks.history(period=period)
    
    if stocks_data.empty:
        # print(f"Warning: No data returned from yfinance for tickers: {tickers}")
        return []

    # Ensure 'Close' is present, could be MultiIndex if multiple tickers
    if 'Close' in stocks_data:
        stocks_data_close = stocks_data['Close']
    elif isinstance(stocks_data.columns, pd.MultiIndex):
        # Fallback for MultiIndex, try to get 'Close' price for each ticker
        # This handles cases where some tickers might fail and yfinance returns a MultiIndex
        # with 'Close' under each ticker symbol.
        # We will process valid tickers and skip those with errors.
        valid_tickers_data = []
        for ticker in tickers:
            if (ticker, 'Close') in stocks_data.columns:
                valid_tickers_data.append(stocks_data[(ticker, 'Close')].rename(ticker))
        if not valid_tickers_data:
            # print(f"Warning: 'Close' price data not found for tickers: {tickers}")
            return []
        stocks_data_close = pd.concat(valid_tickers_data, axis=1)
    else:
        # print(f"Warning: 'Close' price data not found in yfinance output for tickers: {tickers}")
        return []

    if stocks_data_close.empty:
        # print(f"Warning: 'Close' price data is empty for tickers: {tickers}")
        return []

    # If only one ticker, stocks_data_close might be a Series, convert to DataFrame
    if isinstance(stocks_data_close, pd.Series):
        stocks_data_close = stocks_data_close.to_frame(name=tickers[0])

    stocks_current_prices = stocks_data_close.iloc[-1].tolist()
    stocks_mean_prices = stocks_data_close.mean(axis=0).tolist()
    stocks_prices_names = list(stocks_data_close.columns)

    suitable_stocks = []
    for stock_name, mean_price, current_price in zip(stocks_prices_names, stocks_mean_prices, stocks_current_prices):
        if pd.isna(mean_price) or pd.isna(current_price):
            # print(f"Warning: Skipping {stock_name} due to missing data (mean or current price).")
            continue
        suitable_stocks.append((stock_name, mean_price, current_price, current_price - mean_price))
    return suitable_stocks


if __name__ == "__main__":
    # Step 1: Get user input
    amount, dividend_investing, growth_investing, index_investing = get_user_investment_preferences()

    # Step 2: Add stock data based on user-selected options
    optional_stocks = prepare_stock_selection(dividend_investing, growth_investing, index_investing,
                                            dividend_stocks, growth_stocks, index_funds)

    PERIOD = '2y'

    # Step 3: Scan suitable stocks for mean price
    suitable_stocks = fetch_stock_data(optional_stocks, PERIOD)

    if VERBOSE:
        # Print the list of suitable stocks and their mean price
        print("Suitable stocks:")
        # The following loop assumes suitable_stocks is a list of tuples (stock, mean_price, current_price, diff)
        # but the print statement seems to expect (stock, price) where price is likely mean_price.
        # Adjusting to print the stock name and its mean price for clarity if VERBOSE is True.
        for stock_name, mean_p, _, _ in suitable_stocks: # Assuming structure from fetch_stock_data
            print(f"found {stock_name} for mean price {mean_p}")
        print("=======================")

    # Step 4: Allocate investment amount among selected stocks
    # generate_portfolio expects stock_prices as: list of (name, mean_price, current_price, diff)
    # and returns list of (stock_ticker, num_shares, mean_price, current_price)
    portfolio = generate_portfolio(stock_prices=suitable_stocks, total_budget=amount)

    # Step 5: Generate report or output for user
    print("Portfolio recommendation:") # Changed title for clarity
    price_sum = 0
    # Portfolio items are (stock, num_shares, mean_price_at_purchase_time, current_price)
    for stock_name, num_shares, mean_price_at_purchase_time, current_price_val in portfolio:
        if num_shares > 0:
            # The original print used 'mean_price' which could be ambiguous.
            # Using 'mean_price_at_purchase_time' from the portfolio tuple.
            # The 'price_sum' calculation should also use this consistent mean price.
            price_sum += num_shares * mean_price_at_purchase_time
            print(f"Buy {num_shares} shares of {stock_name}. "
                  f"Current price: {current_price_val:.2f} | "
                  f"Mean {PERIOD} price (used for allocation): {mean_price_at_purchase_time:.2f}")

    print(f"Total estimated cost (based on mean prices at allocation): ${price_sum:,.2f}")
