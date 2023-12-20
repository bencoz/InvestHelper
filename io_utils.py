import sys
import matplotlib.pyplot as plt


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


def print_graph(df, stock):
    fig = plt.figure(figsize=[15, 6])
    ax = plt.subplot(1, 1, 1)
    ax.plot(df['Date'], df['long_MA'], label='long MA')
    ax.plot(df['Date'], df['short_MA'], color='orange', label='short MA')
    ax.plot(df['Date'], df['Close'], color='black', label='Close')
    ax.plot(df['Date'], df['buy'], color='green', label='Buy', marker='^')

    ax.plot(df['Date'], df['sell'], color='red', label='Sell', marker='v')
    ax.legend(loc='upper right')
    ax.set_xlabel('Date')
    ax.set_title(stock)
    plt.show()

    fig = plt.figure(figsize=[15, 6])
    ax = plt.subplot(1, 1, 1)
    ax.plot(df['Date'], df['MA_wealth'], color='black', label='MA strategy wealth')
    ax.plot(df['Date'], df['LT_wealth'], color='red', label='buy and hold wealth')
    ax.legend(loc='upper left')
    ax.set_xlabel('date')
    ax.set_title(stock)
    plt.show()


def print_rsi_graph(df, rsi):
    # Make our resulting figure much bigger
    plt.rcParams['figure.figsize'] = (20, 20)
    # Create two charts on the same figure.
    ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=4, colspan=1)
    ax2 = plt.subplot2grid((10, 1), (5, 0), rowspan=4, colspan=1)

    # First chart:
    # Plot the closing price on the first chart
    ax1.plot(df['Close'], linewidth=2)
    ax1.set_title('Close Price')

    # Second chart
    # Plot the RSI
    ax2.set_title('Relative Strength Index')
    ax2.plot(rsi, color='orange', linewidth=1)
    # Add two horizontal lines, signalling the buy and sell ranges.
    # Oversold
    ax2.axhline(30, linestyle='--', linewidth=1.5, color='green')
    # Overbought
    ax2.axhline(70, linestyle='--', linewidth=1.5, color='red')

    plt.show()
