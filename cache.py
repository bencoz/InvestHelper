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
