# Task 10: Data Integrity & Caching Audit

## Overview
Fix critical data accuracy bugs in the Portfolio Generator and harden the two-tier caching layer against serving stale/incorrect financial data. The free yfinance API introduces split-adjusted pricing quirks and rate limits that must be explicitly handled.

## Priority
**Critical (Data Bug)** — Two bugs discovered by live audit:
1. VTI mean price displays as `$37.72` but should be ~$230+ (split-adjusted pricing).
2. **NEW (from logs)**: ~10 tickers (`SPY, QQQ, VOO, PANW, AVGO, CVX, CNQ, KMI, TXN, VIG`) crash with `"The truth value of a Series is ambiguous"` — these tickers are **silently dropped** from every portfolio.

## Estimated Effort
2-3 hours

## Root Cause Analysis

The pipeline is:
```
config.json tickers → main.py:fetch_stock_data() → main.py:_get_stock_stats()
  → cached_stock_data.py:get_stock_data_cached() → yf.download()
  → Returns df → df['Close'].mean() used as "Mean Price (2y)"
```

**Suspected root cause**: `yf.download()` returns **split-adjusted** historical prices by default (`auto_adjust=True` since yfinance 0.2.x). For VTI (which underwent a reverse split), the 2-year mean of *adjusted* prices can be dramatically lower than the *current market price*. The `mean_price` then gets used for share allocation (`max_shares = budget // mean_price`), producing wildly incorrect allocations.

**Caching risk**: The persistent cache (`persistent_cache.py`) has a 24h TTL. If stale adjusted data was cached before a split event, it would serve wrong numbers for up to 24 hours. Additionally, the cache key includes `period_str` but NOT an `auto_adjust` flag — meaning changing yfinance defaults silently corrupts cached results.

## Implementation Steps

### 0. Fix the pandas Series ambiguity crash (URGENT — 30 mins)
From the live logs:
```
Error fetching SPY: The truth value of a Series is ambiguous.
Use a.empty, a.bool(), a.item(), a.any() or a.all().
```
- [ ] In `main.py:_get_stock_stats()` (line 48-51), `current_price = df['Close'].iloc[-1]` can return a `pd.Series` instead of a scalar when yfinance returns multi-level column indices (this happens with recent yfinance versions). Then `pd.isna(mean_price)` crashes because it's applied to a Series.
  - **Fix**: Force scalar extraction:
    ```python
    current_price = float(df['Close'].iloc[-1])
    mean_price = float(df['Close'].mean())
    ```
  - Alternatively, flatten the columns after download: `df.columns = df.columns.get_level_values(0)` in `cached_stock_data.py:_fetch_stock_data()`.
- [ ] This same multi-level column issue likely also affects `get_current_price_cached()` in `cached_stock_data.py` (line 108).

### 1. Fix the VTI pricing bug (1 hour)
- [ ] In `main.py:_get_stock_stats()` (line 42-54), the `mean_price` is computed as `df['Close'].mean()` — this is the **adjusted** 2-year historical mean. This is mathematically correct but **semantically misleading** for portfolio allocation. The "mean price" shown to the user should be from a relevant recent window, not the entire 2y split-adjusted history.
  - **Option A**: Use only the last 30-90 days for the `mean_price` calculation to reduce the impact of distant, heavily-adjusted prices.
  - **Option B**: Use `current_price` (the most recent close) for share allocation instead of `mean_price`.
  - **Recommended**: Option A — change `df['Close'].mean()` to `df['Close'].tail(90).mean()` and rename the column label from "Mean Price (2y)" to "Mean Price (90d)" in `app.py` line 90.
- [ ] In `cached_stock_data.py:_fetch_stock_data()` (line 67), explicitly pass `auto_adjust=True` to `yf.download()` so behavior doesn't change with yfinance version upgrades.
- [ ] Add a validation check: if `abs(mean_price - current_price) / current_price > 0.5` (50% difference), log a warning. This catches split-related anomalies immediately.

### 2. Harden the cache key (30 mins)
- [ ] In `cached_stock_data.py` (line 29), the cache key is `f"stock_data:{stock}:{startdate}:{enddate}:{period_str}:{interval_str}"`.  
  Add the yfinance version and `auto_adjust` setting to prevent silent cache corruption:
  ```python
  import yfinance as yf
  cache_key = f"stock_data:v{yf.__version__}:{stock}:{startdate}:{enddate}:{period_str}:{interval_str}:adj=True"
  ```
- [ ] Add equivalent versioning to `current_price` and `sector` cache keys.

### 3. Add cache diagnostics to the UI (30 mins)
- [ ] In `app.py`'s "Cache Management" sidebar expander (line 33-41), add:
  - Display the oldest cached entry timestamp (so the user can tell if data is hours old).
  - A "Force Refresh" checkbox that passes `use_cache=False` to the fetch functions.
  - Display total cache size on disk.

### 4. Add a rate-limit safeguard (30 mins)
- [ ] In `parallel_processing.py`, between parallel API calls, add a small sleep (100-200ms) to prevent yfinance rate limiting when running 10+ parallel threads. The retry decorator in `decorators.py` handles retries, but proactively throttling is better.
- [ ] Log the total number of API calls made per session for observability.

## Files Affected
- `main.py` (lines 42-54): Mean price calculation
- `cached_stock_data.py` (lines 29, 67): Cache key + yf.download params
- `app.py` (lines 33-41, 90): UI labels + cache diagnostics
- `parallel_processing.py` (lines 27-43): Rate throttling

## Success Criteria
- ✅ VTI "Mean Price" column shows a value within 30% of the current market price
- ✅ Cache keys include yfinance version to prevent silent corruption
- ✅ "Cache Management" sidebar shows the age of cached data
- ✅ Running `python .agent/scripts/agent_linter.py .` reports no new violations

## Dependencies
- None (standalone — can run in parallel with Task 09, 11, 12)

## Testing
- Run the Portfolio Generator with $5000 and verify VTI/SPY prices are reasonable
- Clear cache, regenerate, and verify fresh data is fetched  
- Use `agent-browser` to visually verify the cache sidebar shows timestamps
