# Task 12: Code Quality Sweep (Golden Principles Enforcement)

## Overview
Run the structural linter across the entire codebase and systematically fix all violations to bring the project into compliance with `.agent/GOLDEN_PRINCIPLES.md`. This is pure refactoring — no feature changes.

## Priority
**Medium** — Required for agents to operate cleanly on the codebase going forward.

## Estimated Effort  
2-3 hours

## Implementation Steps

### 1. Run the linter to get the full violation list (10 mins)
- [ ] Run: `.venv/bin/python .agent/scripts/agent_linter.py .`
- [ ] Capture the full output and use it as the work checklist

### 2. Replace all `print()` statements with structured logging (1 hour)
Known locations:
- [ ] `constants.py` (lines 8, 14, 29): Replace with `logger.error()` and `logger.warning()`
- [ ] `main.py` (lines 19, 92-98, 106-119, 122): Replace with `logger.info()` / `logger.debug()`
- [ ] `io_utils.py` (line 27, 34): `sys.stdout.write()` calls in `query_yes_no` — these are interactive prompts, acceptable to leave in CLI mode but add a note
- [ ] Any `print()` in test files and scripts — exclude `.agent/scripts/` from this rule (those are agent-facing stdout tools)

### 3. Fix bare `except Exception:` blocks (45 mins)
Known locations from code review:
- [ ] `app.py` (lines 109, 210, 270): Replace `except Exception as e:` with specific exceptions from `exceptions.py`
- [ ] `cached_stock_data.py` (lines 79, 110): Already partially addressed — verify all paths use custom exceptions
- [ ] `persistent_cache.py` (lines 43, 63, 86-91): Catches broad exceptions during pickle operations — narrow to `(pickle.PickleError, EOFError, OSError)`
- [ ] `conftest.py` (lines 81, 208, 266, 298): Test infrastructure — mark as acceptable with `# noqa: golden-principles` comment

### 4. Add type hints to uncovered public functions (45 mins)
Priority functions missing hints:
- [ ] `stock_utils.py:get_stock_data()` — add return type `pd.DataFrame`
- [ ] `stock_utils.py:ma_strategy()` — add `(df: pd.DataFrame, short_MA: int, long_MA: int) -> pd.DataFrame`
- [ ] `stock_utils.py:buy_sell_signals()` — add full signature
- [ ] `stock_utils.py:backtest()` — add full signature  
- [ ] `stock_utils.py:RSI()` — add `(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]`
- [ ] `io_utils.py` — all plotting functions

### 5. Re-run linter and update QUALITY.md (15 mins)
- [ ] Run the linter again and confirm zero violations (excluding `.agent/scripts/` and test files)
- [ ] Update `.agent/QUALITY.md` with new grades reflecting the cleanup

## Files Affected
- `constants.py`, `main.py`, `io_utils.py` — print replacement
- `app.py`, `cached_stock_data.py`, `persistent_cache.py` — exception narrowing
- `stock_utils.py`, `io_utils.py` — type hints
- `.agent/QUALITY.md` — grade updates

## Success Criteria
- ✅ `.venv/bin/python .agent/scripts/agent_linter.py .` returns **0 failures** (excluding agent scripts)
- ✅ All public functions in `stock_utils.py` have type hints
- ✅ No bare `except Exception:` in production code
- ✅ All existing tests still pass

## Dependencies
- None (standalone — can run in parallel with Task 09, 10, 11)

## Testing
- Run `pytest tests/` after ALL changes to verify no regressions
- Run the agent linter for automated validation
