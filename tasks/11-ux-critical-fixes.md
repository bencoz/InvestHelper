# Task 11: UX Critical Fixes (Pre-Sellable Polish)

## Overview
Fix the visual and compliance issues identified in the live app audit that block the product from being presented to real users. This is pure UI/UX work — no business logic changes.

## Priority
**High** — Compliance (disclaimers) and visual quality are blockers to any real user exposure.

## Estimated Effort  
2-3 hours

## Implementation Steps

### 1. Add financial disclaimer (30 mins)
- [ ] Add a persistent footer/caption at the bottom of every page in `app.py`:
  ```python
  st.caption("⚠️ This tool is for educational and informational purposes only. It does not constitute financial advice. Investing involves risk of loss.")
  ```
- [ ] Add a more prominent `st.warning()` disclaimer at the top of the Portfolio Generator mode (before any inputs).

### 2. Fix RSI chart x-axis (30 mins)
- [ ] In `io_utils.py:get_rsi_plot()` (line 117), the RSI series `rsi_series.index` is a numeric RangeIndex instead of a DatetimeIndex because `RSI()` in `stock_utils.py` (line 211) returns the original df's numeric index after `change.dropna()`.
- [ ] Fix: In `stock_utils.py:RSI()`, ensure the returned rsi_series shares the DatetimeIndex from the source DataFrame:
  ```python
  rsi = 100 * avg_up / (avg_up + avg_down)
  rsi.index = df['Date'].iloc[rsi.index]  # Map numeric index to dates
  ```
- [ ] Alternatively, in `io_utils.py:get_rsi_plot()`, check if rsi_series has a DatetimeIndex and re-index it from `df_with_close_price['Date']` if not.

### 3. Consistent chart rendering (45 mins)
- [ ] Currently, Price/MA and RSI charts use `matplotlib` (static), but the Wealth chart is rendered via `st.pyplot()`. All charts should use the same library.
- [ ] **Preferred approach**: Keep matplotlib for all charts (simpler, less dependency). Just ensure all 4 charts use the same figure sizing and font styling for consistency.
- [ ] Set a consistent color palette across all matplotlib charts using `plt.style.use('seaborn-v0_8-darkgrid')` or similar.

### 4. Hide "Cache Management" from end users (15 mins)
- [ ] Wrap the "Cache Management" sidebar section in a check:
  ```python
  if st.sidebar.checkbox("Developer Mode", value=False, key="dev_mode"):
      with st.sidebar.expander("Cache Management"):
          # ... existing code
  ```

### 5. Add CSV template download to Portfolio Analyzer (30 mins)
- [ ] Before the file uploader in Portfolio Analyzer mode, add a downloadable sample CSV:
  ```python
  sample_csv = "symbol,Qty\nAAPL,10\nMSFT,5\nGOOG,8\nVTI,20\n"
  st.download_button("📥 Download Sample CSV Template", sample_csv, "portfolio_template.csv", "text/csv")
  ```

### 6. Brand consistency (15 mins)
- [ ] Change `st.title("AI Stock Research Assistant")` to `st.title("InvestHelper")` with a subtitle:
  ```python
  st.title("InvestHelper")
  st.caption("AI-Powered Stock Research & Portfolio Management")
  ```

## Files Affected
- `app.py`: Disclaimer, brand title, cache section hiding, CSV template download
- `io_utils.py` (line 117): RSI chart x-axis fix
- `stock_utils.py` (line 211-229): RSI DatetimeIndex propagation

## Success Criteria
- ✅ Financial disclaimer visible on every page load
- ✅ RSI chart shows dates on x-axis, not numbers
- ✅ All 4 charts use consistent styling
- ✅ "Cache Management" hidden behind "Developer Mode" toggle
- ✅ Portfolio Analyzer shows a downloadable CSV template
- ✅ Title says "InvestHelper" consistently

## Dependencies
- None (standalone — can run in parallel with Task 09, 10, 12)

## Testing
- Use `agent-browser` to snapshot each mode and visually verify all fixes
- Run existing e2e tests to confirm no regressions
