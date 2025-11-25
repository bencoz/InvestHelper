# Task 06: Testing Enhancements

## Overview
Expand test coverage, add integration tests, and implement automated testing best practices.

## Priority
**Medium-High** - Good test coverage ensures reliability and enables confident refactoring.

## Estimated Effort
4-5 hours

## Current State

### Existing Tests
- ✅ Unit tests in `test_stock_utils.py` and `test_io_utils.py`
- ✅ E2E tests using Playwright in `tests/e2e/`
- ❌ No mocking of external APIs
- ❌ Limited edge case coverage
- ❌ No performance tests
- ❌ No integration tests

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │  E2E Tests  │  ← Few, slow, high confidence
        │   (5-10%)   │     Test user workflows
        └─────────────┘
       ┌───────────────┐
       │ Integration   │  ← Some, medium speed
       │  Tests (15%)  │    Test component interaction
       └───────────────┘
     ┌───────────────────┐
     │   Unit Tests      │  ← Many, fast, specific
     │     (75%)         │    Test individual functions
     └───────────────────┘
```

## Improvements Needed

### 1. Mock External API Calls

#### Problem
Current tests make real API calls to yfinance, making them:
- Slow
- Unreliable (network dependent)
- Subject to rate limits
- Non-deterministic

#### Solution

```python
# tests/conftest.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

@pytest.fixture
def mock_stock_data():
    """Generate realistic mock stock data."""
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    
    # Generate synthetic price data
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates)),
        'date': dates.date
    })
    
    return df

@pytest.fixture
def mock_yfinance(mock_stock_data):
    """Mock yfinance download function."""
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = mock_stock_data
        yield mock_download

@pytest.fixture
def mock_ticker_info():
    """Mock yfinance Ticker.info property."""
    return {
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'marketCap': 2500000000000,
        'fiftyTwoWeekHigh': 180.0,
        'fiftyTwoWeekLow': 120.0
    }

@pytest.fixture
def mock_ticker(mock_stock_data, mock_ticker_info):
    """Mock yfinance Ticker object."""
    mock = Mock()
    mock.history.return_value = mock_stock_data
    mock.info = mock_ticker_info
    return mock

@pytest.fixture(autouse=True)
def mock_all_yfinance(mock_yfinance, mock_ticker):
    """Auto-use fixture to mock all yfinance calls."""
    with patch('yfinance.Ticker', return_value=mock_ticker):
        yield
```

#### Update Test Files

```python
# tests/test_stock_utils.py (enhanced)
import pytest
import pandas as pd
from stock_utils import get_stock_data, ma_strategy, backtest, calculate_diversification_score

class TestStockData:
    """Test suite for stock data fetching."""
    
    def test_get_stock_data_success(self, mock_yfinance):
        """Test successful stock data fetch."""
        df = get_stock_data('AAPL', '2020-01-01', '2023-12-31', None, '1d')
        
        assert not df.empty
        assert 'Date' in df.columns
        assert 'Close' in df.columns
        assert len(df) > 0
        mock_yfinance.assert_called_once()
    
    def test_get_stock_data_invalid_ticker(self, mock_yfinance):
        """Test handling of invalid ticker."""
        mock_yfinance.return_value = pd.DataFrame()  # Empty dataframe
        
        df = get_stock_data('INVALID', '2020-01-01', '2023-12-31', None, '1d')
        
        assert df.empty
    
    def test_get_stock_data_missing_date_column(self, mock_yfinance):
        """Test handling of missing date column."""
        # Return dataframe without proper date column
        bad_df = pd.DataFrame({
            'Close': [100, 101, 102],
            'Volume': [1000, 1100, 1200]
        })
        mock_yfinance.return_value = bad_df
        
        df = get_stock_data('AAPL', '2020-01-01', '2023-12-31', None, '1d')
        
        assert df.empty  # Should return empty due to missing date

