import pytest
from playwright.sync_api import Page, expect
from conftest import wait_for_streamlit_load, select_app_mode

@pytest.mark.e2e
class TestPortfolioGenerator:
    def test_portfolio_generator_basic_flow(self, page: Page):
        """Test the basic flow of portfolio generation."""
        # Select Portfolio Generator mode
        select_app_mode(page, "Portfolio Generator")
        
        # Wait for the number input to be visible and input investment amount
        page.wait_for_selector("input[type='number']", timeout=10000)
        page.locator("input[type='number']").first.fill("5000")
        
        # Ensure checkboxes are checked
        for checkbox_text in ["Invest in high dividend stocks?", 
                            "Invest in growth stocks?", 
                            "Invest in index funds?"]:
            page.wait_for_selector(f"div:has-text('{checkbox_text}')", timeout=10000)
            checkbox = page.locator(f"input[type='checkbox'][aria-label='{checkbox_text}']").first
            if not checkbox.is_checked():
                checkbox.check()
        
        # Click generate button
        page.wait_for_selector("button:has-text('Generate Portfolio')", timeout=10000)
        page.locator("button:has-text('Generate Portfolio')").click()
        
        # Wait for the portfolio to be generated
        page.wait_for_selector("h3:has-text('Generated Portfolio:')", timeout=30000)
        
        # Verify the portfolio table is displayed
        expect(page.locator("div[data-testid='stDataFrame']")).to_be_visible()
        
        # Verify metrics are displayed
        expect(page.locator("div[data-testid='stMetric']")).to_be_visible()
    
    def test_portfolio_generator_no_selection(self, page: Page):
        """Test portfolio generation with no investment types selected."""
        select_app_mode(page, "Portfolio Generator")
        
        # Uncheck all boxes
        for checkbox_text in ["Invest in high dividend stocks?", 
                            "Invest in growth stocks?", 
                            "Invest in index funds?"]:
            page.wait_for_selector(f"div:has-text('{checkbox_text}')", timeout=10000)
            checkbox = page.locator(f"input[type='checkbox'][aria-label='{checkbox_text}']").first
            if checkbox.is_checked():
                checkbox.click()
        
        # Click generate button
        page.wait_for_selector("button:has-text('Generate Portfolio')", timeout=10000)
        page.locator("button:has-text('Generate Portfolio')").click()
        
        # Wait for and verify warning message
        page.wait_for_selector("div[data-testid='stAlert']", timeout=10000)
        expect(page.locator("div[data-testid='stAlert']")).to_contain_text("Please select at least one investment type.")
    
    def test_portfolio_generator_invalid_amount(self, page: Page):
        """Test portfolio generation with invalid investment amount."""
        select_app_mode(page, "Portfolio Generator")
        
        # Try to input 0
        page.get_by_label("Enter amount of money ($) to invest:").fill("0")
        
        # Verify the input is not accepted (Streamlit enforces min_value=0.01)
        input_value = float(page.get_by_label("Enter amount of money ($) to invest:").input_value())
        assert input_value >= 0.01, "Amount should not be less than 0.01"
