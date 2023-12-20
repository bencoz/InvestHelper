from datetime import datetime

import pandas as pd

from io_utils import print_graph, print_rsi_graph
from stock_utils import get_stock_data, ma_strategy, buy_sell_signals, backtest, RSI

long_MA = 200
short_MA = 50
initial_wealth = '1000'
while True:
    try:
        stock = input("Enter a stock ticker: ")
    except Exception as e:
        print(e)
        continue
    else:
        break
while True:
    try:
        date_entry = input('Enter a date in YYYY-MM-DD format')
        year, month, day = map(int, date_entry.split('-'))
        start_date = datetime(year=year, month=month, day=day).date()
    except Exception as e:
        print(e)
        continue
    else:
        break

period = '60d'
end_date = datetime.today().strftime('%Y-%m-%d')
interval = '1d'
totalprofit = 0

df = get_stock_data(stock, start_date, end_date, period, interval)
df = ma_strategy(df, long_MA, short_MA)
df = buy_sell_signals(df, stock, start_date, end_date)
df = backtest(df, stock, start_date, end_date, initial_wealth)
print_graph(df, stock)

df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')
df, rsi = RSI(df)
print_rsi_graph(df, rsi)
