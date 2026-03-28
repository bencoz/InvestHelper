import streamlit as st
import pandas as pd
import plotly.express as px # Added import for plotly
from datetime import datetime, date # Ensure date is imported
import logging
from logging_config import setup_logging
from exceptions import InvestHelperError, DataFetchError, InvalidTickerError, InsufficientDataError

# Initialize logging
logger = setup_logging()

# Import functions from existing project modules
from main import prepare_stock_selection, fetch_stock_data # get_user_investment_preferences removed as it's handled by UI
from stock_utils import (
    generate_portfolio, get_stock_data, ma_strategy, buy_sell_signals, backtest, RSI,
    calculate_diversification_score, suggest_rebalancing_actions
)
from io_utils import get_price_ma_and_wealth_plots, get_rsi_plot # Updated plotting functions
from constants import dividend_stocks, growth_stocks, index_funds
from cache import stock_cache
from persistent_cache import persistent_cache

st.set_page_config(layout="wide")

st.title("InvestHelper")
st.caption("AI-Powered Stock Research & Portfolio Management")

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose the app mode",
                                ["Portfolio Generator", "Stock Analyzer", "Portfolio Analyzer"])

# --- Cache Management (Developer Mode only) ---
if st.sidebar.checkbox("Developer Mode", value=False, key="dev_mode"):
    with st.sidebar.expander("Cache Management"):
        stats = stock_cache.get_stats()
        st.write(f"Memory Cache: {stats['entries']} entries")
        
        # Display persistent cache disk size
        import os
        from pathlib import Path
        cache_dir = Path(".cache")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            st.write(f"Disk Cache: {len(cache_files)} files ({total_size / 1024:.1f} KB)")
            
            # Show oldest cached entry
            if cache_files:
                oldest_mtime = min(f.stat().st_mtime for f in cache_files)
                from datetime import datetime as dt
                oldest_dt = dt.fromtimestamp(oldest_mtime)
                age_minutes = (dt.now() - oldest_dt).total_seconds() / 60
                if age_minutes < 60:
                    st.write(f"Oldest entry: {age_minutes:.0f} min ago")
                else:
                    st.write(f"Oldest entry: {age_minutes / 60:.1f} hours ago")
        else:
            st.write("Disk Cache: empty")
        
        # Force Refresh toggle
        force_refresh = st.checkbox("Force Refresh (bypass cache)", value=False, key="force_refresh_toggle")
        
        if st.button("Clear Cache"):
            stock_cache.clear()
            persistent_cache.clear()
            st.cache_data.clear()
            st.success("Cache cleared!")

