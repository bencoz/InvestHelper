from typing import Optional
import pandas as pd
import yfinance as yf
from cache import stock_cache
from persistent_cache import persistent_cache
import logging
import numpy as np

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
    try:
        df = yf.download(
            tickers=stock,
            start=startdate,
            end=enddate,
            interval=interval_str,
            period=period_str,
            multi_level_index=False,
            progress=False
        )
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {stock}: {e}")
        return pd.DataFrame()

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
