# InvestHelper - Task Overview

This directory contains detailed specifications for improvement tasks.

## 🚨 Adversarial Agent Review Results (Tasks 09-12)

A parallel agent dispatch was executed for tasks 09, 10, 11, and 12. Below is the critical, adversarial review of their work:

**Task 09 (Skills Migration) - Grade: B**
* **Success**: Restructured old flat `.md` files into the `agentskills.io` standard format with `scripts/` directories.
* **Failure**: The newly written `sentiment_analyst` and `technical_analyst` scripts contain massive amounts of `print()` statements, which subsequently caused 134 structural linter failures.

**Task 10 (Data Integrity) - Grade: F (Critical Failure)**
* **Success**: Fixed pandas Series ambiguity crash. Updated UI metric labels to say "Mean Price (90d)".
* **Failure**: **"Lipstick on a pig" bug**. The agent changed the text to say 90-day mean, but the calculation in `main.py` is STILL `df['Close'].mean()` (the 2y historical mean). It completely failed to do the math accurately. 
* **Failure**: Did not harden `cached_stock_data.py` cache keys with `yf.__version__` or `auto_adjust=True`.

**Task 11 (UX & Compliance) - Grade: C**
* **Success**: Updated title branding to "InvestHelper", added the CSV template download for Portfolio Analyzer, and wrapped cache management in developer mode.
* **Failure**: **Failed Compliance Requirements**. The agent completely ignored adding the persistent financial disclaimer to the footer.
* **Failure**: Failed to implement the RSI chart x-axis date rendering fix in `stock_utils.py`.

**Task 12 (Code Quality Sweep) - Grade: C**
* **Success**: Addressed existing bare exceptions (`except Exception:`) across the app, replaced top-level `print`s with logging, and successfully type-hinted core stock utilities.
* **Failure**: Failed to ensure the linter passed (still 130+ violations) because it didn't update the linter script to exclude the `.agent/skills/` tool outputs.

---

## 🚀 Next Immediate Steps (Remediation Tasks)

The following fix-up tasks must be executed to correct the agent failures.

### Critical Remediation

**[Task 13: Fix 90d Calculation and Cache Hardening](13-data-and-caching-fixes.md)** - 1 hour
   - Fix the `mean_price` calculation in `main.py` explicitly to use `.tail(90).mean()`.
   - Update `cached_stock_data.py` cache keys to include `auto_adjust=True` and `yf.__version__`.

**[Task 14: Compliance, Charts, and Linting](14-compliance-and-linter.md)** - 1-2 hours
   - Add financial advice disclaimers at the bottom of the Streamlit UI in `app.py`.
   - Fix the RSI chart date axis by propagating the DateTimeIndex from the target DataFrame.
   - Update `.agent/scripts/agent_linter.py` to explicitly ignore `.agent/skills/` directories, allowing agent skill scripts to use `print()` for returning unstructured string data.

---

### Previous Tasks (Foundation — Partially Complete)


1. ✅ **[Task 02: Error Handling & Logging](02-error-handling-logging.md)** - 3-4 hours
   - Improve reliability and debugging
   - Add comprehensive error handling
   - Implement structured logging

2. **[Task 03: Performance & Caching](03-performance-caching.md)** - 4-5 hours
   - Add multi-level caching
   - Implement parallel processing
   - Significant speed improvements

### Medium Priority
3. ✅ **[Task 01: Code Quality](01-code-quality-improvements.md)** - 2-3 hours
   - Refactor complex code
   - Add type hints
   - Replace print with logging

4. **[Task 04: New Features](04-new-features.md)** - 8-10 hours
   - Export functionality
   - Stock comparison
   - Additional technical indicators

5. **[Task 05: Documentation](05-documentation.md)** - 3-4 hours
   - Complete docstrings
   - Architecture documentation
   - User guide

6. **[Task 06: Testing](06-testing-enhancements.md)** - 4-5 hours
   - Mock external APIs
   - Integration tests
   - >80% coverage

7. **[Task 07: Configuration](07-configuration-dependencies.md)** - 2-3 hours
   - Dependency management
   - Configuration system
   - Environment variables

### Low Priority
8. **[Task 08: Deployment](08-deployment-containerization.md)** - 2-3 hours
   - Docker containerization
   - Deployment guides
   - Cloud configs

## Recommended Implementation Order

### Phase 1: Foundation (8-10 hours)
0. Task 09: Agent Skills Standardization (Critical blocking agentic workflow shift)
1. Task 02: Error Handling & Logging
2. Task 01: Code Quality
3. Task 07: Configuration

### Phase 2: Performance (4-5 hours)
4. Task 03: Performance & Caching

### Phase 3: Quality & Testing (7-9 hours)
5. Task 06: Testing
6. Task 05: Documentation

### Phase 4: Features (8-10 hours)
7. Task 04: New Features

### Phase 5: Deployment (2-3 hours)
8. Task 08: Deployment

## Total Estimated Effort
30-40 hours for all tasks

## Quick Wins (Can be done independently)
- Task 07: Configuration (2-3 hours)
- Task 08: Deployment (2-3 hours)
- Parts of Task 01: Code Quality

## Notes
- Tasks can be tackled in any order
- Some tasks have dependencies (noted in each spec)
- Estimated times are for one developer
- Testing should be done incrementally with each task
