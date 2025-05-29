import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import numpy as np

# Assuming stock_utils.py is in the parent directory or accessible via PYTHONPATH
# For local testing, you might need to adjust sys.path or run as a module
# For this environment, it's assumed stock_utils is discoverable.
from stock_utils import calculate_diversification_score, suggest_rebalancing_actions

# Helper function to create mock yfinance Ticker objects based on symbol
def mock_yfinance_ticker_side_effect(ticker_symbol):
    mock_ticker = MagicMock(name=f"TickerMock_{ticker_symbol}")
    
    if ticker_symbol == "AAPL":
        mock_ticker.info = {'sector': 'Technology'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [150.0]})
    elif ticker_symbol == "MSFT":
        mock_ticker.info = {'sector': 'Technology'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [300.0]})
    elif ticker_symbol == "JNJ":
        mock_ticker.info = {'sector': 'Healthcare'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [170.0]})
    elif ticker_symbol == "AMZN": # For equal value, diff sector test
        mock_ticker.info = {'sector': 'Consumer Discretionary'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [100.0]})
    elif ticker_symbol == "GOOG": # For equal value, diff sector test
        mock_ticker.info = {'sector': 'Communication Services'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [100.0]})
    elif ticker_symbol == "UNKNOWN_SECTOR_STOCK":
        mock_ticker.info = {}  # No sector info, should default to 'Unknown'
        mock_ticker.history.return_value = pd.DataFrame({'Close': [50.0]})
    elif ticker_symbol == "PRICE_FAIL_STOCK":
        mock_ticker.info = {'sector': 'Financials'}
        # Simulate yfinance returning empty history DataFrame
        mock_ticker.history.return_value = pd.DataFrame(columns=['Close'])
    elif ticker_symbol == "PRICE_FAIL_STOCK_2":
        mock_ticker.info = {'sector': 'Industrials'}
        mock_ticker.history.return_value = pd.DataFrame(columns=['Close'])
    elif ticker_symbol == "ZERO_QTY_STOCK":
        mock_ticker.info = {'sector': 'Utilities'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [200.0]})
    else: # Default mock for any other ticker, e.g. in concentration test
        mock_ticker.info = {'sector': 'Other'}
        mock_ticker.history.return_value = pd.DataFrame({'Close': [10.0]}) # Low price for concentration test
    return mock_ticker

