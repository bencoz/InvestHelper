# Stock Portfolio Generator and Researcher

## Overview

This project provides tools for generating investment portfolios and researching individual stocks. Users can customize stock selections through a configuration file and utilize scripts for portfolio creation based on investment preferences and for detailed stock analysis using moving averages and RSI.

## Features

*   **Portfolio Generation**: Creates a diversified stock portfolio based on user-defined investment amounts and preferences for dividend stocks, growth stocks, or index funds.
*   **Stock Research**: Performs technical analysis on individual stocks, including moving average strategies and Relative Strength Index (RSI) calculations, and visualizes results.
*   **Customizable Stock Lists**: Stock choices for portfolio generation can be easily modified by editing a JSON configuration file.
*   **Modular Codebase**: The code is organized into modules for clarity and maintainability.

## Setup

1.  Ensure you have Python 3.x installed.
2.  Clone the repository (if you haven't already).
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Portfolio Generation (`main.py`)

This script generates a stock portfolio based on your investment amount and selected stock categories.

1.  Run the script:
    ```bash
    python main.py
    ```
2.  Enter the amount of money you want to invest when prompted.
3.  Answer the prompts for investing in high dividend stocks, growth stocks, and index funds with 'yes' (or 'y') or 'no' (or 'n').
4.  The script will output a suggested portfolio, including the number of shares to buy for each selected stock and total investment cost.

### Stock Research (`research_stock.py`)

This script allows you to perform a technical analysis for a specific stock.

1.  Run the script:
    ```bash
    python research_stock.py
    ```
2.  Enter the stock ticker (e.g., `AAPL`, `GOOG`) when prompted.
3.  Enter the start date for the analysis in `YYYY-MM-DD` format.
4.  The script will display graphs showing moving averages, buy/sell signals, strategy wealth simulation, and the RSI.

## Configuration (`config.json`)

The stock lists used by `main.py` for portfolio generation are managed in the `config.json` file located in the root directory. This allows you to customize the universe of stocks considered for investment without modifying the Python code.

The `config.json` file contains the following lists:

*   `"dividend_stocks"`: A list of stock tickers considered high-dividend.
*   `"growth_stocks"`: A list of stock tickers considered growth stocks.
*   `"index_funds"`: A list of tickers for index funds.

**To customize these lists:**

1.  Open `config.json` in a text editor.
2.  Modify the lists by adding or removing stock tickers (strings) as desired.
3.  Save the file. The changes will be reflected the next time you run `main.py`.

Example `config.json` structure:
```json
{
  "dividend_stocks": ["TICKER1", "TICKER2", ...],
  "growth_stocks": ["TICKER3", "TICKER4", ...],
  "index_funds": ["TICKER5", "TICKER6", ...]
}
```

## Code Structure

The codebase has been refactored for improved modularity and organization. Key scripts like `main.py` (portfolio generation) and `research_stock.py` (stock analysis) now delegate tasks to helper functions within their respective files or to utility modules like `stock_utils.py` and `io_utils.py`. This separation of concerns makes the code easier to understand, maintain, and extend.

## Testing

Unit tests are included to ensure the reliability of key functions. To run the tests:

1.  Navigate to the root directory of the project in your terminal.
2.  Run the following command:
    ```bash
    python -m unittest discover tests
    ```
    This will automatically discover and run all tests within the `tests` directory.

---

*Note: Investing in the stock market involves risk. This tool is for informational and educational purposes only and should not be considered financial advice.*
