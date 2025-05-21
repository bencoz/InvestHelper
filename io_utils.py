import sys
import matplotlib.pyplot as plt


def query_yes_no(question, default="yes"):
    """Asks a yes/no question via input() and returns their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid_responses = {"yes": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt_suffix = " [y/n] "
    elif default == "yes":
        prompt_suffix = " [Y/n] "
    elif default == "no":
        prompt_suffix = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        sys.stdout.write(question + prompt_suffix)
        choice = input().lower().strip()  # Normalize input
        if default is not None and choice == "":
            return valid_responses[default]
        elif choice in valid_responses:
            return valid_responses[choice]
        else:
            sys.stdout.write("Please answer with 'yes' or 'no'.\n")


def get_price_ma_and_wealth_plots(df, stock):
    """
    Generates two Matplotlib figures:
    1. Stock prices with Moving Averages and Buy/Sell signals.
    2. MA strategy wealth vs. Buy and Hold wealth.
    Returns a tuple of (fig_price_ma, fig_wealth).
    """
    # Figure 1: Price, MAs, Buy/Sell signals
    fig_price_ma = plt.figure(figsize=[15, 6])
    ax1 = fig_price_ma.add_subplot(1, 1, 1)
    ax1.plot(df['Date'], df['long_MA'], label='Long MA')
    ax1.plot(df['Date'], df['short_MA'], color='orange', label='Short MA')
    ax1.plot(df['Date'], df['Close'], color='black', label='Close Price')
    
    # Plot buy signals if 'buy' column exists and has data
    if 'buy' in df.columns and not df['buy'].dropna().empty:
        ax1.plot(df['Date'], df['buy'], color='green', label='Buy Signal', marker='^', linestyle='None', markersize=10)
    
    # Plot sell signals if 'sell' column exists and has data
    if 'sell' in df.columns and not df['sell'].dropna().empty:
        ax1.plot(df['Date'], df['sell'], color='red', label='Sell Signal', marker='v', linestyle='None', markersize=10)
        
    ax1.legend(loc='upper right')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price')
    ax1.set_title(f'{stock} - Price, Moving Averages, and Signals')
    fig_price_ma.tight_layout()

    # Figure 2: MA Wealth vs LT Wealth
    fig_wealth = plt.figure(figsize=[15, 6])
    ax2 = fig_wealth.add_subplot(1, 1, 1)
    if 'MA_wealth' in df.columns: # Check if MA_wealth column exists (from backtest)
        ax2.plot(df['Date'], df['MA_wealth'], color='black', label='MA Strategy Wealth')
    if 'LT_wealth' in df.columns: # Check if LT_wealth column exists (from backtest)
        ax2.plot(df['Date'], df['LT_wealth'], color='red', label='Buy and Hold Wealth')
    ax2.legend(loc='upper left')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Portfolio Value')
    ax2.set_title(f'{stock} - Investment Strategy Wealth Comparison')
    fig_wealth.tight_layout()
    
    return fig_price_ma, fig_wealth


def get_rsi_plot(df_with_close_price, rsi_series):
    """
    Generates a Matplotlib figure for the Relative Strength Index (RSI).
    'df_with_close_price' is the DataFrame that must contain the 'Close' price and its index must be DatetimeIndex.
    'rsi_series' is the Pandas Series containing the RSI values, indexed by date.
    Returns the Matplotlib figure object.
    """
    fig_rsi = plt.figure(figsize=[15, 7]) # Adjusted size for better layout with two subplots

    # Ensure the DataFrame index is datetime for proper plotting
    # This should ideally be handled before calling this function (e.g., df.set_index('Date'))
    # For safety, we can check here if it's not already the index for df_with_close_price
    df_plot = df_with_close_price.copy()
    if not isinstance(df_plot.index, pd.DatetimeIndex):
         if 'Date' in df_plot.columns:
            df_plot['Date'] = pd.to_datetime(df_plot['Date'])
            df_plot = df_plot.set_index('Date')
         else:
            # If no 'Date' column and index is not datetime, we can't proceed reliably
            # Or, if rsi_series has datetime index, we can use that.
            # For now, assume df_with_close_price comes with 'Date' as index or column.
            pass


    # Create two charts on the same figure.
    ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=5, colspan=1) # Adjusted rowspan
    ax2 = plt.subplot2grid((10, 1), (6, 0), rowspan=4, colspan=1) # Adjusted rowspan and start

    # First chart: Plot the closing price
    ax1.plot(df_plot.index, df_plot['Close'], linewidth=2, label='Close Price')
    ax1.set_title('Close Price')
    ax1.set_ylabel('Price')
    ax1.legend()

    # Second chart: Plot the RSI
    ax2.set_title('Relative Strength Index (RSI)')
    ax2.plot(rsi_series.index, rsi_series, color='orange', linewidth=1.5, label='RSI')
    ax2.axhline(30, linestyle='--', linewidth=1.5, color='green') # Oversold
    ax2.axhline(70, linestyle='--', linewidth=1.5, color='red')   # Overbought
    ax2.set_xlabel('Date')
    ax2.set_ylabel('RSI')
    ax2.legend()
    
    fig_rsi.tight_layout() # Adjust layout to prevent overlap
    return fig_rsi