class TestCalculateDiversificationScore(unittest.TestCase):

    @patch('stock_utils.yf.Ticker')
    def test_empty_portfolio(self, mock_yf_ticker):
        portfolio_df = pd.DataFrame(columns=['symbol', 'Qty'])
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        self.assertEqual(score, 0.0)
        pd.testing.assert_frame_equal(processed_df, portfolio_df)

    @patch('stock_utils.yf.Ticker')
    def test_invalid_portfolio_missing_columns(self, mock_yf_ticker):
        portfolio_df_no_qty = pd.DataFrame({'symbol': ['AAPL']})
        score, processed_df = calculate_diversification_score(portfolio_df_no_qty.copy())
        self.assertEqual(score, 0.0)
        pd.testing.assert_frame_equal(processed_df, portfolio_df_no_qty)

        portfolio_df_no_symbol = pd.DataFrame({'Qty': [10]})
        score, processed_df = calculate_diversification_score(portfolio_df_no_symbol.copy())
        self.assertEqual(score, 0.0)
        pd.testing.assert_frame_equal(processed_df, portfolio_df_no_symbol)

    @patch('stock_utils.yf.Ticker')
    def test_single_stock_portfolio(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        
        portfolio_df = pd.DataFrame({'symbol': ['AAPL'], 'Qty': [10]})
        expected_score = 0.0 # HHI = 1^2 = 1. Score = (1-1)*100 = 0
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)
        self.assertEqual(processed_df.loc[0, 'sector'], 'Technology')
        self.assertAlmostEqual(processed_df.loc[0, 'current_price'], 150.0)
        self.assertAlmostEqual(processed_df.loc[0, 'market_value'], 1500.0)

    @patch('stock_utils.yf.Ticker')
    def test_perfectly_diversified_portfolio_two_stocks_equal_value_different_sectors(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        # AMZN: Consumer Discretionary, $100
        # GOOG: Communication Services, $100
        portfolio_df = pd.DataFrame({
            'symbol': ['AMZN', 'GOOG'],
            'Qty': [1, 1] # 1 share each, $100 each = $100 market value each
        })
        # Sector AMZN: 100 (50%), Sector GOOG: 100 (50%)
        # HHI = (0.5^2) + (0.5^2) = 0.25 + 0.25 = 0.5
        # Score = (1 - 0.5) * 100 = 50.0
        expected_score = 50.0
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)
        self.assertEqual(processed_df.loc[processed_df['symbol'] == 'AMZN', 'sector'].iloc[0], 'Consumer Discretionary')
        self.assertEqual(processed_df.loc[processed_df['symbol'] == 'GOOG', 'sector'].iloc[0], 'Communication Services')
        self.assertAlmostEqual(processed_df.loc[processed_df['symbol'] == 'AMZN', 'market_value'].iloc[0], 100.0)
        self.assertAlmostEqual(processed_df.loc[processed_df['symbol'] == 'GOOG', 'market_value'].iloc[0], 100.0)


    @patch('stock_utils.yf.Ticker')
    def test_poorly_diversified_portfolio_heavy_concentration(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        # AAPL: Tech, $150
        # MSFT: Tech, $300
        # JNJ: Healthcare, $170
        portfolio_df = pd.DataFrame({
            'symbol': ['AAPL', 'MSFT', 'JNJ'],
            'Qty': [10, 5, 1] 
        })
        # Market Values:
        # AAPL (Tech): 10 * 150 = 1500
        # MSFT (Tech): 5 * 300 = 1500
        # JNJ (Healthcare): 1 * 170 = 170
        # Total Tech = 3000. Total Healthcare = 170. Total Portfolio = 3170.
        # Weights: Tech = 3000/3170, Healthcare = 170/3170
        weight_tech = 3000 / 3170
        weight_healthcare = 170 / 3170
        expected_hhi = (weight_tech**2) + (weight_healthcare**2)
        expected_score = (1 - expected_hhi) * 100
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)

    @patch('stock_utils.yf.Ticker')
    def test_portfolio_with_unknown_sector(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        # AAPL: Tech, $150
        # UNKNOWN_SECTOR_STOCK: 'Unknown' sector, $50
        portfolio_df = pd.DataFrame({
            'symbol': ['AAPL', 'UNKNOWN_SECTOR_STOCK'],
            'Qty': [1, 1]
        })
        # Market Values: AAPL (Tech) $150, UNKNOWN_SECTOR_STOCK (Unknown) $50. Total $200.
        # Weights: Tech = 150/200 = 0.75. Unknown = 50/200 = 0.25
        # HHI = (0.75^2) + (0.25^2) = 0.5625 + 0.0625 = 0.625
        # Score = (1 - 0.625) * 100 = 37.5
        expected_score = 37.5
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)
        self.assertEqual(processed_df.loc[processed_df['symbol'] == 'UNKNOWN_SECTOR_STOCK', 'sector'].iloc[0], 'Unknown')

    @patch('stock_utils.yf.Ticker')
    def test_portfolio_with_price_fetch_failure_one_stock(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        # AAPL: Tech, $150
        # PRICE_FAIL_STOCK: Financials, price fetch fails (empty history)
        portfolio_df = pd.DataFrame({
            'symbol': ['AAPL', 'PRICE_FAIL_STOCK'],
            'Qty': [1, 100] # Qty for PRICE_FAIL_STOCK doesn't matter as it will be dropped
        })
        # Effectively a single stock portfolio of AAPL.
        # HHI = 1^2 = 1. Score = (1-1)*100 = 0.0
        expected_score = 0.0
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)
        # Check that PRICE_FAIL_STOCK is not in the processed_df for market_value calculation
        # (it might be there with NaN price/value before final dropna in calculate_diversification_score)
        # The returned df from calculate_diversification_score should have dropped it if price was NaN.
        # The current implementation of calculate_diversification_score returns the original df if all price fetches fail
        # or if the df becomes empty after dropping NaNs. If only one fails, the stock with NaN price is dropped.
        self.assertTrue('PRICE_FAIL_STOCK' not in processed_df['symbol'].tolist() or
                        pd.isna(processed_df.loc[processed_df['symbol'] == 'PRICE_FAIL_STOCK', 'current_price'].iloc[0]) or
                        processed_df.loc[processed_df['symbol'] == 'PRICE_FAIL_STOCK'].empty)


    @patch('stock_utils.yf.Ticker')
    def test_portfolio_all_price_fetch_failures(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        original_df = pd.DataFrame({
            'symbol': ['PRICE_FAIL_STOCK', 'PRICE_FAIL_STOCK_2'],
            'Qty': [1, 1]
        })
        expected_score = 0.0
        
        score, processed_df = calculate_diversification_score(original_df.copy())
        
        self.assertEqual(score, expected_score)
        # In this case, processed_df returned by the function will be the original_df
        # because it fails early (after failing to get any prices and df becomes empty after internal dropna)
        pd.testing.assert_frame_equal(processed_df, original_df, check_dtype=False, check_like=True)


    @patch('stock_utils.yf.Ticker')
    def test_portfolio_with_zero_quantity_stocks(self, mock_yf_ticker):
        mock_yf_ticker.side_effect = mock_yfinance_ticker_side_effect
        # AAPL: Tech, $150
        # ZERO_QTY_STOCK: Utilities, $200
        portfolio_df = pd.DataFrame({
            'symbol': ['AAPL', 'ZERO_QTY_STOCK'],
            'Qty': [10, 0] # ZERO_QTY_STOCK has 0 quantity
        })
        # Effectively a single stock portfolio of AAPL (market value for ZERO_QTY_STOCK is 0).
        # HHI = 1^2 = 1. Score = (1-1)*100 = 0.0
        expected_score = 0.0
        
        score, processed_df = calculate_diversification_score(portfolio_df.copy())
        
        self.assertAlmostEqual(score, expected_score, places=2)
        # ZERO_QTY_STOCK will have market_value 0.
        # The HHI calculation should only consider stocks with market_value > 0 implicitly if weights are based on sum.
        # If ZERO_QTY_STOCK has 0 market value, its weight is 0, so it doesn't affect HHI.
        self.assertEqual(processed_df.loc[processed_df['symbol'] == 'AAPL', 'market_value'].iloc[0], 1500)
        self.assertEqual(processed_df.loc[processed_df['symbol'] == 'ZERO_QTY_STOCK', 'market_value'].iloc[0], 0)
        self.assertEqual(len(processed_df), 2) # Should still contain ZERO_QTY_STOCK


class TestSuggestRebalancingActions(unittest.TestCase):

    def test_insufficient_data_empty_df(self):
        portfolio_df = pd.DataFrame(columns=['symbol', 'Qty', 'sector', 'market_value'])
        suggestions = suggest_rebalancing_actions(portfolio_df, 50.0)
        self.assertIn("Portfolio data is insufficient", suggestions[0])

    def test_insufficient_data_missing_columns(self):
        # Missing 'market_value'
        portfolio_df = pd.DataFrame({
            'symbol': ['AAPL'], 
            'Qty': [1], 
            'sector': ['Technology']
        })
        suggestions = suggest_rebalancing_actions(portfolio_df, 50.0)
        self.assertIn("Portfolio data is insufficient", suggestions[0])

        # Missing 'sector'
        portfolio_df_no_sector = pd.DataFrame({
            'symbol': ['AAPL'], 
            'Qty': [1], 
            'market_value': [150]
        })
        suggestions = suggest_rebalancing_actions(portfolio_df_no_sector, 50.0)
        self.assertIn("Portfolio data is insufficient", suggestions[0])

    def test_well_diversified_portfolio(self):
        portfolio_df = pd.DataFrame({
            'symbol': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'Qty': [1, 1, 1, 1, 1],
            'sector': ['Tech', 'Health', 'Finance', 'Consumer', 'Industrials'],
            'market_value': [1000, 1000, 1000, 1000, 1000] # Equal distribution
        })
        # For this df, HHI = 5 * (0.2^2) = 5 * 0.04 = 0.2. Score = (1-0.2)*100 = 80
        suggestions = suggest_rebalancing_actions(portfolio_df, 85.0) # Score is manually set high
        self.assertIn("Your portfolio is well-diversified", suggestions[0])
        self.assertIn("ensure your portfolio aligns", suggestions[-1]) # Generic advice

    def test_low_score_over_concentration(self):
        portfolio_df = pd.DataFrame({
            'symbol': ['S1', 'S2', 'S3'],
            'Qty': [8, 1, 1],
            'sector': ['Tech', 'Tech', 'Health'],
            'market_value': [800, 200, 100] # Tech: 1000 (90.9%), Health: 100 (9.1%)
        }) # Total MV = 1100. Tech MV = 1000. Health MV = 100
           # Tech weight = 1000/1100 = 0.909. Health weight = 100/1100 = 0.091
           # HHI = 0.909^2 + 0.091^2 = ~0.826 + ~0.008 = ~0.834
           # Score = (1 - 0.834) * 100 = ~16.6
        suggestions = suggest_rebalancing_actions(portfolio_df, 16.6)
        
        self.assertTrue(any("Consider reducing exposure to the 'Tech' sector" in s for s in suggestions))
        self.assertTrue(any("Consider diversifying by adding investments in sectors like" in s for s in suggestions))
        self.assertIn("ensure your portfolio aligns", suggestions[-1])

    def test_low_score_too_few_stocks(self):
        # 2 stocks, different sectors, equal value. Score would be 50 (decent)
        # but stock count is low (LOW_STOCK_COUNT_THRESHOLD is 5 in function)
        portfolio_df = pd.DataFrame({
            'symbol': ['S1', 'S2'],
            'Qty': [1, 1],
            'sector': ['Tech', 'Health'],
            'market_value': [500, 500]
        })
        suggestions = suggest_rebalancing_actions(portfolio_df, 50.0) # Score is 50
        
        self.assertTrue(any("Your portfolio has 2 unique positions." in s for s in suggestions))
        # Depending on thresholds, it might also suggest diversifying sectors if score is < DIVERSIFICATION_THRESHOLD_LOW (60)
        # In this case, score 50 is < 60, so it should also suggest adding new sectors
        self.assertTrue(any("Consider diversifying by adding investments in sectors like" in s for s in suggestions))
        self.assertIn("ensure your portfolio aligns", suggestions[-1])

    def test_low_score_few_sectors_not_highly_concentrated_in_one(self):
        # 5 stocks, but only 2 sectors. Score is 50.
        portfolio_df = pd.DataFrame({
            'symbol': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'Qty': [1,1,1,1,1],
            'sector': ['Tech', 'Tech', 'Health', 'Health', 'Health'],
            'market_value': [200, 200, 200, 200, 200] # Tech 400 (40%), Health 600 (60%)
        }) # Tech weight = 0.4, Health weight = 0.6. HHI = 0.4^2 + 0.6^2 = 0.16 + 0.36 = 0.52. Score = 48
        suggestions = suggest_rebalancing_actions(portfolio_df, 48.0)
        
        # Check if it flags the 60% concentration in Health (SECTOR_CONCENTRATION_THRESHOLD is 35%)
        self.assertTrue(any("Consider reducing exposure to the 'Health' sector" in s for s in suggestions))
        # Check if it suggests diversifying into new sectors
        self.assertTrue(any("Consider diversifying by adding investments in sectors like" in s for s in suggestions))
        self.assertIn("ensure your portfolio aligns", suggestions[-1])


    def test_moderate_score_no_specific_issue(self):
        # 6 stocks, 3 sectors, no major concentration, score between LOW (60) and GOOD (80)
        portfolio_df = pd.DataFrame({
            'symbol': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            'Qty': [1]*6,
            'sector': ['Tech', 'Tech', 'Health', 'Health', 'Finance', 'Finance'],
            'market_value': [166.6, 166.6, 166.6, 166.6, 166.6, 166.6] # Each sector ~33.3%
        }) # HHI = 3 * (0.3333^2) = 3 * 0.111 = 0.333. Score = (1-0.333)*100 = 66.7
        suggestions = suggest_rebalancing_actions(portfolio_df, 66.7)
        
        self.assertTrue(any("Your portfolio diversification is moderate." in s for s in suggestions))
        self.assertFalse(any("Consider reducing exposure" in s for s in suggestions)) # Should not flag over-concentration
        self.assertFalse(any("Your portfolio has few unique positions" in s for s in suggestions)) # Stock count is 6
        self.assertIn("ensure your portfolio aligns", suggestions[-1])

    def test_zero_total_market_value(self):
        portfolio_df = pd.DataFrame({
            'symbol': ['S1'],
            'Qty': [0], # Results in 0 market value
            'sector': ['Tech'],
            'market_value': [0]
        })
        suggestions = suggest_rebalancing_actions(portfolio_df, 0.0)
        self.assertIn("Cannot generate suggestions: total portfolio value is zero.", suggestions[0])

if __name__ == '__main__':
    unittest.main()
