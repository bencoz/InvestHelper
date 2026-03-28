---
name: Sentiment Analyst
description: Fetches and interprets the latest news headlines for a stock ticker using yfinance, providing a sentiment signal (POSITIVE / NEUTRAL / NEGATIVE) based on title analysis. Outputs structured data for LLM consumption.
---

# Sentiment Analyst Skill

## Overview
This skill ingests alternative data (news headlines) for a given stock ticker to provide a sentiment signal as a complement to technical analysis. It is the competitive-edge data layer of the InvestHelper agentic system.

## Capabilities

### 1. Fetch News Headlines (`scrape_news.py`)
- **Script**: `.agent/skills/sentiment_analyst/scripts/scrape_news.py`
- **Source**: `yfinance` news property (`yf.Ticker(symbol).news`)
- **CLI**: `python scrape_news.py <TICKER> [--limit 5] [--format json|markdown]`
- **Output Format**:
  ```
  Headline: [Title], Publisher: [Org], Published: [timestamp]
  ```

### 2. Sentiment Signal
- The script performs lightweight keyword-based sentiment classification on each headline:
    - **POSITIVE**: Keywords like "beats", "surges", "record", "upgrade", "buy", "growth", "strong", "profit"
    - **NEGATIVE**: Keywords like "misses", "falls", "cuts", "downgrade", "sell", "loss", "weak", "risk", "crash"
    - **NEUTRAL**: No strong signal keywords detected.
- Aggregated signal is the majority sentiment across all fetched headlines.

## Instruction for Agent
Interpret title sentiment **cautiously** — headlines can be misleading in isolation. Always report the raw headlines alongside the sentiment signal so the Orchestrator can make a fully informed synthesis. Do not treat sentiment alone as a buy/sell directive.
