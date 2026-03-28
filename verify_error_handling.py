import logging
from logging_config import setup_logging
from cached_stock_data import get_stock_data_cached, get_current_price_cached
from exceptions import DataFetchError

# Setup logging
logger = setup_logging()

def test_valid_fetch():
    logger.info("\nTesting valid fetch (AAPL)...")
    try:
        df = get_stock_data_cached("AAPL", "2023-01-01", "2023-01-10", None, "1d")
        if not df.empty:
            logger.info("Success: Fetched data for AAPL")
        else:
            logger.error("Failure: Returned empty dataframe for AAPL")
    except (DataFetchError, ValueError, TypeError) as e:
        logger.error(f"Failure: Unexpected exception: {e}")

def test_invalid_ticker():
    logger.info("\nTesting invalid ticker (INVALID_TICKER_XYZ)...")
    try:
        df = get_stock_data_cached("INVALID_TICKER_XYZ", "2023-01-01", "2023-01-10", None, "1d")
        if df.empty:
            logger.info("Success: Handled invalid ticker gracefully (returned empty df)")
        else:
            logger.warning("Warning: Somehow fetched data for invalid ticker?")
    except (DataFetchError, ValueError, TypeError) as e:
        logger.error(f"Failure: Unexpected exception: {e}")

def test_retry_logic():
    logger.info("\nTesting retry logic (simulated by checking logs manually)...")
    # This is hard to test automatically without mocking, but we can check if it runs without crashing
    try:
        price = get_current_price_cached("AAPL", use_cache=False)
        logger.info(f"Fetched price: {price}")
    except (DataFetchError, ValueError, TypeError) as e:
        logger.error(f"Failure: {e}")

if __name__ == "__main__":
    test_valid_fetch()
    test_invalid_ticker()
    test_retry_logic()
    logger.info("\nCheck logs/investhelper.log and logs/errors.log for details.")
