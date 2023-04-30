import sys
import random
import yfinance as yf

VERBOSE = False
dividend_stocks = ['VYM', 'SDY', 'VIG', 'T', 'KO', 'JNJ', 'QCOM', 'TSM', 'BBY', 'HD', 'TXN', 'CNQ', 'AVGO', 'PG', 'KMI']
growth_stocks = ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'PANW', 'DIS', 'MA', 'AMD', 'ATVI']
index_funds = ['SPY', 'QQQ', 'DIA', 'VTI', 'IWM', 'EWJ', 'VGK', 'EEM', 'EFA']


def query_yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


def generate_portfolio(stock_prices, total_budget, option='random'):
    # Shuffle the list of stock prices to randomize the selection
    random.shuffle(stock_prices)
    portfolio = []
    budget = total_budget
    num_stocks = len(stock_prices)

    if option == 'equal':
        # Calculate the budget for each stock
        stock_budget = budget // num_stocks
        # Allocate an equal budget to each stock
        for stock, price in stock_prices:
            # Calculate the number of shares that can be purchased with the budget for this stock
            shares_to_buy = stock_budget // price
            # Calculate the total cost of the shares to buy
            cost = shares_to_buy * price
            # Subtract the cost from the remaining budget
            budget -= cost
            # Add the stock and number of shares to the portfolio
            portfolio.append((stock, shares_to_buy, price))
    else:
        # Iterate through the list of stock prices and add stocks to the portfolio
        for stock, price in stock_prices:
            # Calculate the maximum number of shares of this stock that can be purchased within the remaining budget
            max_shares = budget // price
            # Choose a random number of shares to buy, between 0 and the maximum number of shares
            shares_to_buy = random.randint(0, max_shares)
            # Calculate the total cost of the shares to buy
            cost = shares_to_buy * price
            # Subtract the cost from the remaining budget
            budget -= cost
            # Add the stock and number of shares to the portfolio
            portfolio.append((stock, shares_to_buy, price))

    return portfolio


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

# Step 3: Scan suitable stocks for mean price
stocks = yf.Tickers(optional_stocks)
stocks_data = stocks.history(period='14d')['Close']
stocks_prices = stocks_data.mean(axis=0).tolist()
stocks_prices_names = list(stocks_data.columns)

suitable_stocks = [(stock, price) for stock, price in
                        zip(stocks_prices_names, stocks_prices)]

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
for stock, num, price in portfolio:
    if num > 0:
        price_sum += num * price
        print(f"buy {num} {stock} stocks for {price}")

print(f"for a total of {price_sum}")