# --- Portfolio Generator Mode ---
if app_mode == "Portfolio Generator":
    st.header("Generate Your Stock Portfolio")
    st.warning("⚠️ This tool is for educational and informational purposes only. It does not constitute financial advice. Past performance does not guarantee future results. Investing involves risk, including the possible loss of principal.")

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
                # Ensure constants are loaded (dividend_stocks, growth_stocks, index_funds are imported from constants.py)
                selected_tickers = prepare_stock_selection(
                    dividend_investing, growth_investing, index_investing,
                    dividend_stocks, growth_stocks, index_funds
                )

                if not selected_tickers:
                    st.warning("No stock categories selected, or no stocks found for the selected categories. Please check your selections and `config.json`.")
                else:
                    # DEBUG: st.write(f"Selected tickers: {', '.join(selected_tickers)}")
                    try:
                        # 2. Fetch stock data (respect Force Refresh toggle)
                        use_cache = not st.session_state.get("force_refresh_toggle", False)
                        stocks_data_for_portfolio = fetch_stock_data(selected_tickers, period=PERIOD, use_cache=use_cache)

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
                                portfolio_df = pd.DataFrame(raw_portfolio, columns=["Stock", "Shares", "Mean Price (90d)", "Current Price"])
                                portfolio_df = portfolio_df[portfolio_df["Shares"] > 0]

                                if portfolio_df.empty:
                                    st.info("No stocks were allocated with enough budget to purchase at least one share, or all selected stocks were filtered out after generation.")
                                else:
                                    st.subheader("Generated Portfolio:")
                                    st.dataframe(portfolio_df.set_index("Stock"))
                                    
                                    total_investment_mean_price = (portfolio_df["Shares"] * portfolio_df["Mean Price (90d)"]).sum()
                                    st.metric(label=f"Total Portfolio Value (at 90d mean prices)", value=f"${total_investment_mean_price:,.2f}")
                                    
                                    total_investment_current_price = (portfolio_df["Shares"] * portfolio_df["Current Price"]).sum()
                                    st.metric(label="Total Portfolio Value (at current prices)", value=f"${total_investment_current_price:,.2f}")
                                    
                                    st.caption(f"Note: The 'random' allocation strategy prioritizes stocks with a larger positive difference between current and mean price. Results may vary if not all budget is used.")
                    except DataFetchError as e:
                        logger.error(f"Data fetch error during portfolio generation: {e}")
                        st.error(f"Failed to fetch necessary stock data. Please check your internet connection and try again.")
                    except (InvestHelperError, ValueError, TypeError) as e:
                        logger.error(f"An error occurred during portfolio generation: {e}", exc_info=True)
                        st.error(f"An unexpected error occurred: {e}")
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

                try:
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
                except DataFetchError as e:
                    logger.error(f"Data fetch error for {stock_ticker}: {e}")
                    st.error(f"Failed to fetch data for {stock_ticker}. Please check the ticker symbol and try again.")
                except (InvestHelperError, ValueError, KeyError, TypeError) as e:
                    logger.error(f"An error occurred during the stock analysis for {stock_ticker}: {e}", exc_info=True)
                    st.error(f"An error occurred during the stock analysis for {stock_ticker}: {e}")
                    st.error("This could be due to insufficient data for the selected period (e.g., for Moving Averages), or an issue with the underlying calculations. Try a longer date range or a different stock.")
                    st.error("Please check the console for more details if you are running this locally.")

