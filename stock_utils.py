import random
import yfinance as yf
import numpy as np
import math
import pandas as pd

pd.set_option('mode.chained_assignment', None)


def get_stock_data(stock, startdate, enddate, period, interval):
    yf.pdr_override()
    df = yf.download(tickers=stock, start=startdate, end=enddate, interval=interval, period=period)
    df.reset_index(inplace=True)
    df['date'] = df['Date'].dt.date

    return df


def ma_strategy(df, short_MA, long_MA):
    df['long_MA'] = df['Close'].rolling(int(long_MA)).mean()
    df['short_MA'] = df['Close'].rolling(int(short_MA)).mean()
    df['crosszero'] = np.where(df['short_MA'] < df['long_MA'], 1.0, 0.0)
    df['position'] = df['crosszero'].diff()
    df['position'].iloc[-1] = -1
    for i, row in df.iterrows():
        if df.loc[i, 'position'] == 1:
            buy_price = round(df.loc[i, 'Close'], 2)
            df.loc[i, 'buy'] = buy_price
        if df.loc[i, 'position'] == -1:
            sell_price = round(df.loc[i, 'Close'], 2)
            df.loc[i, 'sell'] = sell_price
    return df


def buy_sell_signals(df, stock, start_date, end_date):
    totalprofit = 0
    print('Stock: {}'.format(stock))
    print('Period: {} - {}'.format(start_date, end_date))
    print('-' * 57)
    print('{:^7}{:^10}{:^15}{:^10}{:^15}'.format('S/N', 'Buy Date', 'Buy Price($)', 'Sell Date', 'Sell Price($)'))
    print('-' * 57)

    for i, row in df.iterrows():
        if df.loc[i, 'position'] == 1:
            buy_price = round(df.loc[i, 'buy'], 2)
            buydate = df.loc[i, 'Date']
        if df.loc[i, 'position'] == -1:
            sell_price = round(df.loc[i, 'sell'], 2)
            selldate = df.loc[i, 'Date']
            profit = sell_price - buy_price
            profit = round(profit, 2)
            totalprofit = totalprofit + profit
            totalprofit = round(totalprofit, 2)
            print('{:^7}{}{:^15}{}{:^15}'.format(i, buydate, buy_price, selldate, sell_price))

    return df


