import streamlit as st
import pandas as pd
from datetime import datetime, date # Ensure date is imported
import json # Added for saving ticker changes

# Import functions from existing project modules
from main import prepare_stock_selection, fetch_stock_data # get_user_investment_preferences removed as it's handled by UI
from stock_utils import generate_portfolio, get_stock_data, ma_strategy, buy_sell_signals, backtest, RSI
from io_utils import get_price_ma_and_wealth_plots, get_rsi_plot # Updated plotting functions
# Import for initial population
from constants import dividend_stocks as initial_dividend_stocks
from constants import growth_stocks as initial_growth_stocks
from constants import index_funds as initial_index_funds

st.set_page_config(layout="wide")

# Initialize session state for stock lists if they don't exist
if 'dividend_stocks' not in st.session_state:
    st.session_state.dividend_stocks = list(initial_dividend_stocks)
if 'growth_stocks' not in st.session_state:
    st.session_state.growth_stocks = list(initial_growth_stocks)
if 'index_funds' not in st.session_state:
    st.session_state.index_funds = list(initial_index_funds)

st.title("AI Stock Research Assistant")

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose the app mode",
                                ["Portfolio Generator", "Stock Analyzer"])

# --- Portfolio Generator Mode ---
if app_mode == "Portfolio Generator":
    st.header("Generate Your Stock Portfolio")

    amount = st.number_input("Enter amount of money ($) to invest:", min_value=0.01, value=1000.0, step=100.0, format="%.2f")
    
    st.subheader("Investment Preferences:")
    dividend_investing = st.checkbox("Invest in high dividend stocks?", True)
    growth_investing = st.checkbox("Invest in growth stocks?", True)
    index_investing = st.checkbox("Invest in index funds?", True)

    # PERIOD for stock data fetching
    PERIOD = "2y"

    if st.button("Generate Portfolio"):
        if not (dividend_investing or growth_investing or index_investing):
            st.warning("Please select at least one investment type.")
        else:
            with st.spinner("Generating portfolio..."):
                # 1. Prepare stock selection
                # Use stock lists from session state
                selected_tickers = prepare_stock_selection(
                    dividend_investing, growth_investing, index_investing,
                    st.session_state.dividend_stocks, 
                    st.session_state.growth_stocks, 
                    st.session_state.index_funds
                )

                if not selected_tickers:
                    st.warning("No stock categories selected, or no stocks found for the selected categories. Please check your selections and `config.json`.")
                else:
                    # DEBUG: st.write(f"Selected tickers: {', '.join(selected_tickers)}")
                    try:
                        # 2. Fetch stock data
                        stocks_data_for_portfolio = fetch_stock_data(selected_tickers, period=PERIOD)

                        if not stocks_data_for_portfolio:
                            st.error("Could not fetch data for the selected stocks. This could be due to: \n"
                                     "- Invalid tickers in `config.json`. \n"
                                     "- Network connectivity issues. \n"
                                     "- yfinance API service disruptions. \n"
                                     "Please verify your stock lists and try again later.")
                        else:
                            # 3. Generate portfolio
                            raw_portfolio = generate_portfolio(stock_prices=stocks_data_for_portfolio, total_budget=amount)

                            if not raw_portfolio:
                                st.info("No stocks could be allocated with the given budget and current stock prices. The portfolio is empty.")
                            else:
                                portfolio_df = pd.DataFrame(raw_portfolio, columns=["Stock", "Shares", "Mean Price (2y)", "Current Price"])
                                portfolio_df = portfolio_df[portfolio_df["Shares"] > 0]

                                if portfolio_df.empty:
                                    st.info("No stocks were allocated with enough budget to purchase at least one share, or all selected stocks were filtered out after generation.")
                                else:
                                    st.subheader("Generated Portfolio:")
                                    st.dataframe(portfolio_df.set_index("Stock"))
                                    
                                    total_investment_mean_price = (portfolio_df["Shares"] * portfolio_df["Mean Price (2y)"]).sum()
                                    st.metric(label=f"Total Portfolio Value (at {PERIOD} mean prices)", value=f"${total_investment_mean_price:,.2f}")
                                    
                                    total_investment_current_price = (portfolio_df["Shares"] * portfolio_df["Current Price"]).sum()
                                    st.metric(label="Total Portfolio Value (at current prices)", value=f"${total_investment_current_price:,.2f}")
                                    
                                    st.caption(f"Note: The 'random' allocation strategy prioritizes stocks with a larger positive difference between current and mean price. Results may vary if not all budget is used.")
                    except Exception as e:
                        st.error(f"An unexpected error occurred during portfolio generation: {e}")
                        st.error("Please check the console for more details if you are running this locally.")


