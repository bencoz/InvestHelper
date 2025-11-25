# Task 03: Performance Optimization & Caching

## Overview
Implement caching and optimize data fetching to improve application performance and reduce API calls.

## Priority
**High** - Significantly improves user experience, especially for repeated queries.

## Estimated Effort
4-5 hours

## Current Issues

### 1. Repeated API Calls

#### Problem
- Same stock data fetched multiple times within short periods
- No caching between sessions
- Portfolio analyzer makes sequential API calls (slow for large portfolios)

#### Example
```python
# In calculate_diversification_score - Line 314
df['current_price'] = df['symbol'].apply(
    lambda x: yf.Ticker(x).history(period='1d')['Close'].iloc[-1] ...
)
# This calls yfinance API sequentially for EACH stock
```

### 2. Sequential Processing

#### Problem
Portfolio analyzer processes stocks one-by-one instead of in parallel.

## Solutions

### 1. Implement Multi-Level Caching

#### In-Memory Cache (Fast, Session-Only)
```python
# cache.py
from functools import lru_cache
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, Dict, Any
import threading

class StockDataCache:
    """
    Thread-safe in-memory cache for stock data.
    """
    def __init__(self, ttl_minutes: int = 15):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if still valid."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() - entry['timestamp'] < self.ttl:
                    return entry['data']
                else:
                    # Expired
                    del self._cache[key]
        return None
    
    def set(self, key: str, data: Any) -> None:
        """Cache data with timestamp."""
        with self._lock:
            self._cache[key] = {
                'data': data,
                'timestamp': datetime.now()
            }
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                'entries': len(self._cache),
                'size_mb': self._estimate_size() / (1024 * 1024)
            }
    
    def _estimate_size(self) -> int:
        """Estimate cache size in bytes (rough)."""
        import sys
        return sum(sys.getsizeof(v) for v in self._cache.values())

# Global cache instance
stock_cache = StockDataCache(ttl_minutes=15)
```

#### Persistent File Cache (Survives Restarts)
```python
# persistent_cache.py
import pickle
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import pandas as pd

class PersistentCache:
    """
    File-based cache for stock data that persists between sessions.
    """
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path from key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """Load cached data if still valid."""
        cache_file = self._get_cache_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check expiry
            if datetime.now() - cache_data['timestamp'] < self.ttl:
                return cache_data['data']
            else:
                # Expired, delete file
                cache_file.unlink()
                return None
                
        except (pickle.PickleError, EOFError, KeyError):
            # Corrupted cache, delete
            cache_file.unlink()
            return None
    
    def set(self, key: str, data: Any) -> None:
        """Save data to cache file."""
        cache_file = self._get_cache_path(key)
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'data': data,
                    'timestamp': datetime.now(),
                    'key': key
                }, f)
        except pickle.PickleError as e:
            logger.error(f"Failed to cache {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
    
    def clear_expired(self) -> int:
        """Remove expired cache files. Returns count removed."""
        removed = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                if datetime.now() - cache_data['timestamp'] >= self.ttl:
                    cache_file.unlink()
                    removed += 1
            except:
                # Corrupted, remove it
                cache_file.unlink()
                removed += 1
        return removed

# Global instance
persistent_cache = PersistentCache(ttl_hours=24)
```

### 2. Cached Data Fetching Functions

```python
# cached_stock_data.py
from typing import Optional
import pandas as pd
import yfinance as yf
from cache import stock_cache
from persistent_cache import persistent_cache
import logging

logger = logging.getLogger(__name__)

def get_stock_data_cached(
    stock: str,
    startdate: str,
    enddate: str,
    period_str: Optional[str],
    interval_str: str,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch stock data with two-level caching.
    
    Uses in-memory cache (15 min TTL) for frequently accessed data,
    and disk cache (24 hour TTL) for persistence between sessions.
    """
    # Generate cache key
    cache_key = f"stock_data:{stock}:{startdate}:{enddate}:{period_str}:{interval_str}"
    
    if not use_cache:
        return _fetch_stock_data(stock, startdate, enddate, period_str, interval_str)
    
    # Try in-memory cache first (fastest)
    data = stock_cache.get(cache_key)
    if data is not None:
        logger.debug(f"Cache hit (memory) for {stock}")
        return data
    
    # Try persistent cache
    data = persistent_cache.get(cache_key)
    if data is not None:
        logger.debug(f"Cache hit (disk) for {stock}")
        # Populate memory cache for future requests
        stock_cache.set(cache_key, data)
        return data
    
    # Cache miss - fetch from API
    logger.debug(f"Cache miss for {stock}, fetching from API")
    data = _fetch_stock_data(stock, startdate, enddate, period_str, interval_str)
    
    # Cache the result
    if not data.empty:
        stock_cache.set(cache_key, data)
        persistent_cache.set(cache_key, data)
    
    return data

def _fetch_stock_data(stock, startdate, enddate, period_str, interval_str) -> pd.DataFrame:
    """Internal function to actually fetch data - original implementation."""
    # This is the original get_stock_data logic from stock_utils.py
    df = yf.download(
        tickers=stock,
        start=startdate,
        end=enddate,
        interval=interval_str,
        period=period_str,
        multi_level_index=False
    )
    # ... rest of processing
    return df

def get_current_price_cached(symbol: str, use_cache: bool = True) -> float:
    """Get current stock price with caching."""
    cache_key = f"current_price:{symbol}"
    
    if use_cache:
        price = stock_cache.get(cache_key)
        if price is not None:
            return price
    
    # Fetch from API
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if len(hist) > 0:
            price = hist['Close'].iloc[-1]
            stock_cache.set(cache_key, price)
            return price
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
    
    return np.nan

def get_stock_sector_cached(ticker_symbol: str, use_cache: bool = True) -> str:
    """Get stock sector with caching."""
    cache_key = f"sector:{ticker_symbol}"
    
    if use_cache:
        sector = stock_cache.get(cache_key)
        if sector is not None:
            return sector
    
    # Fetch from API (original logic)
    try:
        ticker = yf.Ticker(ticker_symbol)
        sector = ticker.info.get('sector', 'Unknown')
        if sector:
            stock_cache.set(cache_key, sector)
        return sector
    except Exception as e:
        logger.warning(f"Error fetching sector for {ticker_symbol}: {e}")
        return "Unknown"
```

