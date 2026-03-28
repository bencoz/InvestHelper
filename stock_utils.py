import random
import yfinance as yf
import numpy as np
import math
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime, date # Ensure datetime and date are imported
from cached_stock_data import get_stock_data_cached, get_current_price_cached, get_stock_sector_cached
from parallel_processing import fetch_multiple_stocks_parallel
import logging

logger = logging.getLogger(__name__)

pd.set_option('mode.chained_assignment', None)


def get_stock_data(stock: str, startdate: Optional[str], enddate: Optional[str], period_str: Optional[str], interval_str: str) -> pd.DataFrame:
    # yf.pdr_override() # Removed as requested
    
    # Use cached version instead of direct yfinance call
    df = get_stock_data_cached(stock, startdate, enddate, period_str, interval_str)
    
    if df.empty:
        return pd.DataFrame()

    df.reset_index(inplace=True)

    # Logic to find and rename date column
    date_col_found = False
    if 'Datetime' in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)
        date_col_found = True
    elif 'Date' in df.columns: # Already named 'Date'
        date_col_found = True
    elif 'index' in df.columns:
        # Check if the 'index' column actually contains date-like information
        if not df['index'].empty and isinstance(df['index'].iloc[0], (datetime, pd.Timestamp, date)):
            df.rename(columns={'index': 'Date'}, inplace=True)
            date_col_found = True
        # Add a check for string dates that might be in 'index' if yf changes format (less common)
        elif not df['index'].empty and isinstance(df['index'].iloc[0], str):
            try:
                pd.to_datetime(df['index'].iloc[0]) # Try converting first element
                df.rename(columns={'index': 'Date'}, inplace=True)
                date_col_found = True
            except (ValueError, TypeError):
                pass # Not a convertible date string

    if not date_col_found:
        # If no recognizable date column is found after checking common names
        return pd.DataFrame() # Return empty DataFrame

    # Ensure 'Date' column is datetime type
    try:
        df['Date'] = pd.to_datetime(df['Date'])
    except (ValueError, TypeError):
        # If conversion fails (e.g., column was misidentified as 'Date' but isn't convertible)
        return pd.DataFrame()

    # Create lowercase 'date' column with just the date part
    # This assumes 'Date' (capitalized) now correctly refers to the datetime objects.
    df['date'] = df['Date'].dt.date
    
    # Explicitly check for 'Close' column existence (optional here, as app.py might catch it)
    # if 'Close' not in df.columns:
    #     return pd.DataFrame() # Or raise an error

    return df


def ma_strategy(df: pd.DataFrame, short_MA: int, long_MA: int) -> pd.DataFrame:
    df['long_MA'] = df['Close'].rolling(int(long_MA)).mean()
    df['short_MA'] = df['Close'].rolling(int(short_MA)).mean()
    df['crosszero'] = np.where(df['short_MA'] < df['long_MA'], 1.0, 0.0)
    df['position'] = df['crosszero'].diff()
    df.loc[df.index[-1], 'position'] = -1
    for i, row in df.iterrows():
        if df.loc[i, 'position'] == 1:
            buy_price = round(df.loc[i, 'Close'], 2)
            df.loc[i, 'buy'] = buy_price
        if df.loc[i, 'position'] == -1:
            sell_price = round(df.loc[i, 'Close'], 2)
            df.loc[i, 'sell'] = sell_price
    return df


def buy_sell_signals(df: pd.DataFrame, stock: str, start_date: str, end_date: str) -> pd.DataFrame:
    totalprofit = 0
    # print('Stock: {}'.format(stock))
    # print('Period: {} - {}'.format(start_date, end_date))
    # print('-' * 57)
    # print('{:^7}{:^10}{:^15}{:^10}{:^15}'.format('S/N', 'Buy Date', 'Buy Price($)', 'Sell Date', 'Sell Price($)'))
    # print('-' * 57)

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
            # print('{:^7}{}{:^15}{}{:^15}'.format(i, buydate, buy_price, selldate, sell_price))

    return df


