import unittest
import sys
import math
# Add the project root to the Python path to allow importing project modules
sys.path.insert(0, sys.path[0] + "/..")
from stock_utils import generate_portfolio

class TestGeneratePortfolio(unittest.TestCase):

    def test_basic_allocation_random(self):
        stock_prices = [
            ("STOCKA", 100.0, 105.0, 5.0), # name, mean_price, current_price, diff
            ("STOCKB", 50.0, 52.0, 2.0),
            ("STOCKC", 200.0, 210.0, 10.0)
        ]
        total_budget = 1000.0
        portfolio = generate_portfolio(stock_prices, total_budget, option='random')

        self.assertTrue(isinstance(portfolio, list))
        allocated_budget = 0
        for stock, shares, mean_price, _ in portfolio:
            self.assertIn(stock, ["STOCKA", "STOCKB", "STOCKC"])
            self.assertIsInstance(shares, int)
            self.assertGreaterEqual(shares, 0)
            allocated_budget += shares * mean_price
        
        self.assertLessEqual(allocated_budget, total_budget)
        # In 'random' mode, it's hard to predict exact shares, but we can check budget constraints.

    def test_basic_allocation_equal(self):
        stock_prices = [
            ("STOCKA", 100.0, 105.0, 5.0),
            ("STOCKB", 50.0, 52.0, 2.0),
            ("STOCKC", 200.0, 210.0, 10.0) # Won't be able to afford if budget is 333 per stock
        ]
        total_budget = 1000.0
        portfolio = generate_portfolio(stock_prices, total_budget, option='equal')
        
        self.assertTrue(isinstance(portfolio, list))
        num_stocks = len(stock_prices)
        expected_budget_per_stock = total_budget // num_stocks # 333.33

        allocated_budget = 0
        shares_for_stock_a = 0
        shares_for_stock_b = 0
        shares_for_stock_c = 0

        for item in portfolio:
            stock_name = item[0]
            shares = item[1]
            mean_price = item[2]
            allocated_budget += shares * mean_price
            if stock_name == "STOCKA":
                shares_for_stock_a = shares
            elif stock_name == "STOCKB":
                shares_for_stock_b = shares
            elif stock_name == "STOCKC":
                shares_for_stock_c = shares
        
        # Expected shares:
        # STOCKA: 333.33 // 100 = 3 shares
        # STOCKB: 333.33 // 50 = 6 shares
        # STOCKC: 333.33 // 200 = 1 share
        self.assertEqual(shares_for_stock_a, 3)
        self.assertEqual(shares_for_stock_b, 6)
        self.assertEqual(shares_for_stock_c, 1)
        
        self.assertLessEqual(allocated_budget, total_budget)
        # Check if the total cost is close to the budget (considering leftover from division)
        self.assertTrue(total_budget - allocated_budget < (100.0 + 50.0 + 200.0)) # Sum of prices

    def test_budget_too_small_for_any_stock(self):
        stock_prices = [
            ("STOCKA", 100.0, 105.0, 5.0),
            ("STOCKB", 50.0, 52.0, 2.0)
        ]
        total_budget = 40.0 # Less than any stock's mean_price
        portfolio_random = generate_portfolio(stock_prices, total_budget, option='random')
        portfolio_equal = generate_portfolio(stock_prices, total_budget, option='equal')

        for stock, shares, _, _ in portfolio_random:
            self.assertEqual(shares, 0)
        for stock, shares, _, _ in portfolio_equal:
            self.assertEqual(shares, 0)
            
        # More robust check: sum of shares should be 0
        self.assertEqual(sum(s[1] for s in portfolio_random), 0)
        self.assertEqual(sum(s[1] for s in portfolio_equal), 0)


    def test_empty_stock_prices(self):
        stock_prices = []
        total_budget = 1000.0
        portfolio_random = generate_portfolio(stock_prices, total_budget, option='random')
        portfolio_equal = generate_portfolio(stock_prices, total_budget, option='equal')
        self.assertEqual(portfolio_random, [])
        self.assertEqual(portfolio_equal, [])

    def test_zero_budget(self):
        stock_prices = [
            ("STOCKA", 100.0, 105.0, 5.0),
            ("STOCKB", 50.0, 52.0, 2.0)
        ]
        total_budget = 0.0
        portfolio_random = generate_portfolio(stock_prices, total_budget, option='random')
        portfolio_equal = generate_portfolio(stock_prices, total_budget, option='equal')

        self.assertEqual(sum(s[1] for s in portfolio_random), 0)
        self.assertEqual(sum(s[1] for s in portfolio_equal), 0)

    def test_output_format(self):
        stock_prices = [("STOCKA", 100.0, 105.0, 5.0)]
        total_budget = 150.0
        portfolio = generate_portfolio(stock_prices, total_budget, option='random') # Could be 'equal' too
        
        if portfolio: # It might be empty if random picks 0 shares
            item = portfolio[0]
            self.assertEqual(len(item), 4)
            self.assertIsInstance(item[0], str)  # stock name
            self.assertIsInstance(item[1], int)  # shares
            self.assertIsInstance(item[2], float) # mean_price
            self.assertIsInstance(item[3], float) # current_price

    def test_allocation_with_nan_diff(self):
        # generate_portfolio sorts by diff for 'random', ensure NaN is handled
        stock_prices = [
            ("STOCKA", 100.0, 105.0, 5.0),
            ("STOCKB", 50.0, 52.0, math.nan), # NaN diff
            ("STOCKC", 200.0, 210.0, 10.0)
        ]
        total_budget = 1000.0
        # Test with 'random' as it sorts by diff
        portfolio_random = generate_portfolio(stock_prices, total_budget, option='random')
        
        allocated_budget_random = 0
        has_stock_b_random = False
        for stock, shares, mean_price, _ in portfolio_random:
            allocated_budget_random += shares * mean_price
            if stock == "STOCKB" and shares > 0:
                has_stock_b_random = True # STOCKB with NaN diff should be skipped in allocation
        
        self.assertFalse(has_stock_b_random, "Stock with NaN diff should not have shares allocated in 'random' mode.")
        self.assertLessEqual(allocated_budget_random, total_budget)

        # Test with 'equal' - NaN diff should not affect this mode's primary logic
        portfolio_equal = generate_portfolio(stock_prices, total_budget, option='equal')
        allocated_budget_equal = 0
        shares_stock_b_equal = 0
        for stock, shares, mean_price, _ in portfolio_equal:
            allocated_budget_equal += shares * mean_price
            if stock == "STOCKB":
                shares_stock_b_equal = shares # STOCKB should be considered for allocation
        
        # In 'equal' mode, STOCKB (50) with a budget of 1000/3 = 333.33 should get 6 shares.
        # The NaN diff does not directly influence the share calculation in 'equal' mode.
        self.assertEqual(shares_stock_b_equal, 6, "StockB should be allocated shares in 'equal' mode regardless of NaN diff.")
        self.assertLessEqual(allocated_budget_equal, total_budget)


if __name__ == '__main__':
    unittest.main()
