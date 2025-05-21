from datetime import datetime

import pandas as pd

from io_utils import print_graph, print_rsi_graph
from stock_utils import get_stock_data, ma_strategy, buy_sell_signals, backtest, RSI


def get_stock_research_parameters():
    """Prompts the user for stock ticker and start date."""
    while True:
        try:
            stock = input("Enter a stock ticker: ")
            # Add any specific validation for stock ticker if needed
            if not stock:  # Basic check for non-empty input
                raise ValueError("Stock ticker cannot be empty.")
            break
        except Exception as e:
            print(f"Invalid input: {e}")
            continue

    while True:
        try:
            date_entry = input('Enter a start date in YYYY-MM-DD format: ')
            year, month, day = map(int, date_entry.split('-'))
            start_date = datetime(year=year, month=month, day=day).date()
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
        except Exception as e:
            print(f"An error occurred: {e}")
            continue
    return stock, start_date


def perform_stock_analysis(ticker, start_date, end_date, period, interval, long_ma, short_ma, initial_wealth_str):
    """Performs stock analysis using moving averages and RSI."""
    df = get_stock_data(ticker, start_date, end_date, period, interval)
    if df.empty:
        print(f"No data found for {ticker} from {start_date} to {end_date}. Aborting analysis.")
        return

    df = ma_strategy(df, long_ma, short_ma) # Corrected: short_MA to short_ma, long_MA to long_ma
    df = buy_sell_signals(df, ticker, start_date, end_date)
    df = backtest(df, ticker, start_date, end_date, initial_wealth_str) # Corrected: initial_wealth to initial_wealth_str
    print_graph(df, ticker)

    # Ensure 'Date' column is datetime for RSI calculation if not already
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    df_indexed = df.set_index('Date') # RSI function expects 'Date' index
    df_indexed, rsi = RSI(df_indexed) # RSI function modifies and returns df
    
    # print_rsi_graph needs the original df with 'Date' as column for plotting if it was modified
    # However, the RSI function returns df_indexed (which is df with Date as index)
    # and print_rsi_graph uses df.index for x-axis if 'Date' column is not present.
    # The original code did:
    # df['Date'] = pd.to_datetime(df['Date'])
    # df = df.set_index('Date')
    # df, rsi = RSI(df)
    # print_rsi_graph(df, rsi)
    # This implies print_rsi_graph can handle a DataFrame with 'Date' as index.
    print_rsi_graph(df_indexed, rsi)


long_MA_CONST = 200 # Renamed to avoid conflict with function parameter
short_MA_CONST = 50 # Renamed to avoid conflict with function parameter
initial_wealth_CONST = '1000' # Renamed
PERIOD_CONST = '60d'
INTERVAL_CONST = '1d'

# Get user inputs
stock_ticker, analysis_start_date = get_stock_research_parameters()

# Determine end_date
analysis_end_date = datetime.today().strftime('%Y-%m-%d')

# Perform analysis
perform_stock_analysis(stock_ticker, analysis_start_date, analysis_end_date,
                       PERIOD_CONST, INTERVAL_CONST,
                       long_MA_CONST, short_MA_CONST, initial_wealth_CONST)
