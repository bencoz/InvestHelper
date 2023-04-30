## Stock Portfolio Generator

This script generates a random stock portfolio based on user input. The user is prompted to input the amount of money they want to invest, and whether they want to invest in high dividend stocks, growth stocks, or index funds.

The script uses the `yfinance` library to fetch the stock prices of suitable stocks based on the user's selection. The mean price of these stocks is then used to allocate the user's investment amount among them.

### Usage

1. Install the required dependencies by running `pip install -r requirements.txt`
2. Run the script by running `python main.py`
3. Enter the amount of money you want to invest when prompted
4. Answer the prompts for investing in high dividend stocks, growth stocks, and index funds with 'yes' or 'no'
5. The script will generate a portfolio of stocks with their prices and the number of shares to buy

### Parameters
- `dividend_stocks`: List of high dividend stocks to choose from
- `growth_stocks`: List of growth stocks to choose from
- `index_funds`: List of index funds to choose from
