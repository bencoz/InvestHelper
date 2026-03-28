import yfinance as yf
import pandas as pd
import logging
from typing import Optional, Tuple, List

from constants import dividend_stocks, growth_stocks, index_funds
from io_utils import query_yes_no
from stock_utils import generate_portfolio
from cached_stock_data import get_stock_data_cached
from parallel_processing import fetch_multiple_stocks_parallel
from exceptions import InvestHelperError, DataFetchError

logger = logging.getLogger(__name__)

VERBOSE = False


def get_user_investment_preferences() -> Tuple[float, bool, bool, bool]:
    """Gets user input for investment amount and preferences."""
    while True:
        try:
            amount = float(input("Enter amount of money ($) to invest: "))
        except ValueError:
            logger.warning("Invalid input: user entered a non-numeric value for investment amount.")
            continue
        else:
            break
    dividend_investing = query_yes_no("Do you want to invest in high dividend stocks? ")
    growth_investing = query_yes_no("Do you want to invest in growth stocks? ")
    index_investing = query_yes_no("Do you want to invest in index funds? ")
    return amount, dividend_investing, growth_investing, index_investing


def prepare_stock_selection(dividend_investing: bool, growth_investing: bool, index_investing: bool,
                            dividend_stocks: List[str], growth_stocks: List[str], index_funds: List[str]) -> List[str]:
    """Prepares the list of stock tickers based on user preferences."""
    optional_stocks = []
    if dividend_investing:
        optional_stocks.extend(dividend_stocks)
    if growth_investing:
        optional_stocks.extend(growth_stocks)
    if index_investing:
        optional_stocks.extend(index_funds)
    return list(set(optional_stocks))  # Remove duplicates


def _get_stock_stats(ticker: str, period: str) -> Optional[Tuple[str, float, float, float]]:
    """Helper to fetch data and calc stats for a single stock."""
    df = get_stock_data_cached(ticker, startdate=None, enddate=None, period_str=period, interval_str='1d')
    if df.empty or 'Close' not in df.columns:
        return None
    
    current_price = float(df['Close'].iloc[-1].item()) if isinstance(df['Close'].iloc[-1], pd.Series) else float(df['Close'].iloc[-1])
    mean_price = float(df['Close'].tail(90).mean())
    
    if pd.isna(mean_price) or pd.isna(current_price):
        return None
        
    return (ticker, mean_price, current_price, current_price - mean_price)

def fetch_stock_data(tickers: List[str], period: str) -> List[Tuple[str, float, float, float]]:
    """Fetches stock data using cached parallel execution."""
    if not tickers:
        return []
    
    # Use parallel processing to fetch and calculate stats
    results = fetch_multiple_stocks_parallel(tickers, _get_stock_stats, period=period)
    
    # Filter out None results
    suitable_stocks = [r for r in results if r is not None]
    
    return suitable_stocks


if __name__ == "__main__":
    from logging_config import setup_logging
    import logging
    
    # Initialize logging
    logger = setup_logging()
    
    try:
        # Step 1: Get user input
        amount, dividend_investing, growth_investing, index_investing = get_user_investment_preferences()

        # Step 2: Add stock data based on user-selected options
        optional_stocks = prepare_stock_selection(dividend_investing, growth_investing, index_investing,
                                                dividend_stocks, growth_stocks, index_funds)

        PERIOD = '2y'

        # Step 3: Scan suitable stocks for mean price
        suitable_stocks = fetch_stock_data(optional_stocks, PERIOD)

        if VERBOSE:
            # Log the list of suitable stocks and their mean price
            logger.info("Suitable stocks:")
            for stock_name, mean_p, _, _ in suitable_stocks:
                logger.info(f"found {stock_name} for mean price {mean_p}")
            logger.info("=======================")

        # Step 4: Allocate investment amount among selected stocks
        portfolio = generate_portfolio(stock_prices=suitable_stocks, total_budget=amount)

        # Step 5: Generate report or output for user
        logger.info("Portfolio recommendation:")
        price_sum = 0
        for stock_name, num_shares, mean_price_at_purchase_time, current_price_val in portfolio:
            if num_shares > 0:
                price_sum += num_shares * mean_price_at_purchase_time
                logger.info(f"Buy {num_shares} shares of {stock_name}. "
                      f"Current price: {current_price_val:.2f} | "
                      f"Mean {PERIOD} price (used for allocation): {mean_price_at_purchase_time:.2f}")

        logger.info(f"Total estimated cost (based on mean prices at allocation): ${price_sum:,.2f}")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except InvestHelperError as e:
        logger.error(f"InvestHelper error: {e}", exc_info=True)
    except (ValueError, TypeError, pd.errors.EmptyDataError) as e:
        logger.error(f"Data processing error: {e}", exc_info=True)
