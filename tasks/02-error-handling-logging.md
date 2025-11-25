# Task 02: Error Handling & Logging

## Overview
Implement comprehensive error handling with proper logging to improve debugging and user experience.

## Priority
**High** - Better error handling improves reliability and user experience significantly.

## Estimated Effort
3-4 hours

## Current Issues

### 1. Generic Exception Handling

#### Problem
Many try-except blocks catch generic `Exception`:
```python
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
```

This masks specific errors and makes debugging difficult.

#### Solution
Implement specific exception handling:

```python
# Create custom exceptions
class InvestHelperError(Exception):
    """Base exception for InvestHelper"""
    pass

class DataFetchError(InvestHelperError):
    """Raised when stock data cannot be fetched"""
    pass

class InvalidTickerError(InvestHelperError):
    """Raised when ticker symbol is invalid"""
    pass

class InsufficientDataError(InvestHelperError):
    """Raised when not enough data for analysis"""
    pass

# Usage in stock_utils.py
def get_stock_data(stock, startdate, enddate, period_str, interval_str):
    try:
        df = yf.download(
            tickers=stock, 
            start=startdate, 
            end=enddate, 
            interval=interval_str, 
            period=period_str, 
            multi_level_index=False
        )
    except HTTPError as e:
        logger.error(f"Network error fetching {stock}: {e}")
        raise DataFetchError(f"Network error for {stock}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching {stock}: {e}")
        raise DataFetchError(f"Failed to fetch {stock}") from e
    
    if df.empty:
        raise InsufficientDataError(f"No data returned for {stock}")
    
    return df
```

### 2. No Retry Logic for API Calls

#### Problem
yfinance API can be flaky. Single failures cause operation to fail completely.

#### Solution
Implement retry decorator with exponential backoff:

```python
from functools import wraps
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
            
            raise last_exception
        return wrapper
    return decorator

# Usage:
@retry_with_backoff(max_retries=3, base_delay=1.0)
def fetch_ticker_data(ticker: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period='1d')
```

### 3. No Centralized Error Logging

#### Problem
Errors are not logged to file for later analysis. Only shown to user in UI.

#### Solution
Implement structured logging to file:

```python
# logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
):
    """
    Configure logging for the application.
    
    Args:
        log_dir: Directory to store log files
        log_level: Minimum logging level
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('investhelper')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / 'investhelper.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Separate error log
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / 'errors.log',
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Initialize in app.py:
logger = setup_logging(log_level="INFO")
```

### 4. Silent Failures

#### Problem
Some operations fail silently (e.g., sector fetch returns "Unknown" without logging).

#### Solution
Log all failures, even when handled:

```python
def get_stock_sector(ticker_symbol: str) -> str:
    """
    Fetches the sector for a given stock ticker symbol.
    
    Args:
        ticker_symbol: The stock ticker symbol
        
    Returns:
        The sector of the stock, or "Unknown" if not available
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        sector = ticker.info.get('sector')
        
        if sector:
            logger.debug(f"Fetched sector for {ticker_symbol}: {sector}")
            return sector
        else:
            logger.warning(f"No sector information available for {ticker_symbol}")
            return "Unknown"
            
    except HTTPError as e:
        logger.warning(f"Network error fetching sector for {ticker_symbol}: {e}")
        return "Unknown"
    except Exception as e:
        logger.error(f"Unexpected error fetching sector for {ticker_symbol}: {e}", 
                    exc_info=True)
        return "Unknown"
```

## Implementation Steps

1. **Create custom exceptions** (30 mins)
   - [ ] Create `exceptions.py` module
   - [ ] Define base exception class
   - [ ] Define specific exceptions for common errors
   - [ ] Add docstrings

2. **Implement logging infrastructure** (1 hour)
   - [ ] Create `logging_config.py`
   - [ ] Implement `setup_logging()` function
   - [ ] Add rotating file handlers
   - [ ] Create separate error log
   - [ ] Add `.gitignore` entry for logs/

3. **Implement retry mechanism** (1 hour)
   - [ ] Create `decorators.py` module
   - [ ] Implement `retry_with_backoff()` decorator
   - [ ] Add configuration for retry parameters
   - [ ] Test with flaky network conditions

4. **Update error handling** (1.5 hours)
   - [ ] Replace generic exceptions in `stock_utils.py`
   - [ ] Replace generic exceptions in `main.py`
   - [ ] Replace generic exceptions in `app.py`
   - [ ] Add logging to all error paths
   - [ ] Use retry decorator for API calls

5. **Update UI error messages** (30 mins)
   - [ ] Create user-friendly error messages
   - [ ] Map technical errors to user messages
   - [ ] Add suggestions for common errors

## File Structure

```
/Users/bencohen/Projects/python/InvestHelper/
├── exceptions.py          # Custom exception classes
├── logging_config.py      # Logging setup
├── decorators.py          # Retry and other decorators
├── logs/                  # Log directory (gitignored)
│   ├── investhelper.log
│   └── errors.log
└── ...
```

## Configuration

Add to `config.json` or create `logging_config.json`:

```json
{
  "logging": {
    "level": "INFO",
    "log_to_file": true,
    "log_to_console": true,
    "log_dir": "logs",
    "max_file_size_mb": 10,
    "backup_count": 5
  },
  "retry": {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 10.0
  }
}
```

## Testing Requirements

- [ ] Test each custom exception is raised correctly
- [ ] Test retry logic with mocked failures
- [ ] Test logging to file and console
- [ ] Test log rotation
- [ ] Verify error messages are user-friendly in UI

## Success Criteria

- ✅ All API calls have retry logic
- ✅ All errors are logged with appropriate level
- ✅ Custom exceptions used throughout
- ✅ Separate error log created
- ✅ User sees helpful error messages
- ✅ No silent failures

## Dependencies

- Task 01 (Code Quality) - Should ideally be done first
- Python standard library (logging, functools)

## Related Tasks

- Task 03 (Performance) - Retry logic affects performance
- Task 05 (Documentation) - Document error handling patterns

## Notes

- Consider adding Sentry or similar for production error tracking
- Add health check endpoint to monitor API availability
- Consider circuit breaker pattern for repeated failures
- Update `.gitignore` to exclude log files
