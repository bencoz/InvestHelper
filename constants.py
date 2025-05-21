import json

# Load stock lists from config.json
try:
    with open("config.json", 'r') as f:
        config_data = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Please ensure the file exists in the root directory.")
    # Provide default empty lists or raise an error if configuration is critical
    dividend_stocks = []
    growth_stocks = []
    index_funds = []
except json.JSONDecodeError:
    print("Error: Could not decode config.json. Please ensure it is valid JSON.")
    # Provide default empty lists or raise an error
    dividend_stocks = []
    growth_stocks = []
    index_funds = []
else:
    dividend_stocks = config_data.get("dividend_stocks", [])
    growth_stocks = config_data.get("growth_stocks", [])
    index_funds = config_data.get("index_funds", [])

# The following is for potential future use, if we want to validate the loaded lists.
# For now, we just load them or use empty lists on error.
if not all(isinstance(stock, str) for stock_list in [dividend_stocks, growth_stocks, index_funds] for stock in stock_list):
    # This basic check ensures all items in the lists are strings.
    # More complex validation could be added here (e.g., checking for empty strings, specific formats).
    print("Warning: Some stock tickers loaded from config.json may not be strings. This could lead to errors.")

# Example of how these lists would be used in main.py (no changes needed in main.py):
# from constants import dividend_stocks, growth_stocks, index_funds
# ... rest of main.py logic ...