### 3. Parallel Processing for Portfolio Analysis

```python
# parallel_processing.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any
import pandas as pd
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

# Updated calculate_diversification_score with parallel fetching
def calculate_diversification_score_optimized(portfolio_df: pd.DataFrame):
    """Optimized version with parallel data fetching."""
    if not isinstance(portfolio_df, pd.DataFrame) or portfolio_df.empty:
        return 0.0, portfolio_df
    
    df = portfolio_df.copy()
    symbols = df['symbol'].tolist()
    
    # Fetch sectors in parallel
    logger.info(f"Fetching sector data for {len(symbols)} stocks in parallel")
    sectors = fetch_multiple_stocks_parallel(
        symbols,
        get_stock_sector_cached,
        max_workers=10
    )
    df['sector'] = sectors
    
    # Fetch current prices in parallel
    logger.info(f"Fetching current prices for {len(symbols)} stocks in parallel")
    prices = fetch_multiple_stocks_parallel(
        symbols,
        get_current_price_cached,
        max_workers=10
    )
    df['current_price'] = prices
    
    # Rest of calculation remains the same
    df.dropna(subset=['current_price'], inplace=True)
    # ... continue with diversification calculation
```

### 4. Streamlit Cache Integration

```python
# In app.py
import streamlit as st

# Use Streamlit's built-in caching for app-level data
@st.cache_data(ttl=900)  # 15 minutes
def load_stock_config():
    """Load stock configuration from JSON."""
    with open('config.json', 'r') as f:
        return json.load(f)

@st.cache_data(ttl=3600)  # 1 hour
def get_stock_data_for_display(ticker, start, end):
    """Cached wrapper for stock data in Streamlit."""
    return get_stock_data_cached(ticker, start, end, None, '1d')
```

## Implementation Steps

1. **Create caching infrastructure** (2 hours)
   - [ ] Create `cache.py` with StockDataCache
   - [ ] Create `persistent_cache.py` with PersistentCache
   - [ ] Add `.cache/` to `.gitignore`
   - [ ] Write tests for cache functionality

2. **Create cached data fetching functions** (1 hour)
   - [ ] Create `cached_stock_data.py`
   - [ ] Implement `get_stock_data_cached()`
   - [ ] Implement `get_current_price_cached()`
   - [ ] Implement `get_stock_sector_cached()`

3. **Implement parallel processing** (1.5 hours)
   - [ ] Create `parallel_processing.py`
   - [ ] Implement `fetch_multiple_stocks_parallel()`
   - [ ] Update `calculate_diversification_score()`
   - [ ] Test with various portfolio sizes

4. **Integrate caching** (1 hour)
   - [ ] Update `stock_utils.py` to use cached functions
   - [ ] Update `app.py` to use Streamlit cache
   - [ ] Update `main.py` for CLI usage
   - [ ] Add cache management UI

5. **Add cache management** (30 mins)
   - [ ] Add "Clear Cache" button in Streamlit sidebar
   - [ ] Add cache statistics display
   - [ ] Implement automatic cleanup of expired cache

## Configuration

Add to `config.json`:
```json
{
  "cache": {
    "enabled": true,
    "memory_ttl_minutes": 15,
    "disk_ttl_hours": 24,
    "cache_dir": ".cache",
    "max_cache_size_mb": 100
  },
  "performance": {
    "max_parallel_requests": 10,
    "request_timeout_seconds": 30
  }
}
```

## File Structure

```
/Users/bencohen/Projects/python/InvestHelper/
├── cache.py                  # In-memory cache
├── persistent_cache.py       # Disk cache
├── cached_stock_data.py      # Cached data fetching
├── parallel_processing.py    # Parallel execution utilities
├── .cache/                   # Cache directory (gitignored)
│   └── *.pkl
└── ...
```

## Testing Requirements

- [ ] Test cache hit/miss scenarios
- [ ] Test cache expiration
- [ ] Test parallel fetching vs sequential (performance)
- [ ] Test cache with corrupted data
- [ ] Test memory usage doesn't grow unbounded
- [ ] Benchmark improvement (should be 5-10x faster for cached data)

## Success Criteria

- ✅ Repeated queries return instantly from cache
- ✅ Portfolio analysis 5x faster for large portfolios
- ✅ Cache persists between app restarts
- ✅ Memory usage stays reasonable (<100MB for cache)
- ✅ User has control over cache (clear button)
- ✅ Proper cache invalidation

## Performance Targets

- First load: <5 seconds for 30 stocks
- Cached load: <500ms for 30 stocks
- Portfolio analysis: <10 seconds for 50 stocks (currently ~50s)

## Dependencies

- Task 02 (Logging) - Log cache operations
- Python standard library: `threading`, `pickle`, `concurrent.futures`

## Related Tasks

- Task 01 (Code Quality) - Clean code makes caching easier
- Task 04 (New Features) - Export can include cache status

## Notes

- Consider using Redis for production deployment
- Monitor yfinance API rate limits
- Add cache warming for popular stocks
- Consider implementing cache preloading at startup
- Add metrics for cache hit rate
