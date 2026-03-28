import logging
from datetime import datetime

import pandas as pd

# Updated to use the new function names from io_utils
from io_utils import get_price_ma_and_wealth_plots, get_rsi_plot 
from stock_utils import get_stock_data, ma_strategy, buy_sell_signals, backtest, RSI

logger = logging.getLogger(__name__)


def get_stock_research_parameters():
    """Prompts the user for stock ticker and start date."""
    while True:
        try:
            stock = input("Enter a stock ticker: ")
            # Add any specific validation for stock ticker if needed
            if not stock:  # Basic check for non-empty input
                raise ValueError("Stock ticker cannot be empty.")
            break
        except ValueError as e:
            logger.warning(f"Invalid input: {e}")
            continue

    while True:
        try:
            date_entry = input('Enter a start date in YYYY-MM-DD format: ')
            year, month, day = map(int, date_entry.split('-'))
            start_date = datetime(year=year, month=month, day=day).date()
            break
        except ValueError:
            logger.warning("Invalid date format. Please use YYYY-MM-DD.")
        except (TypeError, AttributeError) as e:
            logger.error(f"An error occurred: {e}")
            continue
    return stock, start_date


def perform_stock_analysis(ticker, start_date, end_date, period, interval, long_ma, short_ma, initial_wealth_str):
    """Performs stock analysis using moving averages and RSI."""
    df = get_stock_data(ticker, start_date, end_date, period, interval)
    if df.empty:
        logger.warning(f"No data found for {ticker} from {start_date} to {end_date}. Aborting analysis.")
        return

    df = ma_strategy(df, long_ma, short_ma)
    df = buy_sell_signals(df, ticker, start_date, end_date) # This function prints to console
    df = backtest(df, ticker, start_date, end_date, initial_wealth_str) # This function prints to console
    
    # Use the new plotting functions that return figures
    fig_price, fig_wealth = get_price_ma_and_wealth_plots(df, ticker)
    # In a script context, we would call plt.show() for each figure.
    # For library use, returning figures or further processing would be needed.
    # Since this is now primarily a library for app.py, direct plt.show() here might be too much.
    # However, if run as a script, the user expects to see plots.
    # For now, let's assume if perform_stock_analysis is called directly (not typical anymore),
    # it should behave like the old script.
    if __name__ == "__main__": # Check if this function is being run as part of the script's main execution
        fig_price.show()
        fig_wealth.show()


    # Ensure 'Date' column is datetime for RSI calculation if not already
    df_for_rsi = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_for_rsi['Date']):
        df_for_rsi['Date'] = pd.to_datetime(df_for_rsi['Date'])
    
    # RSI function from stock_utils might expect 'Date' as index or handle it internally.
    # Based on previous usage, it seems to return a df with 'Date' as column and an RSI series.
    # The get_rsi_plot expects a DataFrame with 'Close' and a DatetimeIndex, and the RSI series.
    df_with_rsi_col, rsi_series = RSI(df_for_rsi) # df_for_rsi is modified by RSI to add 'RSI_14'

    # Prepare df for get_rsi_plot
    df_plot_rsi = df_with_rsi_col.copy()
    if 'Date' in df_plot_rsi.columns and not isinstance(df_plot_rsi.index, pd.DatetimeIndex):
        df_plot_rsi = df_plot_rsi.set_index('Date')
    
    fig_rsi = get_rsi_plot(df_plot_rsi, rsi_series)
    if __name__ == "__main__": # Similar to above, only show plot if script is run directly
         fig_rsi.show()
    # Note: For app.py, these figures (fig_price, fig_wealth, fig_rsi) would ideally be returned by
    # perform_stock_analysis or handled via callbacks if we wanted app.py to display them.
    # The current structure of perform_stock_analysis does not return them.
    # This will be handled by app.py calling the io_utils functions directly.


if __name__ == "__main__":
    # Constants for script execution
    LONG_MA_CONST = 200
    SHORT_MA_CONST = 50
    INITIAL_WEALTH_CONST = '1000'
    # PERIOD_CONST is used by get_stock_data if start/end dates are not provided.
    # Here, we prompt for start_date, so period_str in get_stock_data should be None.
    # However, perform_stock_analysis takes 'period' as an arg, which is confusing.
    # Let's assume for direct script execution, we're using a fixed period or no period if start_date is given.
    # The get_stock_data function's `period` param is `period_str`.
    # The original script had `period = '60d'` but then used start_date from input.
    # This implies `period_str` in get_stock_data should be None when start_date is used.
    # For clarity, if this script is run, 'period' for perform_stock_analysis will be set to None
    # and 'interval' will be '1d'.
    
    INTERVAL_CONST = '1d'

    # Get user inputs
    stock_ticker, analysis_start_date_obj = get_stock_research_parameters() # Returns date object

    # Determine end_date
    analysis_end_date_str = datetime.today().strftime('%Y-%m-%d')
    analysis_start_date_str = analysis_start_date_obj.strftime('%Y-%m-%d')


    # Perform analysis
    # The 'period' argument for perform_stock_analysis is a bit redundant if start/end dates are used.
    # `get_stock_data` uses `period_str`. We'll pass None for `period_str` if using dates.
    # The `perform_stock_analysis` function itself calls `get_stock_data` with its `period` and `interval` args.
    # So, we should pass `period_str=None` to `perform_stock_analysis` if we intend to use dates primarily.
    # However, `perform_stock_analysis` is defined with `period` not `period_str`.
    # Let's stick to its definition and assume it handles it or `get_stock_data` handles it.
    # The original script defined `period = '60d'` but this was for `get_stock_data`,
    # which is now called inside `perform_stock_analysis`.
    # If run directly, we use date range, so `period_str` inside `get_stock_data` (called by `perform_stock_analysis`) should be None.
    # The `period` argument to `perform_stock_analysis` should be `None` in this case.
    
    logger.info(f"Running analysis for {stock_ticker} from {analysis_start_date_str} to {analysis_end_date_str}...")
    perform_stock_analysis(ticker=stock_ticker, 
                           start_date=analysis_start_date_str, 
                           end_date=analysis_end_date_str, 
                           period=None, # Explicitly None as we are using date ranges
                           interval=INTERVAL_CONST, 
                           long_ma=LONG_MA_CONST, 
                           short_ma=SHORT_MA_CONST, 
                           initial_wealth_str=INITIAL_WEALTH_CONST)
