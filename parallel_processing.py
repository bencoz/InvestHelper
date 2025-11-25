from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict
import logging

logger = logging.getLogger(__name__)

def fetch_multiple_stocks_parallel(
    symbols: List[str],
    fetch_func: Callable,
    max_workers: int = 5,
    **kwargs
) -> List[Any]:
    """
    Fetch data for multiple stocks in parallel.
    
    Args:
        symbols: List of stock ticker symbols
        fetch_func: Function to call for each symbol
        max_workers: Maximum number of parallel threads
        **kwargs: Additional arguments to pass to fetch_func
        
    Returns:
        List of results in same order as symbols
    """
    results = [None] * len(symbols)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(fetch_func, symbol, **kwargs): i
            for i, symbol in enumerate(symbols)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as e:
                logger.error(f"Error fetching {symbols[index]}: {e}")
                results[index] = None
    
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
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                results[symbol] = None
    
    return results
