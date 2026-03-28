#!/usr/bin/env python3
"""
Sentiment Analyst - scrape_news.py
=====================================
CLI tool for fetching the latest news headlines for a stock ticker
and returning a lightweight sentiment signal.

Usage:
    python scrape_news.py <TICKER> [--limit 5] [--format json|markdown]

Examples:
    python scrape_news.py AAPL
    python scrape_news.py TSLA --limit 10 --format markdown

Output is written to stdout so it can be piped directly to an LLM.
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone

# Allow imports from the project root
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _project_root)

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "Missing dependency: yfinance. Run: pip install yfinance"}))
    sys.exit(1)

# ---------------------------------------------------------------------------
# Sentiment keyword lists
# ---------------------------------------------------------------------------
POSITIVE_KEYWORDS = [
    "beats", "beat", "surges", "surge", "record", "upgrade", "upgraded",
    "buy", "outperform", "growth", "strong", "profit", "profits", "gain",
    "gains", "rises", "rise", "soars", "soar", "rallies", "rally",
    "bullish", "positive", "higher", "increases", "increase", "jump", "jumps",
    "expands", "expansion", "boosts", "boost", "wins", "win", "breakthrough",
]

NEGATIVE_KEYWORDS = [
    "misses", "miss", "falls", "fall", "cuts", "cut", "downgrade", "downgraded",
    "sell", "underperform", "loss", "losses", "weak", "risk", "risks", "crash",
    "crashes", "drops", "drop", "slumps", "slump", "declines", "decline",
    "bearish", "negative", "lower", "decreases", "decrease", "plunges", "plunge",
    "shrinks", "shrink", "warns", "warning", "concern", "concerns", "fraud",
    "investigation", "lawsuit", "layoffs", "layoff", "recall", "crisis",
]


def classify_sentiment(title: str) -> str:
    """Classify a single headline as POSITIVE, NEGATIVE, or NEUTRAL."""
    title_lower = title.lower()
    pos_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in title_lower)
    neg_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in title_lower)
    if pos_hits > neg_hits:
        return "POSITIVE"
    if neg_hits > pos_hits:
        return "NEGATIVE"
    return "NEUTRAL"


def aggregate_sentiment(sentiments: list[str]) -> str:
    """Aggregate individual sentiments to an overall signal (majority vote)."""
    if not sentiments:
        return "NEUTRAL"
    counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for s in sentiments:
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get)


def fetch_headlines(ticker: str, limit: int) -> list[dict]:
    """Fetch latest news headlines for a ticker via yfinance."""
    t = yf.Ticker(ticker)
    raw_news = t.news or []

    headlines = []
    for item in raw_news[:limit]:
        # yfinance news item structure varies slightly by version
        content = item.get("content", item)
        title = (
            content.get("title")
            or item.get("title")
            or ""
        )
        publisher = (
            content.get("provider", {}).get("displayName")
            or item.get("publisher")
            or "Unknown"
        )
        pub_date_raw = (
            content.get("pubDate")
            or content.get("displayTime")
            or item.get("providerPublishTime")
            or None
        )

        # Normalise timestamp
        if isinstance(pub_date_raw, (int, float)):
            pub_date = datetime.fromtimestamp(pub_date_raw, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        elif isinstance(pub_date_raw, str):
            pub_date = pub_date_raw
        else:
            pub_date = "Unknown"

        url = (
            content.get("canonicalUrl", {}).get("url")
            or item.get("link")
            or ""
        )

        if title:
            headlines.append({
                "title": title,
                "publisher": publisher,
                "published": pub_date,
                "url": url,
                "sentiment": classify_sentiment(title),
            })

    return headlines


def output_json(ticker: str, headlines: list[dict], overall_sentiment: str) -> None:
    payload = {
        "ticker": ticker.upper(),
        "overall_sentiment": overall_sentiment,
        "headlines_analysed": len(headlines),
        "headlines": [
            {
                "headline": f"Headline: {h['title']}, Publisher: {h['publisher']}, Published: {h['published']}",
                "sentiment": h["sentiment"],
                "url": h["url"],
            }
            for h in headlines
        ],
    }
    print(json.dumps(payload, indent=2))


def output_markdown(ticker: str, headlines: list[dict], overall_sentiment: str) -> None:
    sentiment_icon = {"POSITIVE": "🟢", "NEGATIVE": "🔴", "NEUTRAL": "🟡"}.get(overall_sentiment, "🟡")
    print(f"# Sentiment Analysis: {ticker.upper()}\n")
    print(f"**Overall Sentiment**: {sentiment_icon} `{overall_sentiment}`  ")
    print(f"**Headlines Analysed**: {len(headlines)}\n")
    print("## Headlines\n")
    for h in headlines:
        icon = {"POSITIVE": "🟢", "NEGATIVE": "🔴", "NEUTRAL": "🟡"}.get(h["sentiment"], "🟡")
        print(f"{icon} **Headline**: {h['title']}  ")
        print(f"   **Publisher**: {h['publisher']}  ")
        print(f"   **Published**: {h['published']}  ")
        print(f"   **Sentiment**: `{h['sentiment']}`  ")
        if h.get("url"):
            print(f"   **URL**: {h['url']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Sentiment Analyst — fetch latest news headlines and classify sentiment for a stock ticker."
    )
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--limit", type=int, default=5, help="Number of headlines to fetch (default: 5)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")

    args = parser.parse_args()
    ticker = args.ticker.upper()

    headlines = fetch_headlines(ticker, args.limit)

    if not headlines:
        print(json.dumps({"error": f"No news found for ticker: '{ticker}'. The ticker may be invalid or no recent news is available."}))
        sys.exit(1)

    overall_sentiment = aggregate_sentiment([h["sentiment"] for h in headlines])

    if args.format == "markdown":
        output_markdown(ticker, headlines, overall_sentiment)
    else:
        output_json(ticker, headlines, overall_sentiment)


if __name__ == "__main__":
    main()
