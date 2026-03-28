# InvestHelper Module Quality Tracker

This document is continuously updated by the `.github/workflows/garbage_collector.yml` workflow to reflect the health of the repository against the `GOLDEN_PRINCIPLES.md`.

## 📊 Overarching Score: B
_Last updated: 2026-03-28_

Agents should refer to this document before editing a module to understand its pre-existing technical debt.

### Modules

| Module                 | Grade | Compliance Notes                                                                                                      | Focus Area for Refactoring               |
|------------------------|-------|------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `app.py`               | C     | Extremely large file (19k bytes). Likely mixes routing logic with business logic. Error boundaries improved.   | Needs splitting into smaller components. |
| `stock_utils.py`       | B+    | Good functionality, but functions are long and docstrings are occasionally sparse.                                     | Break down long functions.                 |
| `io_utils.py`          | A     | Clean separation of concerns, mostly focused purely on layout/plotting.                                                | None.|
| `exceptions.py`        | A     | Well-defined foundation for custom exceptions.                                                                         | Increase usage across the app.           |
| `logging_config.py`    | A     | Strong observability foundation.                                                                                       | Enforce usage across the `app.py`.       |
| `cached_stock_data.py` | B+    | Caching logic is functional. Exceptions scoped properly.                                     | Unify caching mechanisms.                |

## 🧹 Garbage Collection Targets
1. `app.py` (Urgent: Refactor logic into separate agents/controllers).
