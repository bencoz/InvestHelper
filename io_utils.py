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
