import yfinance as yf
import matplotlib.pyplot as plt

# Description: This script calculates the current dividends you're receiving from your portfolio,
# compares them to your annual dividend goal, and visualizes dividend yields.

annual_dividend_goal = 50000
my_stocks = [
    ('SPY', 10),
    ('GOOGL', 20),
    ('MSFT', 8),
    ('AAPL', 15),
    ('NVDA', 22),
    ('T', 100),
    ('QQQ', 4),
    ('V', 5),
    ('VYM', 5),
    ('CVX', 4),
    ('DIS', 4),
    ('BABA', 4),
    ('SNAP', 10),
    ('CNQ', 2),
    ('LCID', 20),
    ('KMI', 2),
    ('INTC', 2),
    ('NIO', 1)
]

# Step 1: Get the current dividends and stock prices using yfinance for each stock in my_stocks
stocks = [stock for stock, _ in my_stocks]
tickers = yf.Tickers(stocks)
dividends = tickers.history(period='1y')['Dividends']
prices = tickers.history(period='1d')['Close'].iloc[-1]  # Get the latest closing prices

yearly_dividend_per_stock = {}
dividend_yields = {}
total_dividend = 0

for stock, shares in my_stocks:
    stock_dividends = dividends[stock]
    yearly_dividend = stock_dividends.sum() * shares if not stock_dividends.empty else 0
    yearly_dividend_per_stock[stock] = yearly_dividend
    total_dividend += yearly_dividend

    # Calculate dividend yield
    stock_price = prices.get(stock, 0)
    if stock_price > 0:
        dividend_yield = (yearly_dividend / stock_price / shares) * 100
        dividend_yields[stock] = dividend_yield

# Filter out stocks that don't pay dividends
dividend_paying_stocks = {stock: dividend for stock, dividend in yearly_dividend_per_stock.items() if dividend > 0}

# Step 2: Calculate and print the dividend goal comparison
print(f"Annual Dividend: ${total_dividend:.2f} / ${annual_dividend_goal:.2f}")
print(f"Monthly Dividend: ${total_dividend / 12:.2f} / ${annual_dividend_goal / 12:.2f}")
print(f"Daily Dividend: ${total_dividend / 365:.2f} / ${annual_dividend_goal / 365:.2f}")
print(f"Hourly Dividend: ${total_dividend / (365 * 24):.4f} / ${annual_dividend_goal / (365 * 24):.4f}")
print(f"{'=' * 50}")

# Step 3: Print statistics about the top 10 dividend-paying stocks
top_stocks = sorted(dividend_paying_stocks.items(), key=lambda x: x[1], reverse=True)[:10]
print("Top 10 Dividend-Paying Stocks:")
for stock, dividend in top_stocks:
    yield_info = f" (Yield: {dividend_yields[stock]:.2f}%)" if stock in dividend_yields else ""
    print(f"{stock}: ${dividend:.2f}{yield_info}")

# Step 4: Visualize dividend yields
plt.figure(figsize=(10, 6))
plt.bar(dividend_yields.keys(), dividend_yields.values(), color='skyblue')
plt.xlabel('Stocks')
plt.ylabel('Dividend Yield (%)')
plt.title('Dividend Yield of Dividend-Paying Stocks in Portfolio')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
