import json
import logging

logger = logging.getLogger(__name__)

# Load stock lists from config.json
try:
    with open("config.json", 'r') as f:
        config_data = json.load(f)
except FileNotFoundError:
    logger.error("config.json not found. Please ensure the file exists in the root directory.")
    # Provide default empty lists or raise an error if configuration is critical
    dividend_stocks = []
    growth_stocks = []
    index_funds = []
except json.JSONDecodeError:
    logger.error("Could not decode config.json. Please ensure it is valid JSON.")
    # Provide default empty lists or raise an error
    dividend_stocks = []
    growth_stocks = []
    index_funds = []
else:
    dividend_stocks = config_data.get("dividend_stocks", [])
    growth_stocks = config_data.get("growth_stocks", [])
    index_funds = config_data.get("index_funds", [])

# The following is for potential future use, if we want to validate the loaded lists.
# For now, we just load them or use empty lists on error.
if not all(isinstance(stock, str) for stock_list in [dividend_stocks, growth_stocks, index_funds] for stock in stock_list):
    # This basic check ensures all items in the lists are strings.
    # More complex validation could be added here (e.g., checking for empty strings, specific formats).
    logger.warning("Some stock tickers loaded from config.json may not be strings. This could lead to errors.")

# Example of how these lists would be used in main.py (no changes needed in main.py):
# from constants import dividend_stocks, growth_stocks, index_funds
# ... rest of main.py logic ...

from typing import Final

# Technical Analysis Parameters
MA_SHORT_PERIOD: Final[int] = 50
MA_LONG_PERIOD: Final[int] = 200
RSI_PERIOD: Final[int] = 14
INITIAL_WEALTH: Final[float] = 1000.0

# Portfolio Analysis Thresholds
DIVERSIFICATION_THRESHOLD_LOW: Final[float] = 60.0
DIVERSIFICATION_THRESHOLD_GOOD: Final[float] = 80.0
SECTOR_CONCENTRATION_THRESHOLD: Final[float] = 35.0
LOW_STOCK_COUNT_THRESHOLD: Final[int] = 5

# Data Fetching
DEFAULT_PERIOD: Final[str] = '2y'
DEFAULT_INTERVAL: Final[str] = '1d'
PRICE_FETCH_TIMEOUT: Final[int] = 30  # seconds