class TestMovingAverageStrategy:
    """Test suite for MA trading strategy."""
    
    def test_ma_strategy_calculates_indicators(self, mock_stock_data):
        """Test MA strategy adds correct columns."""
        df = ma_strategy(mock_stock_data.copy(), short_MA=50, long_MA=200)
        
        assert 'long_MA' in df.columns
        assert 'short_MA' in df.columns
        assert 'crosszero' in df.columns
        assert 'position' in df.columns
    
    def test_ma_strategy_buy_signals(self, mock_stock_data):
        """Test MA strategy generates buy signals."""
        df = ma_strategy(mock_stock_data.copy(), short_MA=20, long_MA=50)
        
        # Check that buy signals exist
        buy_signals = df[df['position'] == 1]
        assert len(buy_signals) > 0
        
        # Verify buy signals occur when short MA crosses above long MA
        for idx in buy_signals.index:
            if idx > 0:
                assert df.loc[idx, 'short_MA'] >= df.loc[idx, 'long_MA']
    
    def test_ma_strategy_sell_signals(self, mock_stock_data):
        """Test MA strategy generates sell signals."""
        df = ma_strategy(mock_stock_data.copy(), short_MA=20, long_MA=50)
        
        # Check that sell signals exist
        sell_signals = df[df['position'] == -1]
        assert len(sell_signals) > 0
    
    def test_ma_strategy_different_periods(self, mock_stock_data):
        """Test MA strategy with various period combinations."""
        for short, long in [(10, 20), (50, 200), (20, 100)]:
            df = ma_strategy(mock_stock_data.copy(), short_MA=short, long_MA=long)
            
            assert not df['short_MA'].isna().all()
            assert not df['long_MA'].isna().all()
            assert df.loc[df.index[long-1]:, 'long_MA'].notna().all()

class TestBacktesting:
    """Test suite for backtesting functionality."""
    
    def test_backtest_wealth_calculation(self, mock_stock_data):
        """Test backtest calculates wealth correctly."""
        df_with_signals = ma_strategy(mock_stock_data.copy(), 50, 200)
        result = backtest(df_with_signals, 'AAPL', '2020-01-01', '2023-12-31', '1000')
        
        assert 'MA_wealth' in result.columns
        assert 'LT_wealth' in result.columns
        assert result['MA_wealth'].dropna().iloc[-1] > 0
        assert result['LT_wealth'].dropna().iloc[-1] > 0
    
    def test_backtest_initial_wealth(self, mock_stock_data):
        """Test backtest respects initial wealth."""
        initial_wealth = 5000
        df_with_signals = ma_strategy(mock_stock_data.copy(), 50, 200)
        result = backtest(df_with_signals, 'AAPL', '2020-01-01', '2023-12-31', str(initial_wealth))
        
        # Buy & Hold wealth should be proportional to price change
        first_price = result['Close'].iloc[0]
        last_price = result['Close'].iloc[-1]
        expected_bh_wealth = initial_wealth * (last_price / first_price)
        
        actual_bh_wealth = result['LT_wealth'].dropna().iloc[-1]
        
        # Allow 1% tolerance for rounding
        assert abs(actual_bh_wealth - expected_bh_wealth) / expected_bh_wealth < 0.01