# --- Portfolio Analyzer Mode ---
elif app_mode == "Portfolio Analyzer":
    st.header("Portfolio Analyzer")

    # Initialize session state variables for this mode
    if 'diversification_score' not in st.session_state:
        st.session_state.diversification_score = None
    if 'processed_portfolio_df' not in st.session_state:
        st.session_state.processed_portfolio_df = None
    if 'uploaded_file_name' not in st.session_state: # To track if file changes
        st.session_state.uploaded_file_name = None

    # CSV template download
    sample_csv = "symbol,Qty\nAAPL,10\nMSFT,5\nGOOG,8\nVTI,20\n"
    st.download_button("📥 Download Sample CSV Template", sample_csv, "portfolio_template.csv", "text/csv")

    uploaded_file = st.file_uploader("Upload your portfolio CSV file", type=["csv"])

    if uploaded_file is not None:
        # Check if it's a new file; if so, reset analysis
        if st.session_state.uploaded_file_name != uploaded_file.name:
            st.session_state.diversification_score = None
            st.session_state.processed_portfolio_df = None
            st.session_state.uploaded_file_name = uploaded_file.name

        try:
            df_uploaded = pd.read_csv(uploaded_file)

            required_columns = ["symbol", "Qty"]
            original_columns = {col.lower(): col for col in df_uploaded.columns}
            missing_cols = [col for col in required_columns if col.lower() not in original_columns]

            if missing_cols:
                st.error(f"The uploaded CSV is missing the following required columns: {', '.join(missing_cols)}. Please ensure your CSV has 'symbol' and 'Qty' columns.")
                st.session_state.diversification_score = None # Reset on error
                st.session_state.processed_portfolio_df = None
            else:
                df_uploaded.rename(columns={original_columns['symbol']: 'symbol', original_columns['qty']: 'Qty'}, inplace=True)
                st.success("File uploaded successfully!")
                st.caption("Your Uploaded Portfolio:")
                st.dataframe(df_uploaded, height=230)

                # Calculate score only if not already calculated for this file
                if st.session_state.processed_portfolio_df is None :
                    with st.spinner("Analyzing portfolio diversification..."):
                        score, processed_df = calculate_diversification_score(df_uploaded.copy())
                        st.session_state.diversification_score = score
                        st.session_state.processed_portfolio_df = processed_df
                
        except pd.errors.EmptyDataError:
            logger.warning("Uploaded empty CSV file")
            st.error("The uploaded CSV file is empty. Please upload a valid CSV file.")
            st.session_state.diversification_score = None
            st.session_state.processed_portfolio_df = None
        except pd.errors.ParserError:
            logger.warning("Uploaded malformed CSV file")
            st.error("The uploaded CSV file is malformed. Please ensure it is a valid CSV file.")
            st.session_state.diversification_score = None
            st.session_state.processed_portfolio_df = None
        except (InvestHelperError, ValueError, KeyError, OSError) as e:
            logger.error(f"Error processing uploaded file: {e}", exc_info=True)
            st.error(f"An error occurred while processing the file: {e}")
            st.session_state.diversification_score = None
            st.session_state.processed_portfolio_df = None

    # Display score and optimization button if score is available
    if st.session_state.diversification_score is not None:
        score_value = st.session_state.diversification_score
        st.metric("Portfolio Diversification Score", f"{score_value:.1f} / 100")

        processed_df_check = st.session_state.processed_portfolio_df

        # Display Sector Allocation Pie Chart
        if processed_df_check is not None and not processed_df_check.empty and \
           'sector' in processed_df_check.columns and 'market_value' in processed_df_check.columns and \
           processed_df_check['market_value'].sum() > 0:
            
            st.subheader("Portfolio Sector Allocation")
            sector_allocations = processed_df_check.groupby('sector')['market_value'].sum().reset_index()
            
            # Filter out sectors with zero or negligible market value for a cleaner pie chart
            sector_allocations = sector_allocations[sector_allocations['market_value'] > 0.01]

            if not sector_allocations.empty:
                fig_sector_pie = px.pie(sector_allocations,
                                        names='sector',
                                        values='market_value',
                                        title='Sector Allocation by Market Value',
                                        hole=0.3)
                fig_sector_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_sector_pie, use_container_width=True)
            else:
                st.write("No significant sector allocations to display in chart (all market values are too small or zero).")

        # Check if the score indicates a successful calculation for suggesting actions
        if processed_df_check is not None and not processed_df_check.empty and \
           'market_value' in processed_df_check.columns and processed_df_check['market_value'].sum() > 0:
            if st.button("Suggest Diversification Actions"):
                with st.spinner("Generating suggestions..."):
                    suggestions = suggest_rebalancing_actions(
                        st.session_state.processed_portfolio_df,
                        st.session_state.diversification_score
                    )
                    st.subheader("Rebalancing Suggestions:")
                    if suggestions:
                        for suggestion in suggestions:
                            st.info(suggestion)
                    else:
                        st.info("No specific suggestions at this time.")
        elif score_value == 0.0 : # Specifically handle 0.0 if it might mean an error from calculation
             st.warning("Could not calculate a meaningful diversification score. This may be due to issues fetching stock data (e.g., invalid tickers, no recent price data for any stock), all quantities being zero, or an empty portfolio resulting in zero total market value. Please check your CSV file.")

    elif uploaded_file is not None: # If file was uploaded but score is None (due to error during processing)
        st.error("Failed to process the portfolio for diversification analysis. Please check the file and try again.")

st.sidebar.info(
    "This app helps novice investors with stock research and portfolio generation."
)

# --- Persistent Financial Disclaimer Footer ---
st.divider()
st.caption("⚠️ This tool is for educational and informational purposes only. It does not constitute financial advice. Investing involves risk of loss.")
