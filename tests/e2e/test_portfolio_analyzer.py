import pytest
from playwright.sync_api import Page, expect
import os
from conftest import wait_for_streamlit_load, select_app_mode

@pytest.mark.e2e
class TestPortfolioAnalyzer:
    def test_portfolio_analyzer_basic_flow(self, page: Page):
        """Test the basic flow of portfolio analysis."""
        # Load the app and wait for initial render
        wait_for_streamlit_load(page)
        
        # Select Portfolio Analyzer mode
        select_app_mode(page, "Portfolio Analyzer")
        
        # Wait for the main app content to load
        page.wait_for_selector("div[data-testid='stAppViewContainer']", timeout=30000)
        
        # Wait for file uploader and ensure it's visible
        file_uploader = page.locator("div[data-testid='stFileUploader']")
        file_uploader.wait_for(state="visible", timeout=30000)
        
        # Upload test portfolio file
        with page.expect_file_chooser() as fc_info:
            file_uploader.click()
            file_chooser = fc_info.value
            file_chooser.set_files(os.path.join(os.getcwd(), "test_protfolio.csv"))
        
        # Wait for the upload to complete and page to stabilize
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # Verify that the table is displayed
        table = page.locator("div[data-testid='stDataFrame']")
        table.wait_for(state="visible", timeout=30000)
        
        # Verify the diversification score
        metric = page.locator("div[data-testid='stMetric']")
        metric.wait_for(state="visible", timeout=30000)
        
        # Click the suggestions button and verify results
        suggest_button = page.get_by_role("button", name="Suggest Diversification Actions")
        suggest_button.wait_for(state="visible", timeout=30000)
        suggest_button.click()
        
        # Wait for suggestions to appear
        suggestions = page.locator("h3:has-text('Rebalancing Suggestions:')")
        suggestions.wait_for(state="visible", timeout=30000)
    
    def test_portfolio_analyzer_invalid_file(self, page: Page):
        """Test portfolio analysis with invalid file."""
        # Load the app and wait for initial render
        wait_for_streamlit_load(page)
        
        # Select Portfolio Analyzer mode
        select_app_mode(page, "Portfolio Analyzer")
        
        # Create temporary invalid CSV file
        with open("invalid_portfolio.csv", "w") as f:
            f.write("invalid,data\n1,2,3")
        
        try:
            # Wait for file uploader and ensure it's visible
            file_uploader = page.locator("div[data-testid='stFileUploader']")
            file_uploader.wait_for(state="visible", timeout=30000)
            
            # Upload invalid file
            with page.expect_file_chooser() as fc_info:
                file_uploader.click()
                file_chooser = fc_info.value
                file_chooser.set_files(os.path.join(os.getcwd(), "invalid_portfolio.csv"))
            
            # Wait for the error message
            error_alert = page.locator("div[data-testid='stAlert']")
            error_alert.wait_for(state="visible", timeout=30000)
            expect(error_alert).to_contain_text("missing the following required columns")
            
        finally:
            # Clean up
            os.remove("invalid_portfolio.csv")
    
    def test_portfolio_analyzer_empty_file(self, page: Page):
        """Test portfolio analysis with empty file."""
        # Load the app and wait for initial render
        wait_for_streamlit_load(page)
        
        # Select Portfolio Analyzer mode
        select_app_mode(page, "Portfolio Analyzer")
        
        # Create temporary empty CSV file
        with open("empty_portfolio.csv", "w") as f:
            f.write("")
        
        try:
            # Wait for file uploader and ensure it's visible
            file_uploader = page.locator("div[data-testid='stFileUploader']")
            file_uploader.wait_for(state="visible", timeout=30000)
            
            # Upload empty file
            with page.expect_file_chooser() as fc_info:
                file_uploader.click()
                file_chooser = fc_info.value
                file_chooser.set_files(os.path.join(os.getcwd(), "empty_portfolio.csv"))
            
            # Wait for the error message
            error_alert = page.locator("div[data-testid='stAlert']")
            error_alert.wait_for(state="visible", timeout=30000)
            expect(error_alert).to_contain_text("empty")
            
        finally:
            # Clean up
            os.remove("empty_portfolio.csv")
