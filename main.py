import yfinance as yf
import pandas as pd # Added import for pandas

from constants import dividend_stocks, growth_stocks, index_funds
from io_utils import query_yes_no
from stock_utils import generate_portfolio
from cached_stock_data import get_stock_data_cached
from parallel_processing import fetch_multiple_stocks_parallel

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


def _get_stock_stats(ticker, period):
    """Helper to fetch data and calc stats for a single stock."""
    df = get_stock_data_cached(ticker, startdate=None, enddate=None, period_str=period, interval_str='1d')
    if df.empty or 'Close' not in df.columns:
        return None
    
    current_price = df['Close'].iloc[-1]
    mean_price = df['Close'].mean()
    
    if pd.isna(mean_price) or pd.isna(current_price):
        return None
        
    return (ticker, mean_price, current_price, current_price - mean_price)

def fetch_stock_data(tickers, period):
    """Fetches stock data using cached parallel execution."""
    if not tickers:
        return []
    
    # Use parallel processing to fetch and calculate stats
    results = fetch_multiple_stocks_parallel(tickers, _get_stock_stats, period=period)
    
    # Filter out None results
    suitable_stocks = [r for r in results if r is not None]
    
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
