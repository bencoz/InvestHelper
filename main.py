import yfinance as yf

from constants import dividend_stocks, growth_stocks, index_funds
from io_utils import query_yes_no
from stock_utils import generate_portfolio

VERBOSE = True

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

PERIOD = '1y'

# Step 3: Scan suitable stocks for mean price
stocks = yf.Tickers(optional_stocks)
stocks_data = stocks.history(period=PERIOD)['Close']
stocks_current_prices = stocks_data.iloc[-1].tolist()
stocks_mean_prices = stocks_data.mean(axis=0).tolist()
stocks_prices_names = list(stocks_data.columns)

suitable_stocks = [(stock, mean_price, current_price, current_price - mean_price) for stock, mean_price, current_price
                   in
                   zip(stocks_prices_names, stocks_mean_prices, stocks_current_prices)]
suitable_stocks = sorted(suitable_stocks, key=lambda x: x[3])

if VERBOSE:
    # Print the list of suitable stocks and their mean price
    print("Suitable stocks:")
    for idx, data in enumerate(suitable_stocks):
        stock, mean_price, curr_price, diff_in_price = data
        stock_category = "dividend" if stock in dividend_stocks else "growth" if stock in growth_stocks else "index"
        print(f"{idx+1}: {stock} for {curr_price:.3f} ({stock_category})| (mean is: {mean_price:.3f} so diff is: {diff_in_price:.3f}]")
    print("=======================")

# Step 4.1: Ask user if the wants to invest in these stock in a percentage or not if yes ask for percentage
percentage = None
if query_yes_no("Do you want to select the investment percentage in these stocks? "):
    while True:
        try:
            percentage = input("Enter the percentage of investment in each stock separated by space: ")
            percentage = [float(x) for x in percentage.split()]
            assert len(percentage) == len(suitable_stocks)
            assert sum(percentage) == 1
        except Exception as e:
            print(e)
            continue
        else:
            break
else:
    if query_yes_no("Do you want to uniformly investment in these stocks? "):
        percentage = [1 / len(suitable_stocks) for _ in suitable_stocks]
    else:
        print("OK generating portfolio randomly based on the best diff from mean price")

# Step 4.2: Allocate investment amount among selected stocks
portfolio = generate_portfolio(stock_prices=suitable_stocks, total_budget=amount, percentage=percentage)

# Step 5: Generate report or output for user
print("portfolio:")
price_sum = 0
for stock, num, mean_price, curr_price in portfolio:
    if num > 0:
        price_sum += num * mean_price
        print(f"buy {num} {stock} stocks. current price: {curr_price} | mean {PERIOD} price: {mean_price} ")

print(f"for a total of {price_sum}")
