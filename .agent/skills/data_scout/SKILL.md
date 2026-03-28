---
name: Data Scout
description: Fetches raw market data. Retrieves OHLCV price history and sector classification for any stock ticker using yfinance, with robust caching to prevent API rate limits.
---

# Data Scout Skill

## Overview
This skill is the gateway to the outside world (Stock Market). It handles fetching, caching, and validating raw market data. All output is formatted as JSON or Markdown so it can be piped directly to an LLM.

## Capabilities

### 1. Fetch Stock Data (`fetch_financials.py`)
- **Script**: `.agent/skills/data_scout/scripts/fetch_financials.py`
- **Usage**: Get OHLCV (Open, High, Low, Close, Volume) data for a given ticker and date range.
- **CLI**: `python fetch_financials.py <TICKER> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--period 1y] [--interval 1d]`
- **Underlying**: Uses `yfinance` via `stock_utils.get_stock_data`.
- **Caching**: Implements robust caching (`cached_stock_data.py`) to prevent rate limits.
- **Output Format**: JSON array of OHLCV rows, or a Markdown table.

### 2. Get Stock Sector
- **Function**: `stock_utils.get_stock_sector(ticker)`
- **Usage**: Identify the industry sector of a ticker (e.g., AAPL → "Technology").
- **Critical For**: Diversification calculations in the Portfolio Manager skill.

## Dependencies
- `yfinance`
- `pandas`
- `cached_stock_data.py`
- `stock_utils.py`

## Error Handling
- If `get_stock_data` returns an empty DataFrame, the **Data Scout** must report `{"error": "Data Unavailable or Invalid Ticker"}` to stdout.
- Handle API limits gracefully — rely on the cache layer before making live network requests.

## Instruction for Agent
Focus on data integrity above all. If a ticker symbol is invalid or data cannot be fetched, report it immediately using a structured error JSON. Do not guess or fabricate data.
