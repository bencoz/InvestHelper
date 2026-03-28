from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict
import logging
from exceptions import InvestHelperError
import time
import threading

logger = logging.getLogger(__name__)

# Thread-safe API call counter for observability
_api_call_lock = threading.Lock()
_api_call_count = 0

def _rate_limited_call(fetch_func, symbol, delay_seconds, **kwargs):
    """Wrapper that adds a small delay before the API call to prevent rate limiting."""
    global _api_call_count
    time.sleep(delay_seconds)
    with _api_call_lock:
        _api_call_count += 1
    return fetch_func(symbol, **kwargs)

def fetch_multiple_stocks_parallel(
    symbols: List[str],
    fetch_func: Callable,
    max_workers: int = 5,
    rate_limit_ms: int = 150,
    **kwargs
) -> List[Any]:
    """
    Fetch data for multiple stocks in parallel.
    
    Args:
        symbols: List of stock ticker symbols
        fetch_func: Function to call for each symbol
        max_workers: Maximum number of parallel threads
        rate_limit_ms: Milliseconds delay between submitting API calls (default 150ms)
        **kwargs: Additional arguments to pass to fetch_func
        
    Returns:
        List of results in same order as symbols
    """
    global _api_call_count
    with _api_call_lock:
        _api_call_count = 0
    
    results = [None] * len(symbols)
    delay = rate_limit_ms / 1000.0  # Convert to seconds
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks with staggered delays to avoid rate limiting
        future_to_index = {}
        for i, symbol in enumerate(symbols):
            future = executor.submit(_rate_limited_call, fetch_func, symbol, delay * i, **kwargs)
            future_to_index[future] = i
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except (InvestHelperError, ValueError, KeyError, TypeError, OSError) as e:
                logger.error(f"Error fetching {symbols[index]}: {e}")
                results[index] = None
    
    with _api_call_lock:
        logger.info(f"Parallel fetch complete: {_api_call_count} API calls for {len(symbols)} symbols")
    
    return results

def fetch_multiple_stocks_parallel_dict(
    symbols: List[str],
    fetch_func: Callable,
    max_workers: int = 5,
    **kwargs
) -> Dict[str, Any]:
    """
    Fetch data for multiple stocks in parallel, returning a dictionary.
    
    Args:
        symbols: List of stock ticker symbols
        fetch_func: Function to call for each symbol
        max_workers: Maximum number of parallel threads
        **kwargs: Additional arguments to pass to fetch_func
        
    Returns:
        Dictionary mapping symbol to result
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(fetch_func, symbol, **kwargs): symbol
            for symbol in symbols
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                results[symbol] = future.result()
            except (InvestHelperError, ValueError, KeyError, TypeError, OSError) as e:
                logger.error(f"Error fetching {symbol}: {e}")
                results[symbol] = None
    
    return results
