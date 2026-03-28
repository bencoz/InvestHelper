---
name: Portfolio Manager
description: Scores portfolio diversification using the HHI index, generates portfolio allocations, and suggests rebalancing actions. Outputs structured data for LLM consumption.
---

# Portfolio Manager Skill

## Overview
This skill focuses on asset allocation, diversification scoring, and rebalancing advice. It wraps the core portfolio functions from `stock_utils.py` and exposes them as a CLI tool so an Orchestrator agent can request and interpret portfolio health data.

## Capabilities

### 1. Calculate Diversification Score (`calculate_diversification_score`)
- **Usage**: Score a portfolio based on sector concentration using the Herfindahl-Hirschman Index (HHI).
- **Function**: `stock_utils.calculate_diversification_score(portfolio_df)`
- **Input**: CSV file or DataFrame with `symbol` and `Qty` columns.
- **Output**: Score (0–100).
    - **> 80**: Well-diversified.
    - **60–80**: Moderate — review allocations.
    - **< 60**: Poor — rebalancing strongly advised.

### 2. Generate Portfolio (`generate_portfolio`)
- **Usage**: Allocate a total budget across a list of stocks.
- **Function**: `stock_utils.generate_portfolio(stock_prices, total_budget, option='random')`
- **Logic**: Fetches mean prices and allocates shares based on remaining budget.

### 3. Suggest Rebalancing Actions (`suggest_rebalancing_actions`)
- **Usage**: Get text-based advice on how to improve a low diversification score.
- **Function**: `stock_utils.suggest_rebalancing_actions(portfolio_df, score)`
- **Output**: List of actionable strings, e.g., "Consider reducing exposure to Technology".

## CLI Entry Point
- **Script**: `.agent/skills/portfolio_manager/scripts/score_diversity.py`
- **Usage**: `python score_diversity.py <portfolio.csv> [--format json|markdown]`
- **CSV Format**: Must have columns `symbol` (ticker) and `Qty` (number of shares held).

## Instruction for Agent
Prioritize diversification (HHI score). When reporting portfolio health, always explain *why* the score is what it is — e.g., "Concentrated 70% in Technology sector." When generating portfolios, explain *why* the mix was chosen (e.g., "Combines high-growth Tech with stable defensive Utilities").