# --- Stock Analyzer Mode ---
elif app_mode == "Stock Analyzer":
    st.header("Analyze Stock Performance")

    stock_ticker = st.text_input("Enter a stock ticker:", "AAPL").upper()
    # Use date type for start_date_input, then convert to datetime
    start_date_input = st.date_input("Select analysis start date:", date(2020, 1, 1)) 
    
    # Define constants for analysis
    LONG_MA_CONST = 200
    SHORT_MA_CONST = 50
    INITIAL_WEALTH_CONST_STR = '1000'
    # INTERVAL_CONST for yfinance call, period_str should be None if using start/end dates
    INTERVAL_CONST = '1d'

    if st.button("Analyze Stock"):
        if not stock_ticker:
            st.warning("Please enter a stock ticker.")
        else:
            with st.spinner(f"Analyzing {stock_ticker}..."):
                end_date_dt = datetime.today() 
                # Convert start_date_input (which is a date object) to a datetime object
                start_date_dt = datetime.combine(start_date_input, datetime.min.time())

                # 1. Get stock data
                df = get_stock_data(stock_ticker, 
                                    start_date_dt.strftime('%Y-%m-%d'), 
                                    end_date_dt.strftime('%Y-%m-%d'), 
                                    period_str=None,  # Use None if start/end dates are primary
                                    interval_str=INTERVAL_CONST)

                if df.empty:
                    st.error(f"Could not fetch data for {stock_ticker} from {start_date_input.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}. "
                             "This could be due to an invalid ticker, delisting, or no data available for the selected date range.")
                else:
                    try:
                        # 2. Apply MA strategy
                        df_ma = ma_strategy(df.copy(), SHORT_MA_CONST, LONG_MA_CONST)

                        # 3. Get buy/sell signals
                        df_signals = buy_sell_signals(df_ma.copy(), stock_ticker,
                                                      start_date_dt.strftime('%Y-%m-%d'),
                                                      end_date_dt.strftime('%Y-%m-%d'))
                        
                        # 4. Perform backtest
                        backtest_results_df = backtest(df_signals.copy(), stock_ticker,
                                                   start_date_dt.strftime('%Y-%m-%d'),
                                                   end_date_dt.strftime('%Y-%m-%d'),
                                                   INITIAL_WEALTH_CONST_STR)
                        
                        st.subheader(f"Analysis Results for {stock_ticker}")

                        # 5. Display charts
                        if not pd.api.types.is_datetime64_any_dtype(backtest_results_df['Date']):
                            backtest_results_df['Date'] = pd.to_datetime(backtest_results_df['Date'])

                        fig_price_ma, fig_wealth = get_price_ma_and_wealth_plots(backtest_results_df, stock_ticker)
                        st.pyplot(fig_price_ma)
                        st.pyplot(fig_wealth)

                        # 6. Calculate and display RSI
                        # df_with_rsi_col (from RSI function) should have 'Date' as a column and 'Close' prices.
                        # rsi_series is the calculated RSI data.
                        # io_utils.get_rsi_plot will handle setting the index from 'Date' column if necessary.
                        df_with_rsi_col, rsi_series = RSI(backtest_results_df.copy()) 
                        
                        fig_rsi = get_rsi_plot(df_with_rsi_col, rsi_series)
                        st.pyplot(fig_rsi)
                        
                        # 7. Display Backtest results metrics
                        # Check if necessary columns exist and have valid data (e.g., not all NaN, length > 0)
                        if ('MA_wealth' in backtest_results_df.columns and 
                            'LT_wealth' in backtest_results_df.columns and
                            not backtest_results_df['MA_wealth'].dropna().empty and 
                            not backtest_results_df['LT_wealth'].dropna().empty):
                            
                            final_ma_wealth = backtest_results_df['MA_wealth'].dropna().iloc[-1]
                            final_lt_wealth = backtest_results_df['LT_wealth'].dropna().iloc[-1]
                            initial_wealth_float = float(INITIAL_WEALTH_CONST_STR)
                            
                            total_profit_ma = final_ma_wealth - initial_wealth_float
                            total_profit_lt = final_lt_wealth - initial_wealth_float

                            st.subheader("Backtesting Summary")
                            col1, col2 = st.columns(2)
                            col1.metric("MA Strategy Final Wealth", f"${final_ma_wealth:,.2f}", f"{((final_ma_wealth-initial_wealth_float)/initial_wealth_float*100):.2f}% Return")
                            col2.metric("Buy & Hold Strategy Final Wealth", f"${final_lt_wealth:,.2f}", f"{((final_lt_wealth-initial_wealth_float)/initial_wealth_float*100):.2f}% Return")
                            col1.metric("MA Strategy Total Profit", f"${total_profit_ma:,.2f}")
                            col2.metric("Buy & Hold Strategy Total Profit", f"${total_profit_lt:,.2f}")
                        else:
                            st.warning("Could not extract complete backtesting wealth figures. This might happen if the analysis period is too short or data is unavailable.")
                    except Exception as e:
                        print(e)
                        st.error(f"An error occurred during the stock analysis for {stock_ticker}: {e}")
                        st.error("This could be due to insufficient data for the selected period (e.g., for Moving Averages), or an issue with the underlying calculations. Try a longer date range or a different stock.")
                        st.error("Please check the console for more details if you are running this locally.")


