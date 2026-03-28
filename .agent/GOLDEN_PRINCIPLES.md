# InvestHelper Golden Principles

These rules mechanically define "taste" in the InvestHelper repository. AI code generation and agent reviewers must explicitly adhere to these rules. The custom structural linters validate against them.

## 1. Error Handling Boundaries
- **Rule**: Never use bare `except Exception:`.
- **Reason**: Swallows critical failures and breaks the agent's ability to debug.
- **Enforcement**: Must raise custom exceptions extending `InvestHelperError` (e.g., `DataFetchError`). 

## 2. Structural Logging
- **Rule**: No loose `print()` statements.
- **Reason**: Breaks observability. Logs must be structured for the ephemeral observability stack.
- **Enforcement**: Always import `logging_config` and use `logger.info`, `logger.error`, etc.
 
## 3. Dependency Flow
- **Rule**: UI code must not contain business logic.
- **Reason**: Separating concerns allows specialized agents (like Technical Analyst vs Orchestrator) to operate cleanly on their respective modules.
- **Enforcement**: `app.py` and `main.py` should only call functions in `stock_utils.py`, `research_stock.py`, or `io_utils.py`. `app.py` must not do raw math or direct API calls.

## 4. Legibility and Metrics
- **Rule**: All classes and methods require strict type hints (`typing` module) and descriptive docstrings.
- **Reason**: Agents rely heavily on type signatures to guess implementation intents.
- **Enforcement**: All `.py` files must pass `mypy` strict checks. Maximum file size should ideally not exceed 500 lines to ensure context windows remain uncluttered.
