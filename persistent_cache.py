import pickle
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

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
                
        except (pickle.PickleError, EOFError, KeyError, OSError) as e:
            # Corrupted cache or other error, delete
            logger.debug(f"Cache read error for key {key}: {e}")
            try:
                if cache_file.exists():
                    cache_file.unlink()
            except OSError:
                pass
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
        except (pickle.PickleError, OSError) as e:
            logger.error(f"Failed to cache {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache files."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except OSError:
                    pass
    
    def clear_expired(self) -> int:
        """Remove expired cache files. Returns count removed."""
        removed = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    if datetime.now() - cache_data['timestamp'] >= self.ttl:
                        cache_file.unlink()
                        removed += 1
                except (pickle.PickleError, EOFError, OSError):
                    # Corrupted, remove it
                    try:
                        cache_file.unlink()
                        removed += 1
                    except OSError:
                        pass
        return removed

# Global instance
persistent_cache = PersistentCache(ttl_hours=24)