st.sidebar.info(
    "This app helps novice investors with stock research and portfolio generation."
)

# --- Manage Stock Tickers ---
st.sidebar.title("Manage Stock Tickers")

# --- Dividend Stocks ---
st.sidebar.subheader("Dividend Stocks")
# Use st.session_state.new_dividend_ticker directly in the logic
st.sidebar.text_input("Add Dividend Ticker", key="new_dividend_ticker")
if st.sidebar.button("Add", key="add_dividend_ticker_button"):
    new_ticker = st.session_state.new_dividend_ticker.upper()
    if new_ticker and new_ticker not in st.session_state.dividend_stocks:
        st.session_state.dividend_stocks.append(new_ticker)
        st.session_state.new_dividend_ticker = "" # Clear input
        st.rerun() # Rerun to update multiselect and write
    elif not new_ticker:
        st.sidebar.warning("Ticker cannot be empty.")
    else:
        st.sidebar.warning(f"{new_ticker} is already in the list.")

# Use st.session_state.remove_dividend_multiselect directly in the logic
st.sidebar.multiselect(
    "Select Dividend Ticker(s) to Remove",
    options=st.session_state.get('dividend_stocks', []), 
    key="remove_dividend_multiselect"
)
if st.sidebar.button("Remove Selected", key="remove_selected_dividend_button"):
    tickers_to_remove = st.session_state.remove_dividend_multiselect
    if tickers_to_remove:
        st.session_state.dividend_stocks = [
            ticker for ticker in st.session_state.dividend_stocks if ticker not in tickers_to_remove
        ]
        st.session_state.remove_dividend_multiselect = [] # Clear selection
        st.rerun() # Rerun to update multiselect and write
    else:
        st.sidebar.warning("No tickers selected for removal.")

