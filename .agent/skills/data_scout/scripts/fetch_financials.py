#!/usr/bin/env python3
"""
Data Scout - fetch_financials.py
=================================
CLI tool for fetching OHLCV stock price history from yfinance.

Usage:
    python fetch_financials.py <TICKER> [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                        [--period 1y] [--interval 1d] [--format json|markdown]

Examples:
    python fetch_financials.py AAPL --start 2024-01-01 --end 2024-12-31
    python fetch_financials.py TSLA --period 6mo --format markdown

Output is written to stdout so it can be piped directly to an LLM.
"""

import argparse
import json
import sys
import os
from datetime import datetime, date

# Allow imports from the project root
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _project_root)

try:
    import yfinance as yf
    import pandas as pd
    from logging_config import setup_logging
    setup_logging()
except ImportError as e:
    print(json.dumps({"error": f"Missing dependency: {e}. Run: pip install -r requirements.txt"}))
    sys.exit(1)


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json."""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def fetch_stock_data_raw(ticker: str, start: str, end: str, period: str, interval: str) -> pd.DataFrame:
    """
    Fetch OHLCV stock data using yfinance directly.
    Returns a cleaned DataFrame with a 'Date' column.
    """
    try:
        t = yf.Ticker(ticker)
        if start and end:
            df = t.history(start=start, end=end, interval=interval)
        else:
            df = t.history(period=period or "1y", interval=interval)

        if df is None or df.empty:
            return pd.DataFrame()

        df.reset_index(inplace=True)

        # Normalise the date column name
        if "Datetime" in df.columns:
            df.rename(columns={"Datetime": "Date"}, inplace=True)
        elif "index" in df.columns:
            df.rename(columns={"index": "Date"}, inplace=True)

        if "Date" not in df.columns:
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"])

        # Keep only relevant OHLCV columns
        keep_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in keep_cols if c in df.columns]]

        return df

    except Exception as exc:
        raise RuntimeError(f"yfinance error for '{ticker}': {exc}") from exc


def get_sector(ticker: str) -> str:
    """Return the sector classification for a ticker."""
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", "Unknown")
    except Exception:
        return "Unknown"


def output_json(df: pd.DataFrame, ticker: str, sector: str) -> None:
    records = df.to_dict(orient="records")
    payload = {
        "ticker": ticker.upper(),
        "sector": sector,
        "rows": len(records),
        "columns": list(df.columns),
        "data": records,
    }
    print(json.dumps(payload, default=_json_serial, indent=2))


def output_markdown(df: pd.DataFrame, ticker: str, sector: str) -> None:
    print(f"# {ticker.upper()} Price History\n")
    print(f"**Sector**: {sector}  \n**Rows**: {len(df)}\n")
    print(df.to_markdown(index=False))


def main():
    parser = argparse.ArgumentParser(
        description="Data Scout — fetch OHLCV price history for a stock ticker."
    )
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--period", default="1y", help="Period string, e.g. 1y, 6mo, 3mo (ignored if --start/--end set)")
    parser.add_argument("--interval", default="1d", help="Data interval, e.g. 1d, 1h, 1wk")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    try:
        df = fetch_stock_data_raw(ticker, args.start, args.end, args.period, args.interval)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if df.empty:
        print(json.dumps({"error": f"Data Unavailable or Invalid Ticker: '{ticker}'"}))
        sys.exit(1)

    sector = get_sector(ticker)

    if args.format == "markdown":
        output_markdown(df, ticker, sector)
    else:
        output_json(df, ticker, sector)


if __name__ == "__main__":
    main()
