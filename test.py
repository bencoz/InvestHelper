# yfinance-0.2.18
import yfinance as yf

apple= yf.Ticker("aapl")

# show actions (dividends, splits)
print(apple.actions)

# show dividends
print(apple.dividends)

# show splits
print(apple.splits)

# + other methods etc.