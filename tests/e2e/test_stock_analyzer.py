import pytest
from playwright.sync_api import Page, expect
from datetime import date
from conftest import wait_for_streamlit_load, select_app_mode

@pytest.mark.e2e
class TestStockAnalyzer:
    def test_stock_analyzer_basic_flow(self, page: Page):
        """Test the basic flow of stock analysis."""
        # Select Stock Analyzer mode
        select_app_mode(page, "Stock Analyzer")
        
        # Wait for and input stock ticker
        page.wait_for_selector("input[type='text']", timeout=10000)
        page.locator("input[type='text']").first.fill("AAPL")
        
        # Set analysis start date (using default date)
        
        # Wait for and click analyze button
        page.wait_for_selector("button:has-text('Analyze Stock')", timeout=10000)
        page.locator("button:has-text('Analyze Stock')").click()
        
        # Wait for the analysis to complete
        page.wait_for_selector("h3:has-text('Analysis Results for AAPL')", timeout=30000)
        
        # Wait for and verify charts are displayed
        page.wait_for_selector("canvas", timeout=30000)
        canvas_elements = page.locator("canvas").all()
        assert len(canvas_elements) >= 3, "Expected at least 3 charts (Price/MA, Wealth, and RSI)"
        
        # Verify metrics are displayed
        expect(page.locator("div[data-testid='stMetric']")).to_be_visible()
    
    def test_stock_analyzer_invalid_ticker(self, page: Page):
        """Test stock analysis with invalid ticker."""
        select_app_mode(page, "Stock Analyzer")
        
        # Input invalid stock ticker
        page.get_by_label("Enter a stock ticker:").fill("INVALID")
        
        # Click analyze button
        page.get_by_role("button", name="Analyze Stock").click()
        
        # Verify error message
        expect(page.locator("div[data-testid='stAlert']")).to_contain_text("Could not fetch data")
    
    def test_stock_analyzer_empty_ticker(self, page: Page):
        """Test stock analysis with empty ticker."""
        select_app_mode(page, "Stock Analyzer")
        
        # Clear ticker input
        page.get_by_label("Enter a stock ticker:").fill("")
        
        # Click analyze button
        page.get_by_role("button", name="Analyze Stock").click()
        
        # Verify warning message
        expect(page.locator("div[data-testid='stAlert']")).to_contain_text("Please enter a stock ticker")
