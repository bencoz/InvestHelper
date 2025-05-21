import yfinance as yf
import pandas as pd

# Step 1: Get the S&P 500 tickers along with additional information like sector and company name
sp500_df = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
sp500_tickers = sp500_df['Symbol'].tolist()
sp500_tickers = [ticker.replace('.', '-') for ticker in sp500_tickers]  # Replace dots with dashes

# Step 2: Fetch the dividend yield and stock price information for each ticker
tickers = yf.Tickers(sp500_tickers)
dividends = tickers.history(period='1y')['Dividends']
prices = tickers.history(period='1d')['Close'].iloc[-1]  # Get the latest closing prices

dividend_yields = {}

# Step 3: Calculate the dividend yield for each stock
for stock in sp500_tickers:
    try:
        stock_dividends = dividends[stock]
        stock_price = prices.get(stock, 0)

        if not stock_dividends.empty and stock_price > 0:
            total_dividend = stock_dividends.sum()
            dividend_yield = (total_dividend / stock_price) * 100
            dividend_yields[stock] = dividend_yield
    except Exception as e:
        print(f"Error fetching data for {stock}: {e}")

# Step 4: Sort the companies by dividend yield in descending order
top_dividend_stocks = sorted(dividend_yields.items(), key=lambda x: x[1], reverse=True)[:100]

# Step 5: Display the top 10 companies with the highest dividend yield along with additional info
print("Top 100 S&P 500 Companies with the Highest Dividend Yield:\n")
data = []
for stock, yield_ in top_dividend_stocks:
    company_info = sp500_df[sp500_df['Symbol'] == stock].iloc[0]
    company_name = company_info['Security']
    sector = company_info['GICS Sector']

    # Fetch additional information using yfinance
    stock_info = yf.Ticker(stock).info
    short_description = stock_info.get('longBusinessSummary', 'No description available.')
    data.append((company_name, stock, sector, yield_, short_description))
    print(f"{company_name} ({stock})")
    print(f"Sector: {sector}")
    print(f"Dividend Yield: {yield_:.2f}%")
    print(f"About: {short_description}\n")
    print("-" * 80)

# store data as a dataframe
df = pd.DataFrame(data, columns=['Company Name', 'Stock Symbol', 'Sector', 'Dividend Yield', 'Description'])
df.to_csv('top_dividend_yield.csv', index=False)