def backtest(df: pd.DataFrame, stock: str, startdate: str, enddate: str, initial_wealth: str) -> pd.DataFrame:
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
    df.loc[df.index[-1], 'position'] = -1


    # print('Stock: {}'.format(stock))
    # print('Period: {} - {}'.format(startdate, enddate))
    # print('Initial Wealth: {}'.format(initial_wealth))
    # print('-' * 100)
    # print('{:^7}{:^15}{:^10}{:^15}{:^20}{:^20}{:^10}{:^20}{:^20}{:^20}{:^20}'.format('Sr. No', 'Buy Date',
                                                                                     # 'Buy Price($)', 'Sell Date',
                                                                                     # 'Sell Price($)',
                                                                                     # 'Investment($)', 'Qty',
                                                                                     # 'total_buy_p', 'total_sell_p',
                                                                                     # 'profitloss', 'MA_wealth'))

    # print('-' * 100)
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

                # print('{:^7}{}{:^15}{}{:^15}{:^15}{:^15}{:^20}{:^20}{:^10}{:^10}'.format(i, buy_d, buy_p, sell_d,
                                                                                         # sell_p, MA_wealth, qty,
                                                                                         # total_buy_p, total_sell_p,
                                                                                         # profitloss, MA_wealth))

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

    # print('-' * 100)
    # print('Short MA Profit/Loss: ${:,}, Long MA Profit/Loss: ${:,}'.format(MA_profitloss, LT_profitloss))
    # print('')
    # print('Short MA Final Wealth: ${:,.2f}, Long MA Final Wealth: ${:,.2f}'.format(MA_wealth, LT_wealth))
    # print('-' * 100)

    return df