def backtest(df, stock, startdate, enddate, initial_wealth):
    # assumptions:
    initial_wealth = int(initial_wealth)
    profitloss = 0
    position = 0
    total_profit = 0
    qty = 0
    balance = initial_wealth
    buy_p = 0  # per share
    total_buy_p = 0
    total_sell_p = 0
    MA_wealth = initial_wealth  # moving average wealth
    LT_wealth = initial_wealth  # long-term wealth
    inital_sell = 0
    df['position'].iloc[-1] = -1

    print('Stock: {}'.format(stock))
    print('Period: {} - {}'.format(startdate, enddate))
    print('Initial Wealth: {}'.format(initial_wealth))
    print('-' * 100)
    print('{:^7}{:^15}{:^10}{:^15}{:^20}{:^20}{:^10}{:^20}{:^20}{:^20}{:^20}'.format('Sr. No', 'Buy Date',
                                                                                     'Buy Price($)', 'Sell Date',
                                                                                     'Sell Price($)',
                                                                                     'Investment($)', 'Qty',
                                                                                     'total_buy_p', 'total_sell_p',
                                                                                     'profitloss', 'MA_wealth'))

    print('-' * 100)
    for i, row in df.iterrows():
        if position == 0:
            if df.loc[i, 'position'] == 1:
                buy_p = round(df.loc[i, 'Close'], 2)
                buy_d = df.loc[i, 'Date']
                balance = balance + total_sell_p
                qty = balance / buy_p
                qty = math.trunc(qty)
                total_buy_p = round(buy_p * qty, 2)
                balance = balance - total_buy_p
                position = 1
            else:
                price = df.loc[i, 'Close']
                if qty == 0 and MA_wealth == initial_wealth:
                    df.loc[i, 'MA_wealth'] = balance
                elif qty != 0 and MA_wealth != initial_wealth:
                    MA_wealth = sell_balance
                    df.loc[i, 'MA_wealth'] = MA_wealth
        elif position == 1:
            if df.loc[i, 'position'] == -1:
                sell_p = round(df.loc[i, 'Close'], 2)
                sell_d = df.loc[i, 'Date']

                total_sell_p = round(sell_p * qty, 2)
                profitloss = round(total_sell_p - total_buy_p, 2)
                total_profit = round(total_profit + profitloss, 2)
                sell_balance = round(balance + total_profit, 2)
                MA_wealth = round(balance + total_sell_p, 2)
                balance = round(balance, 2)

                print('{:^7}{}{:^15}{}{:^15}{:^15}{:^15}{:^20}{:^20}{:^10}{:^10}'.format(i, buy_d, buy_p, sell_d,
                                                                                         sell_p, MA_wealth, qty,
                                                                                         total_buy_p, total_sell_p,
                                                                                         profitloss, MA_wealth))

                sell_balance = balance + total_sell_p
                position = 0
            else:
                price = df.loc[i, 'Close']
                stockprice = price * qty
                MA_wealth = balance + stockprice
                df.loc[i, 'MA_wealth'] = MA_wealth
                # print(MA_wealth)

        # long-term strategy
    first_date = df['Date'].iloc[0]
    initial_price = df['Close'].iloc[0]
    qty = LT_wealth / initial_price

    for i, row in df.iterrows():
        df.loc[i, 'LT_wealth'] = df.loc[i, 'Close'] * qty

    last_date = df['Date'].iloc[-1]
    final_price = df['Close'].iloc[-1]

    LT_buy_p = initial_price * qty
    LT_sell_p = final_price * qty
    LT_profitloss = LT_sell_p - initial_wealth
    LT_wealth = initial_wealth + LT_profitloss
    MA_profitloss = MA_wealth - initial_wealth
    MA_profitloss = round(MA_profitloss, 2)
    LT_profitloss = round(LT_profitloss, 2)

    print('-' * 100)
    print('Short MA Profit/Loss: ${:,}, Long MA Profit/Loss: ${:,}'.format(MA_profitloss, LT_profitloss))
    print('')
    print('Short MA Final Wealth: ${:,.2f}, Long MA Final Wealth: ${:,.2f}'.format(MA_wealth, LT_wealth))
    print('-' * 100)

    return df


def RSI(df):
    change = df["Close"].diff()
    change.dropna(inplace=True)
    # Create two copies of the Closing price Series
    change_up = change.copy()
    change_down = change.copy()

    #
    change_up[change_up < 0] = 0
    change_down[change_down > 0] = 0

    # Verify that we did not make any mistakes
    change.equals(change_up + change_down)

    # Calculate the rolling average of average up and average down
    avg_up = change_up.rolling(14).mean()
    avg_down = change_down.rolling(14).mean().abs()
    rsi = 100 * avg_up / (avg_up + avg_down)
    return df, rsi


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
        for stock, mean_price, curr_price in stock_prices:
            # Calculate the number of shares that can be purchased with the budget for this stock
            shares_to_buy = stock_budget // mean_price
            # Calculate the total cost of the shares to buy
            cost = shares_to_buy * mean_price
            # Subtract the cost from the remaining budget
            budget -= cost
            # Add the stock and number of shares to the portfolio
            portfolio.append((stock, shares_to_buy, mean_price, curr_price))
    else:
        # TODO:: If you want to buy based on good price sort based on the diff between mean price and current
        stock_prices = sorted(stock_prices, key=lambda x: x[3])
        # Iterate through the list of stock prices and add stocks to the portfolio
        for stock, mean_price, curr_price, _diff in stock_prices:
            if math.isnan(_diff):
                continue
            # Calculate the maximum number of shares of this stock that can be purchased within the remaining budget
            max_shares = budget // mean_price
            # Choose a random number of shares to buy, between 0 and the maximum number of shares
            shares_to_buy = random.randint(0, max_shares)
            # Calculate the total cost of the shares to buy
            cost = shares_to_buy * mean_price
            # Subtract the cost from the remaining budget
            budget -= cost
            # Add the stock and number of shares to the portfolio
            portfolio.append((stock, shares_to_buy, mean_price, curr_price))

    return portfolio
