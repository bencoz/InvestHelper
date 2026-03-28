#!/usr/bin/env python3
"""
Portfolio Manager - score_diversity.py
========================================
CLI tool for calculating the HHI diversification score of a portfolio
and generating rebalancing suggestions.

Usage:
    python score_diversity.py <portfolio.csv> [--format json|markdown]

The CSV must have columns: symbol, Qty

Examples:
    python score_diversity.py my_portfolio.csv
    python score_diversity.py my_portfolio.csv --format markdown

Output is written to stdout so it can be piped directly to an LLM.
"""

import argparse
import json
import sys
import os

# Allow imports from the project root
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
sys.path.insert(0, _project_root)

try:
    import pandas as pd
    import numpy as np
    from logging_config import setup_logging
    setup_logging()
    from stock_utils import calculate_diversification_score, suggest_rebalancing_actions
except ImportError as e:
    print(json.dumps({"error": f"Missing dependency: {e}. Run: pip install -r requirements.txt"}))
    sys.exit(1)


def _json_serial(obj):
    """JSON serializer for types not serializable by default."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return round(float(obj), 4) if not (obj != obj) else None  # handle NaN
    raise TypeError(f"Type {type(obj)} not serializable")


def load_portfolio(csv_path: str) -> pd.DataFrame:
    """Load portfolio CSV and validate required columns."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Portfolio file not found: '{csv_path}'")
    df = pd.read_csv(csv_path)
    required = {"symbol", "Qty"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}. Expected: {required}")
    df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0)
    return df


def build_sector_breakdown(processed_df: pd.DataFrame, total_value: float) -> list:
    """Build a sector breakdown list sorted by weight descending."""
    if "sector" not in processed_df.columns or "market_value" not in processed_df.columns:
        return []
    sector_vals = processed_df.groupby("sector")["market_value"].sum()
    breakdown = []
    for sector, val in sector_vals.sort_values(ascending=False).items():
        breakdown.append({
            "sector": sector,
            "market_value": round(val, 2),
            "weight_pct": round((val / total_value) * 100, 2) if total_value > 0 else 0.0,
        })
    return breakdown


def output_json(score, processed_df, suggestions, portfolio_df) -> None:
    total_value = processed_df["market_value"].sum() if "market_value" in processed_df.columns else 0.0
    sector_breakdown = build_sector_breakdown(processed_df, total_value)

    payload = {
        "diversification_score": round(float(score), 2) if score is not None else None,
        "interpretation": (
            "Well-diversified" if score and score >= 80 else
            "Moderate — consider reviewing allocations" if score and score >= 60 else
            "Poorly diversified — rebalancing strongly advised"
        ),
        "total_portfolio_value": round(float(total_value), 2),
        "positions": len(portfolio_df),
        "sector_breakdown": sector_breakdown,
        "rebalancing_suggestions": suggestions,
    }
    print(json.dumps(payload, default=_json_serial, indent=2))


def output_markdown(score, processed_df, suggestions, portfolio_df) -> None:
    total_value = processed_df["market_value"].sum() if "market_value" in processed_df.columns else 0.0
    sector_breakdown = build_sector_breakdown(processed_df, total_value)

    interp = (
        "✅ Well-diversified" if score and score >= 80 else
        "⚠️ Moderate — consider reviewing allocations" if score and score >= 60 else
        "🔴 Poorly diversified — rebalancing strongly advised"
    )

    print("# Portfolio Diversification Report\n")
    print(f"**Diversification Score**: {score:.1f}/100  ")
    print(f"**Assessment**: {interp}  ")
    print(f"**Total Portfolio Value**: ${total_value:,.2f}  ")
    print(f"**Positions**: {len(portfolio_df)}\n")

    if sector_breakdown:
        print("## Sector Breakdown\n")
        print(f"{'Sector':<30} {'Market Value':>14} {'Weight %':>10}")
        print("-" * 56)
        for s in sector_breakdown:
            print(f"{s['sector']:<30} ${s['market_value']:>13,.2f} {s['weight_pct']:>9.1f}%")
        print()

    print("## Rebalancing Suggestions\n")
    for tip in suggestions:
        print(f"- {tip}")


def main():
    parser = argparse.ArgumentParser(
        description="Portfolio Manager — score HHI diversification and suggest rebalancing actions."
    )
    parser.add_argument("portfolio_csv", help="Path to portfolio CSV file (must have 'symbol' and 'Qty' columns)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")

    args = parser.parse_args()

    try:
        portfolio_df = load_portfolio(args.portfolio_csv)
    except (FileNotFoundError, ValueError) as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    score, processed_df = calculate_diversification_score(portfolio_df)

    if score is None:
        print(json.dumps({"error": "Failed to calculate diversification score — check data."}))
        sys.exit(1)

    suggestions = suggest_rebalancing_actions(processed_df, score)

    if args.format == "markdown":
        output_markdown(score, processed_df, suggestions, portfolio_df)
    else:
        output_json(score, processed_df, suggestions, portfolio_df)


if __name__ == "__main__":
    main()