def RSI(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
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

    # Map numeric index to DatetimeIndex so charts show dates on x-axis
    if 'Date' in df.columns:
        rsi.index = pd.to_datetime(df.loc[rsi.index, 'Date'].values)

    return df, rsi


def generate_portfolio(stock_prices: List[Tuple], total_budget: float, option: str = 'random') -> List[Tuple]:
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


def get_stock_sector(ticker_symbol: str):
    """
    Fetches the sector for a given stock ticker symbol.
    Args:
        ticker_symbol (str): The stock ticker symbol.
    Returns:
        str: The sector of the stock, or "Unknown" if not found or an error occurs.
    """
    return get_stock_sector_cached(ticker_symbol)


def calculate_diversification_score(portfolio_df: pd.DataFrame):
    """
    Calculates the diversification score of a given portfolio based on sector concentration.
    Args:
        portfolio_df (pd.DataFrame): DataFrame with 'symbol' and 'Qty' columns.
    Returns:
        tuple: (float, pd.DataFrame) - The diversification score (0-100) and the processed DataFrame.
               Returns (0.0, original_portfolio_df) if calculation is not possible early.
               Returns (None, original_portfolio_df) if critical data fetching fails.
    """
    if not isinstance(portfolio_df, pd.DataFrame) or portfolio_df.empty:
        return 0.0, portfolio_df # Return original df
    if not all(col in portfolio_df.columns for col in ['symbol', 'Qty']):
        return 0.0, portfolio_df # Return original df

    # Make a copy to avoid modifying the original DataFrame
    df = portfolio_df.copy()
    # Initialize columns that might not get populated if errors occur
    df['sector'] = "Unknown"
    df['current_price'] = np.nan
    df['market_value'] = np.nan

    # Fetch Sector Information in Parallel
    logger.info(f"Fetching sector data for {len(df)} stocks in parallel")
    symbols = df['symbol'].tolist()
    sectors = fetch_multiple_stocks_parallel(symbols, get_stock_sector_cached, max_workers=10)
    df['sector'] = sectors
    # Fill None/Unknown sectors
    df['sector'].fillna("Unknown", inplace=True)

    # Fetch Current Prices in Parallel
    logger.info(f"Fetching current prices for {len(df)} stocks in parallel")
    prices = fetch_multiple_stocks_parallel(symbols, get_current_price_cached, max_workers=10)
    df['current_price'] = prices
    
    # Drop rows where current price could not be fetched
    df.dropna(subset=['current_price'], inplace=True)
    if df.empty: # If all price fetches failed
        return 0.0, portfolio_df # Return original df, score 0

    df['market_value'] = df['Qty'] * df['current_price']
    
    # Re-check after market_value calculation, as Qty could be 0
    df.dropna(subset=['market_value'], inplace=True) # if Qty is 0 or current_price was NaN
    if df.empty:
        return 0.0, portfolio_df


    # Calculate Total Portfolio Value
    total_portfolio_value = df['market_value'].sum()
    if total_portfolio_value == 0:
        return 0.0, df # Return processed df but score 0

    # Calculate Sector Weights
    sector_market_values = df.groupby('sector')['market_value'].sum()
    sector_weights = sector_market_values / total_portfolio_value

    # Calculate HHI Diversification Score
    hhi = (sector_weights ** 2).sum()
    diversification_score = (1 - hhi) * 100
    
    # Ensure score is between 0 and 100
    diversification_score = max(0, min(diversification_score, 100))

    return diversification_score, df


def suggest_rebalancing_actions(portfolio_df: pd.DataFrame, diversification_score: float):
    """
    Suggests rebalancing actions based on portfolio composition and diversification score.
    Args:
        portfolio_df (pd.DataFrame): DataFrame with 'symbol', 'Qty', 'sector', 'market_value'.
                                     Assumed to be processed by calculate_diversification_score.
        diversification_score (float): The current diversification score of the portfolio.
    Returns:
        list: A list of string-based suggestions.
    """
    suggestions = []
    
    # Define Thresholds
    DIVERSIFICATION_THRESHOLD_LOW = 60.0
    DIVERSIFICATION_THRESHOLD_GOOD = 80.0
    SECTOR_CONCENTRATION_THRESHOLD = 35.0  # e.g., 35%
    LOW_STOCK_COUNT_THRESHOLD = 5
    
    required_cols = ['symbol', 'Qty', 'sector', 'market_value']
    if not isinstance(portfolio_df, pd.DataFrame) or portfolio_df.empty or \
       not all(col in portfolio_df.columns for col in required_cols):
        return ["Portfolio data is insufficient for suggestions. Ensure it has 'symbol', 'Qty', 'sector', and 'market_value' columns."]

    if diversification_score >= DIVERSIFICATION_THRESHOLD_GOOD:
        suggestions.append("Your portfolio is well-diversified based on sector concentration. No immediate rebalancing actions suggested.")
    else:
        total_portfolio_value = portfolio_df['market_value'].sum()
        if total_portfolio_value == 0:
            return ["Cannot generate suggestions: total portfolio value is zero."]

        sector_allocations = portfolio_df.groupby('sector')['market_value'].sum()
        sector_weights = (sector_allocations / total_portfolio_value) * 100  # as percentage
        
        # Sort sectors by weight for easier identification of concentration
        sorted_sectors = sector_weights.sort_values(ascending=False)

        # Check for low stock count
        if len(portfolio_df['symbol'].unique()) < LOW_STOCK_COUNT_THRESHOLD:
            suggestions.append(f"Your portfolio has {len(portfolio_df['symbol'].unique())} unique positions. Consider adding more stocks to improve diversification across different companies.")

        # Check for over-concentration
        over_concentrated_sectors = []
        for sector, weight in sorted_sectors.items():
            if weight > SECTOR_CONCENTRATION_THRESHOLD:
                suggestions.append(f"Consider reducing exposure to the '{sector}' sector, which currently makes up {weight:.1f}% of your portfolio.")
                over_concentrated_sectors.append(sector)
        
        # Suggest diversifying if score is low, even if no single sector is hugely over-concentrated
        if diversification_score < DIVERSIFICATION_THRESHOLD_LOW:
            if not over_concentrated_sectors and len(sorted_sectors) < 3 and len(sorted_sectors) > 0 : # Few sectors but none above threshold
                 suggestions.append("Your portfolio is concentrated in a small number of sectors.")

            # Suggest adding exposure to under-represented or new sectors
            potential_new_sectors = ["Technology", "Healthcare", "Financials", "Consumer Discretionary", "Industrials", "Energy", "Utilities", "Real Estate", "Materials", "Consumer Staples"]
            # Filter out sectors already present or 'Unknown'
            current_sectors = [s.lower() for s in sector_weights.index.tolist() if s != "Unknown"]
            new_sector_suggestions = [s for s in potential_new_sectors if s.lower() not in current_sectors]
            
            if new_sector_suggestions:
                suggestions.append(f"Consider diversifying by adding investments in sectors like {', '.join(new_sector_suggestions[:3])}.")
            elif not over_concentrated_sectors : # If no specific sector to reduce and no obvious new ones to add from the list.
                 suggestions.append("Review your portfolio to ensure it's spread across a healthy number of diverse sectors.")


        if not suggestions: # If score is between LOW and GOOD, and no specific issues found
            suggestions.append("Your portfolio diversification is moderate. Review sector allocations for potential improvements to achieve a higher diversification score.")

    suggestions.append("Always ensure your portfolio aligns with your investment goals and risk tolerance.")
    return suggestions
