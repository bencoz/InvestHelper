# Task 01: Code Quality Improvements

## Overview
Refactor existing code to improve readability, maintainability, and follow Python best practices.

## Priority
**Medium** - These improvements will make the codebase more maintainable but don't affect functionality.

## Estimated Effort
2-3 hours

## Current Issues

### 1. Complex Lambda Functions in `stock_utils.py`

#### Problem
Line 314 contains a complex lambda that:
- Creates `yf.Ticker` object twice (inefficient)
- Has complex conditional logic
- Difficult to debug
- No error handling

```python
# Current (problematic) code:
df['current_price'] = df['symbol'].apply(
    lambda x: yf.Ticker(x).history(period='1d')['Close'].iloc[-1] 
    if yf.Ticker(x).history(period='1d')['Close'].shape[0] > 0 
    else np.nan
)
```

#### Solution
Extract to a proper function with error handling:

```python
def get_current_price(symbol: str) -> float:
    """
    Fetches the current price for a given stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        
    Returns:
        Current closing price, or np.nan if unavailable
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if len(hist) > 0:
            return hist['Close'].iloc[-1]
        return np.nan
    except Exception as e:
        # Log error (will be implemented in Task 02)
        return np.nan

# Usage:
df['current_price'] = df['symbol'].apply(get_current_price)
```

### 2. Print Statements vs Logging

#### Problem
- Multiple commented-out print statements throughout codebase
- `main.py` uses print for output instead of proper logging
- No way to control verbosity in production

#### Files Affected
- `main.py` (lines 93-136)
- `stock_utils.py` (lines 83-100, 122-201)
- `io_utils.py` (potentially)

#### Solution
Replace print statements with proper logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('investhelper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage examples:
logger.debug("Fetching data for tickers: %s", selected_tickers)
logger.info("Portfolio generated successfully with %d stocks", len(portfolio))
logger.warning("Could not fetch data for ticker: %s", ticker)
logger.error("Error in diversification calculation: %s", str(e))
```

### 3. Missing Type Hints

#### Problem
Most functions lack type hints, making it harder to:
- Understand expected input/output types
- Catch type-related bugs early
- Use IDE autocomplete effectively

#### Solution
Add comprehensive type hints to all functions:

```python
from typing import List, Tuple, Optional, Dict
import pandas as pd

def generate_portfolio(
    stock_prices: List[Tuple[str, float, float, float]], 
    total_budget: float, 
    option: str = 'random'
) -> List[Tuple[str, int, float, float]]:
    """
    Generates a stock portfolio based on available stocks and budget.
    
    Args:
        stock_prices: List of tuples (symbol, mean_price, current_price, diff)
        total_budget: Total amount available for investment
        option: Allocation strategy ('random' or 'equal')
        
    Returns:
        List of tuples (symbol, shares, mean_price, current_price)
    """
    # Implementation...
```

### 4. Magic Numbers and Constants

#### Problem
Hard-coded values scattered throughout code:
- `app.py` line 101-103: MA constants, initial wealth
- `stock_utils.py` line 221: RSI period (14)
- Various thresholds in `suggest_rebalancing_actions()`

#### Solution
Create a `config.py` or `constants.py` file:

```python
# constants.py
from typing import Final

# Technical Analysis Parameters
MA_SHORT_PERIOD: Final[int] = 50
MA_LONG_PERIOD: Final[int] = 200
RSI_PERIOD: Final[int] = 14
INITIAL_WEALTH: Final[float] = 1000.0

# Portfolio Analysis Thresholds
DIVERSIFICATION_THRESHOLD_LOW: Final[float] = 60.0
DIVERSIFICATION_THRESHOLD_GOOD: Final[float] = 80.0
SECTOR_CONCENTRATION_THRESHOLD: Final[float] = 35.0
LOW_STOCK_COUNT_THRESHOLD: Final[int] = 5

# Data Fetching
DEFAULT_PERIOD: Final[str] = '2y'
DEFAULT_INTERVAL: Final[str] = '1d'
PRICE_FETCH_TIMEOUT: Final[int] = 30  # seconds
```

## Implementation Steps

1. **Create utility functions** (1 hour)
   - [x] Extract `get_current_price()` function
   - [x] Extract `get_stock_sector()` helper (already exists, but improve)
   - [x] Add proper error handling to all helpers
   - [x] Add docstrings with type hints

2. **Add logging infrastructure** (30 mins)
   - [x] Create `logger.py` module
   - [x] Configure logging with file and console handlers
   - [x] Add log rotation (optional)

3. **Replace print statements** (45 mins)
   - [x] Update `main.py`
   - [x] Update `stock_utils.py`
   - [x] Remove or update commented print statements
   - [x] Update `VERBOSE` flag to use logging levels

4. **Add type hints** (45 mins)
   - [x] Add to all public functions in `stock_utils.py`
   - [x] Add to all public functions in `main.py`
   - [x] Add to `app.py` helper functions
   - [x] Run `mypy` for type checking

5. **Consolidate constants** (30 mins)
   - [x] Move magic numbers to `constants.py`
   - [x] Update all references
   - [x] Document each constant

## Testing Requirements

- [x] All existing tests pass after refactoring
- [x] No functional changes (pure refactoring)
- [x] Type checking passes with `mypy`
- [x] Code coverage maintained or improved

## Success Criteria

- ✅ No lambda functions longer than one simple operation
- ✅ All print statements replaced with logging
- ✅ All public functions have type hints
- ✅ All magic numbers moved to constants
- ✅ Code passes linting (pylint/flake8)

## Dependencies

- None (pure refactoring)

## Related Tasks

- Task 02 (Error Handling) - Will use logging infrastructure
- Task 06 (Testing) - Type hints improve testability

## Notes

- This is a good opportunity to run linters: `pylint`, `flake8`, `black`
- Consider adding pre-commit hooks for code quality
- Document any breaking changes (though there shouldn't be any)