class TestDiversificationScore:
    """Test suite for portfolio diversification."""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio for testing."""
        return pd.DataFrame({
            'symbol': ['AAPL', 'MSFT', 'JPM', 'XOM', 'JNJ'],
            'Qty': [10, 15, 20, 5, 8]
        })
    
    @pytest.fixture
    def concentrated_portfolio(self):
        """Portfolio concentrated in one sector."""
        return pd.DataFrame({
            'symbol': ['AAPL', 'MSFT', 'GOOGL'],  # All tech
            'Qty': [10, 10, 10]
        })
    
    def test_diversification_score_calculation(self, sample_portfolio, mock_ticker):
        """Test diversification score is calculated."""
        with patch('stock_utils.get_stock_sector', return_value='Technology'):
            with patch('stock_utils.yf.Ticker', return_value=mock_ticker):
                score, df = calculate_diversification_score(sample_portfolio)
                
                assert 0 <= score <= 100
                assert 'sector' in df.columns
                assert 'market_value' in df.columns
    
    def test_concentrated_portfolio_low_score(self, concentrated_portfolio, mock_ticker):
        """Test concentrated portfolio gets lower score."""
        with patch('stock_utils.get_stock_sector', return_value='Technology'):
            with patch('stock_utils.yf.Ticker', return_value=mock_ticker):
                score, _ = calculate_diversification_score(concentrated_portfolio)
                
                # All same sector should give 0 score
                assert score < 20  # Very low diversification
    
    def test_empty_portfolio(self):
        """Test handling of empty portfolio."""
        empty_df = pd.DataFrame({'symbol': [], 'Qty': []})
        score, df = calculate_diversification_score(empty_df)
        
        assert score == 0.0
        assert df.equals(empty_df)
    
    def test_missing_columns(self):
        """Test handling of portfolio with missing columns."""
        bad_df = pd.DataFrame({'ticker': ['AAPL'], 'shares': [10]})
        score, df = calculate_diversification_score(bad_df)
        
        assert score == 0.0

class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_zero_quantity_stocks(self):
        """Test portfolio with zero quantity stocks."""
        portfolio = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT'],
            'Qty': [0, 10]
        })
        
        # Should handle gracefully
        score, df = calculate_diversification_score(portfolio)
        assert score >= 0
    
    def test_negative_prices(self, mock_stock_data):
        """Test handling of negative prices (data error)."""
        mock_stock_data['Close'] = -100
        
        # Should handle or raise appropriate error
        # Implementation dependent
    
    def test_missing_data_points(self, mock_stock_data):
        """Test handling of missing data points."""
        mock_stock_data.loc[100:200, 'Close'] = np.nan
        
        df = ma_strategy(mock_stock_data, 50, 200)
        
        # Should still calculate MA where possible
        assert df['short_MA'].notna().any()
```

### 2. Integration Tests

```python
# tests/test_integration.py
"""Integration tests for multi-component workflows."""

import pytest
import pandas as pd
from main import prepare_stock_selection, fetch_stock_data
from stock_utils import generate_portfolio
from constants import dividend_stocks, growth_stocks, index_funds

class TestPortfolioGenerationIntegration:
    """Test complete portfolio generation workflow."""
    
    @pytest.mark.integration
    def test_complete_portfolio_generation(self):
        """Test full portfolio generation flow."""
        # Step 1: Prepare stock selection
        selected = prepare_stock_selection(
            dividend_investing=True,
            growth_investing=True,
            index_investing=False,
            dividend_stocks=dividend_stocks,
            growth_stocks=growth_stocks,
            index_funds=index_funds
        )
        
        assert len(selected) > 0
        assert set(selected).issubset(set(dividend_stocks + growth_stocks))
        
        # Step 2: Fetch stock data (mocked)
        stock_data = fetch_stock_data(selected, '2y')
        
        assert len(stock_data) > 0
        
        # Step 3: Generate portfolio
        portfolio = generate_portfolio(stock_data, total_budget=10000)
        
        assert len(portfolio) > 0
        
        # Verify budget constraint
        total_cost = sum(shares * mean_price for _, shares, mean_price, _ in portfolio)
        assert total_cost <= 10000
    
    @pytest.mark.integration
    def test_stock_analysis_workflow(self, mock_stock_data):
        """Test complete stock analysis workflow."""
        from stock_utils import ma_strategy, buy_sell_signals, backtest, RSI
        
        # Full analysis pipeline
        df = mock_stock_data
        df_ma = ma_strategy(df.copy(), 50, 200)
        df_signals = buy_sell_signals(df_ma.copy(), 'AAPL', '2020-01-01', '2023-12-31')
        df_backtest = backtest(df_signals.copy(), 'AAPL', '2020-01-01', '2023-12-31', '1000')
        df_rsi, rsi_series = RSI(df_backtest.copy())
        
        # Verify all steps completed
        assert 'MA_wealth' in df_backtest.columns
        assert 'LT_wealth' in df_backtest.columns
        assert 'RSI' in df_rsi.columns
        assert len(rsi_series) > 0

### 3. Performance Tests

```python
# tests/test_performance.py
"""Performance benchmarking tests."""

import pytest
import time
import pandas as pd
from stock_utils import calculate_diversification_score
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """Performance benchmark tests."""
    
    @pytest.mark.performance
    def test_diversification_calculation_speed(self, large_portfolio):
        """Test diversification calculation completes within time limit."""
        start_time = time.time()
        
        score, df = calculate_diversification_score(large_portfolio)
        
        elapsed = time.time() - start_time
        
        # Should complete within 10 seconds for 50 stocks
        assert elapsed < 10.0, f"Took {elapsed:.2f}s, expected <10s"
    
    @pytest.mark.performance
    def test_parallel_vs_sequential(self):
        """Compare parallel vs sequential processing."""
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB'] * 10
        
        # Sequential
        start = time.time()
        for symbol in symbols:
            _ = get_stock_sector_cached(symbol)
        sequential_time = time.time() - start
        
        # Parallel
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            _ = list(executor.map(get_stock_sector_cached, symbols))
        parallel_time = time.time() - start
        
        # Parallel should be at least 2x faster
        assert parallel_time < sequential_time / 2
    
    @pytest.fixture
    def large_portfolio(self):
        """Generate large portfolio for performance testing."""
        return pd.DataFrame({
            'symbol': [f'STOCK{i}' for i in range(50)],
            'Qty': [100] * 50
        })
```

### 4. Fixtures & Test Data

```python
# tests/fixtures/stock_data.py
"""Reusable test data fixtures."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_trending_stock_data(
    start_date: str = '2020-01-01',
    end_date: str = '2023-12-31',
    initial_price: float = 100.0,
    trend: float = 0.1,  # 10% annual growth
    volatility: float = 0.15
) -> pd.DataFrame:
    """
    Generate realistic synthetic stock data with trend and volatility.
    
    Args:
        start_date: Start date string
        end_date: End date string
        initial_price: Starting price
        trend: Annual growth rate (0.1 = 10%)
        volatility: Annual volatility (0.15 = 15%)
        
    Returns:
        DataFrame with OHLCV data
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)
    
    # Generate returns
    daily_return = trend / 252
    daily_vol = volatility / np.sqrt(252)
    
    np.random.seed(42)
    returns = np.random.normal(daily_return, daily_vol, n_days)
    
    # Calculate prices
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * np.random.uniform(0.99, 1.01, n_days),
        'High': prices * np.random.uniform(1.00, 1.03, n_days),
        'Low': prices * np.random.uniform(0.97, 1.00, n_days),
        'Close': prices,
        'Volume': np.random.randint(1000000, 50000000, n_days),
        'date': dates.date
    })
    
    return df
```

## Implementation Steps

### Phase 1: Setup & Mocking (1.5 hours)
- [ ] Update `conftest.py` with comprehensive fixtures
- [ ] Create mock functions for yfinance
- [ ] Add test data generators
- [ ] Configure pytest markers (unit, integration, e2e, performance)

### Phase 2: Expand Unit Tests (2 hours)
- [ ] Add tests for all edge cases
- [ ] Increase coverage to >80%
- [ ] Add parametrized tests
- [ ] Test error conditions

### Phase 3: Integration Tests (1 hour)
- [ ] Create `test_integration.py`
- [ ] Test complete workflows
- [ ] Test component interactions

### Phase 4: Performance Tests (30 mins)
- [ ] Create `test_performance.py`
- [ ] Add benchmark tests
- [ ] Set performance thresholds

### Phase 5: CI/CD (1 hour)
- [ ] Create `.github/workflows/tests.yml`
- [ ] Configure automated testing
- [ ] Add coverage reporting
- [ ] Add badges to README

## Configuration

### pytest.ini (update)
```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (medium speed)
    e2e: End-to-end tests (slow, full app)
    performance: Performance benchmark tests
    slow: Tests that take >1 second

testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage settings
addopts = 
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### GitHub Actions Workflow
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: pytest tests/ -m "not e2e" --cov
    
    - name: Run E2E tests
      run: pytest tests/e2e/ --headed=false
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Success Criteria

- ✅ Test coverage >80%
- ✅ All external API calls mocked in unit tests
- ✅ Integration tests cover main workflows
- ✅ Performance tests establish baselines
- ✅ CI/CD pipeline runs all tests
- ✅ Tests run in <2 minutes (excluding E2E)

## Dependencies

```txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-benchmark>=4.0.0
```

## Related Tasks

- Task 02 (Error Handling) - Test error scenarios
- Task 03 (Performance) - Performance tests validate optimizations

## Notes

- Keep tests fast and focused
- Use fixtures liberally to avoid duplication
- Mock external dependencies
- Test behavior, not implementation
- Maintain tests as code evolves
