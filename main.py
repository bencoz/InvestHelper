import yfinance as yf

from constants import dividend_stocks, growth_stocks, index_funds
from io_utils import query_yes_no
from stock_utils import generate_portfolio

VERBOSE = False

# Step 1: Get user input
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

# Step 2: Add stock data based on user-selected options
optional_stocks = []
if dividend_investing:
    optional_stocks.extend(dividend_stocks)

if growth_investing:
    optional_stocks.extend(growth_stocks)

if index_investing:
    optional_stocks.extend(index_funds)

PERIOD = '2y'

# Step 3: Scan suitable stocks for mean price
stocks = yf.Tickers(optional_stocks)
stocks_data = stocks.history(period=PERIOD)['Close']
stocks_current_prices = stocks_data.iloc[-1].tolist()
stocks_mean_prices = stocks_data.mean(axis=0).tolist()
stocks_prices_names = list(stocks_data.columns)

suitable_stocks = [(stock, mean_price, current_price, current_price - mean_price) for stock, mean_price, current_price
                   in
                   zip(stocks_prices_names, stocks_mean_prices, stocks_current_prices)]

if VERBOSE:
    # Print the list of suitable stocks and their mean price
    print("Suitable stocks:")
    for stock, price in suitable_stocks:
        print(f"found {stock} for {price}")
    print("=======================")

# Step 4: Allocate investment amount among selected stocks
portfolio = generate_portfolio(stock_prices=suitable_stocks, total_budget=amount)

# Step 5: Generate report or output for user
print("portfolio:")
price_sum = 0
for stock, num, mean_price, curr_price in portfolio:
    if num > 0:
        price_sum += num * mean_price
        print(f"buy {num} {stock} stocks. current price: {curr_price} | mean {PERIOD} price: {mean_price} ")

print(f"for a total of {price_sum}")
