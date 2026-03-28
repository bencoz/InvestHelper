#!/usr/bin/env python3
"""
Technical Analyst - run_indicators.py
======================================
CLI tool for performing RSI and Moving Average technical analysis on a stock ticker.

Usage:
    python run_indicators.py <TICKER> [--short-ma 50] [--long-ma 200]
                                      [--period 2y] [--interval 1d]
                                      [--initial-wealth 10000]
                                      [--format json|markdown]

Examples:
    python run_indicators.py AAPL
    python run_indicators.py TSLA --short-ma 20 --long-ma 100 --format markdown

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
    import numpy as np
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
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV history for the ticker."""
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    if df is None or df.empty:
        return pd.DataFrame()
    df.reset_index(inplace=True)
    if "Datetime" in df.columns:
        df.rename(columns={"Datetime": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def compute_ma(df: pd.DataFrame, short_ma: int, long_ma: int) -> dict:
    """Compute MA crossover signals. Returns a summary dict."""
    df = df.copy()
    df["short_MA"] = df["Close"].rolling(short_ma).mean()
    df["long_MA"] = df["Close"].rolling(long_ma).mean()

    last = df.dropna(subset=["short_MA", "long_MA"])
    if last.empty:
        return {"signal": "INSUFFICIENT_DATA", "short_ma": short_ma, "long_ma": long_ma}

    latest = last.iloc[-1]
    prev = last.iloc[-2] if len(last) >= 2 else latest

    current_short = round(float(latest["short_MA"]), 4)
    current_long = round(float(latest["long_MA"]), 4)
    prev_short = round(float(prev["short_MA"]), 4)
    prev_long = round(float(prev["long_MA"]), 4)

    # Detect crossover
    golden_cross = prev_short <= prev_long and current_short > current_long
    death_cross = prev_short >= prev_long and current_short < current_long

    if golden_cross:
        signal = "BUY"
        reason = "Golden Cross: short MA crossed above long MA"
    elif death_cross:
        signal = "SELL"
        reason = "Death Cross: short MA crossed below long MA"
    elif current_short > current_long:
        signal = "BULLISH"
        reason = "Short MA is above long MA (uptrend)"
    else:
        signal = "BEARISH"
        reason = "Short MA is below long MA (downtrend)"

    return {
        "signal": signal,
        "reason": reason,
        "short_ma_period": short_ma,
        "long_ma_period": long_ma,
        "current_short_ma": current_short,
        "current_long_ma": current_long,
        "as_of": str(latest["Date"].date()),
    }


def compute_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """Compute RSI and return the latest value with interpretation."""
    change = df["Close"].diff().dropna()
    change_up = change.clip(lower=0)
    change_down = (-change).clip(lower=0)

    avg_up = change_up.rolling(period).mean()
    avg_down = change_down.rolling(period).mean()

    rsi_series = 100 * avg_up / (avg_up + avg_down)
    rsi_series = rsi_series.dropna()

    if rsi_series.empty:
        return {"signal": "INSUFFICIENT_DATA", "rsi": None}

    latest_rsi = round(float(rsi_series.iloc[-1]), 2)

    if latest_rsi > 70:
        signal = "OVERBOUGHT"
        interpretation = f"RSI {latest_rsi} > 70: Potential sell signal."
    elif latest_rsi < 30:
        signal = "OVERSOLD"
        interpretation = f"RSI {latest_rsi} < 30: Potential buy signal."
    else:
        signal = "NEUTRAL"
        interpretation = f"RSI {latest_rsi} is in neutral territory (30–70)."

    return {
        "signal": signal,
        "rsi": latest_rsi,
        "rsi_period": period,
        "interpretation": interpretation,
    }


def output_json(ticker: str, ma_result: dict, rsi_result: dict, latest_close: float, as_of: str) -> None:
    payload = {
        "ticker": ticker.upper(),
        "latest_close": round(latest_close, 4),
        "as_of": as_of,
        "moving_average": ma_result,
        "rsi": rsi_result,
    }
    print(json.dumps(payload, default=_json_serial, indent=2))


def output_markdown(ticker: str, ma_result: dict, rsi_result: dict, latest_close: float, as_of: str) -> None:
    print(f"# Technical Analysis: {ticker.upper()}\n")
    print(f"**Latest Close**: ${latest_close:.2f}  ")
    print(f"**As of**: {as_of}\n")

    print("## Moving Average Signal")
    print(f"- **Signal**: `{ma_result.get('signal')}`")
    print(f"- **Reason**: {ma_result.get('reason', 'N/A')}")
    print(f"- **Short MA ({ma_result.get('short_ma_period')}-day)**: {ma_result.get('current_short_ma')}")
    print(f"- **Long MA ({ma_result.get('long_ma_period')}-day)**: {ma_result.get('current_long_ma')}\n")

    print("## RSI Signal")
    print(f"- **Signal**: `{rsi_result.get('signal')}`")
    print(f"- **RSI ({rsi_result.get('rsi_period')}-period)**: {rsi_result.get('rsi')}")
    print(f"- **Interpretation**: {rsi_result.get('interpretation', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="Technical Analyst — compute RSI and MA signals for a stock ticker."
    )
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--short-ma", type=int, default=50, help="Short Moving Average period (default: 50)")
    parser.add_argument("--long-ma", type=int, default=200, help="Long Moving Average period (default: 200)")
    parser.add_argument("--period", default="2y", help="History period, e.g. 1y, 2y, 6mo (default: 2y)")
    parser.add_argument("--interval", default="1d", help="Data interval (default: 1d)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    df = fetch_history(ticker, args.period, args.interval)
    if df.empty:
        print(json.dumps({"error": f"Data Unavailable or Invalid Ticker: '{ticker}'"}))
        sys.exit(1)

    ma_result = compute_ma(df, args.short_ma, args.long_ma)
    rsi_result = compute_rsi(df)

    latest_close = float(df["Close"].iloc[-1])
    as_of = str(df["Date"].iloc[-1].date()) if hasattr(df["Date"].iloc[-1], "date") else str(df["Date"].iloc[-1])

    if args.format == "markdown":
        output_markdown(ticker, ma_result, rsi_result, latest_close, as_of)
    else:
        output_json(ticker, ma_result, rsi_result, latest_close, as_of)


if __name__ == "__main__":
    main()
