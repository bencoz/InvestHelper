---
name: Technical Analyst
description: Performs technical analysis on stock price history. Calculates Moving Averages, RSI, and backtests strategies. Outputs signals in structured format for LLM consumption.
---

# Technical Analyst Skill

## Overview
This skill allows the agent to perform technical analysis on historical stock data. It wraps the core calculation functions in `stock_utils.py` and exposes them as a CLI tool, formatting all output as JSON or Markdown so an LLM can pipe and interpret the results.

## Capabilities

### 1. Moving Average Strategy (`ma_strategy`)
- **Usage**: Detect trends by comparing Short-Term MA vs Long-Term MA.
- **Function**: `stock_utils.ma_strategy(df, short_MA, long_MA)`
- **Interpretation**:
    - **Golden Cross**: Short MA crosses *above* Long MA → **BUY Signal**.
    - **Death Cross**: Short MA crosses *below* Long MA → **SELL Signal**.

### 2. RSI Calculation (`RSI`)
- **Usage**: Determine if a stock is overbought or oversold.
- **Function**: `stock_utils.RSI(df)`
- **Interpretation**:
    - **RSI > 70**: Overbought (Potential Sell Signal).
    - **RSI < 30**: Oversold (Potential Buy Signal).

### 3. Backtesting (`backtest`)
- **Usage**: Simulate an MA crossover trading strategy over historical data.
- **Function**: `stock_utils.backtest(df, stock, start, end, initial_wealth)`
- **Output**: MA Strategy final wealth vs Buy-and-Hold final wealth.

## CLI Entry Point
- **Script**: `.agent/skills/technical_analyst/scripts/run_indicators.py`
- **Usage**: `python run_indicators.py <TICKER> [--short-ma 50] [--long-ma 200] [--period 2y] [--format json|markdown]`

## Instruction for Agent
Focus on the data. Do not give financial advice — report **signals** only. If RSI > 70, report "Overbought". If RSI < 30, report "Oversold". Provide the raw numbers alongside the signal interpretation so the Orchestrator can synthesize a human-readable recommendation.