st.sidebar.write("Current Dividend Tickers:", ", ".join(st.session_state.get('dividend_stocks', [])))

# --- Growth Stocks ---
st.sidebar.subheader("Growth Stocks")
st.sidebar.text_input("Add Growth Ticker", key="new_growth_ticker")
if st.sidebar.button("Add", key="add_growth_ticker_button"):
    new_ticker = st.session_state.new_growth_ticker.upper()
    if new_ticker and new_ticker not in st.session_state.growth_stocks:
        st.session_state.growth_stocks.append(new_ticker)
        st.session_state.new_growth_ticker = "" # Clear input
        st.rerun()
    elif not new_ticker:
        st.sidebar.warning("Ticker cannot be empty.")
    else:
        st.sidebar.warning(f"{new_ticker} is already in the list.")

st.sidebar.multiselect(
    "Select Growth Ticker(s) to Remove",
    options=st.session_state.get('growth_stocks', []), 
    key="remove_growth_multiselect"
)
if st.sidebar.button("Remove Selected", key="remove_selected_growth_button"):
    tickers_to_remove = st.session_state.remove_growth_multiselect
    if tickers_to_remove:
        st.session_state.growth_stocks = [
            ticker for ticker in st.session_state.growth_stocks if ticker not in tickers_to_remove
        ]
        st.session_state.remove_growth_multiselect = [] # Clear selection
        st.rerun()
    else:
        st.sidebar.warning("No tickers selected for removal.")

st.sidebar.write("Current Growth Tickers:", ", ".join(st.session_state.get('growth_stocks', [])))

# --- Index Funds ---
st.sidebar.subheader("Index Funds")
st.sidebar.text_input("Add Index Fund Ticker", key="new_index_fund_ticker")
if st.sidebar.button("Add", key="add_index_fund_button"):
    new_ticker = st.session_state.new_index_fund_ticker.upper()
    if new_ticker and new_ticker not in st.session_state.index_funds:
        st.session_state.index_funds.append(new_ticker)
        st.session_state.new_index_fund_ticker = "" # Clear input
        st.rerun()
    elif not new_ticker:
        st.sidebar.warning("Ticker cannot be empty.")
    else:
        st.sidebar.warning(f"{new_ticker} is already in the list.")

st.sidebar.multiselect(
    "Select Index Fund Ticker(s) to Remove",
    options=st.session_state.get('index_funds', []), 
    key="remove_index_fund_multiselect"
)
if st.sidebar.button("Remove Selected", key="remove_selected_index_fund_button"):
    tickers_to_remove = st.session_state.remove_index_fund_multiselect
    if tickers_to_remove:
        st.session_state.index_funds = [
            ticker for ticker in st.session_state.index_funds if ticker not in tickers_to_remove
        ]
        st.session_state.remove_index_fund_multiselect = [] # Clear selection
        st.rerun()
    else:
        st.sidebar.warning("No tickers selected for removal.")

st.sidebar.write("Current Index Funds:", ", ".join(st.session_state.get('index_funds', [])))

# --- Save All Ticker Changes ---
st.sidebar.markdown("---") # Visual separator
if st.sidebar.button("Save Ticker Changes to File", key="save_all_tickers_button"):
    try:
        config_data_to_save = {
            "dividend_stocks": st.session_state.get('dividend_stocks', []),
            "growth_stocks": st.session_state.get('growth_stocks', []),
            "index_funds": st.session_state.get('index_funds', [])
        }
        with open("config.json", 'w') as f:
            json.dump(config_data_to_save, f, indent=2)
        st.sidebar.success("Ticker changes saved to config.json!")
    except Exception as e:
        st.sidebar.error(f"Error saving tickers: {e}")
