import os
import subprocess
import sys
import time
import urllib.request
from typing import Generator
import pytest
from playwright.sync_api import Page, expect, Browser, BrowserContext

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

def pytest_exception_interact(node, call, report):
    if report.failed:
        print("\nTest failed! Debug information:") # noqa: golden-principles
        print(f"Test name: {node.name}") # noqa: golden-principles
        print(f"Exception: {call.excinfo}") # noqa: golden-principles
        # Additional debug info will be in the screenshots and videos

@pytest.fixture(scope="session")
def streamlit_server():
    """Fixture to start and stop the Streamlit server for testing."""
    print("\nDebug: Starting Streamlit server...") # noqa: golden-principles
    
    # Kill any existing Streamlit processes
    import psutil
    for proc in psutil.process_iter():
        try:
            if "streamlit" in proc.name().lower():
                print(f"Debug: Killing existing Streamlit process {proc.pid}") # noqa: golden-principles
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Start the Streamlit server with explicit port
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
        preexec_fn=os.setsid
    )
    
    # Function to monitor server output
    def monitor_output():
        while True:
            output = process.stdout.readline()
            if output:
                print(f"Debug: Streamlit output: {output.strip()}") # noqa: golden-principles
            error = process.stderr.readline()
            if error:
                print(f"Debug: Streamlit error: {error.strip()}") # noqa: golden-principles
            if not output and not error and process.poll() is not None:
                break
    
    # Start output monitoring in a separate thread
    from threading import Thread
    monitor_thread = Thread(target=monitor_output, daemon=True)
    monitor_thread.start()
    
    # Wait for the server to start and be responsive
    url = "http://localhost:8501"
    max_retries = 60  # Increased timeout to 60 seconds
    retry_count = 0
    
    print(f"Debug: Waiting for server at {url}") # noqa: golden-principles
    while retry_count < max_retries:
        try:
            response = urllib.request.urlopen(url)
            if response.status == 200:
                print("Debug: Server is responding with 200 OK") # noqa: golden-principles
                break
        except Exception as e: # noqa: golden-principles
            print(f"Debug: Server not ready (attempt {retry_count + 1}/{max_retries}): {str(e)}") # noqa: golden-principles
            time.sleep(1)
            retry_count += 1
    
    if retry_count >= max_retries:
        process.terminate()
        raise Exception("Streamlit server failed to start after 60 seconds")
    
    # Additional wait to ensure the app is fully loaded
    print("Debug: Server started, waiting for full initialization...") # noqa: golden-principles
    time.sleep(10)  # Increased wait time to 10 seconds
    
    yield url
    
    # Cleanup: Kill the server and its children
    print("Debug: Shutting down Streamlit server...") # noqa: golden-principles
    try:
        import signal
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        print("Debug: Server shutdown complete") # noqa: golden-principles
    except Exception as e: # noqa: golden-principles
        print(f"Debug: Error during server shutdown: {str(e)}") # noqa: golden-principles

@pytest.fixture
def context(browser: Browser, request) -> Generator[BrowserContext, None, None]:
    """Create a new browser context with specific viewport and permissions."""
    # Ensure the test videos directory exists
    os.makedirs("./test-videos", exist_ok=True)
    os.makedirs("./test-traces", exist_ok=True)
    
    # Create the context with longer timeout
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        permissions=["clipboard-read", "clipboard-write"],
        record_video_dir="./test-videos/",
    )
    
    # Enable tracing at the start
    context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True
    )
    
    # Set longer timeouts
    context.set_default_timeout(60000)  # 60 seconds timeout
    context.set_default_navigation_timeout(60000)
    
    # Create a page and set up logging
    page = context.new_page()
    
    def log_request(request):
        print(f"\nDebug: Request >> {request.method} {request.url}") # noqa: golden-principles
    
    def log_response(response):
        print(f"Debug: Response << {response.status} {response.url}") # noqa: golden-principles
    
    page.on("request", log_request)
    page.on("response", log_response)
    
    yield context
    
    try:
        # Always save the trace for debugging
        trace_path = f"./test-traces/trace_{request.node.name}.zip"
        context.tracing.stop(path=trace_path)
        print(f"Debug: Trace saved to {trace_path}") # noqa: golden-principles
        
    except Exception as e: # noqa: golden-principles
        print(f"Debug: Error saving trace: {str(e)}") # noqa: golden-principles
        
    finally:
        # Always close the context
        context.close()

@pytest.fixture
def page(context: BrowserContext, streamlit_server: str) -> Generator[Page, None, None]:
    """Fixture to handle page setup and navigation."""
    page = context.new_page()
    page.set_default_timeout(60000)  # 60 second timeout
    
    # Add JavaScript console logging
    page.on("console", lambda msg: print(f"Browser console: {msg.text}")) # noqa: golden-principles
    
    retries = 3
    for attempt in range(retries):
        try:
            print(f"\nDebug: Navigation attempt {attempt + 1}/{retries}") # noqa: golden-principles
            
            # Navigate to the app
            print(f"Debug: Navigating to {streamlit_server}") # noqa: golden-principles
            response = page.goto(streamlit_server, wait_until="domcontentloaded")
            
            if not response:
                print("Debug: No response from navigation") # noqa: golden-principles
                continue
                
            print(f"Debug: Got response with status {response.status}") # noqa: golden-principles
            
            if response.status != 200:
                print(f"Debug: Unexpected status code: {response.status}") # noqa: golden-principles
                continue
            
            # Wait for initial load
            print("Debug: Waiting for initial page load...") # noqa: golden-principles
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(5000)  # Give it time to initialize
            
            # Check if we have any content
            has_content = page.evaluate("""
                () => {
                    return {
                        bodyText: document.body.textContent,
                        elements: document.body.children.length
                    }
                }
            """)
            
            if not has_content['bodyText'] or has_content['elements'] == 0:
                print("Debug: Page appears empty, retrying...") # noqa: golden-principles
                page.reload()
                continue
            
            print("Debug: Page loaded successfully!") # noqa: golden-principles
            break
            
        except Exception as e: # noqa: golden-principles
            print(f"Debug: Navigation error: {str(e)}") # noqa: golden-principles
            if attempt < retries - 1:
                print("Debug: Retrying...") # noqa: golden-principles
                page.wait_for_timeout(5000)  # Wait before retry
            else:
                raise Exception(f"Failed to load page after {retries} attempts") from e
    
    yield page
    page.close()

def wait_for_streamlit_load(page: Page):
    """Helper function to wait for Streamlit to load completely."""
    print("Debug: Starting to wait for Streamlit load...") # noqa: golden-principles
    
    try:
        # First, just wait for any content to appear
        print("Debug: Waiting for initial page content...") # noqa: golden-principles
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)  # Give it some time to initialize
        
        # Examine the page structure
        print("Debug: Examining page structure...") # noqa: golden-principles
        page_content = page.evaluate("""
            () => {
                return {
                    body: document.body.innerHTML,
                    dataTestIds: Array.from(document.querySelectorAll('[data-testid]')).map(el => el.getAttribute('data-testid')),
                    iframeCount: document.querySelectorAll('iframe').length,
                    divCount: document.querySelectorAll('div').length
                }
            }
        """)
        
        print("Debug: Page content analysis:") # noqa: golden-principles
        print(f"Data-testid elements found: {page_content['dataTestIds']}") # noqa: golden-principles
        print(f"Number of iframes: {page_content['iframeCount']}") # noqa: golden-principles
        print(f"Number of divs: {page_content['divCount']}") # noqa: golden-principles
        
        # Wait for basic structure with a more lenient approach
        print("Debug: Waiting for basic structure...") # noqa: golden-principles
        
        # Try different possible selectors
        selectors = [
            "div#root",  # Basic root
            "[data-testid]",  # Any Streamlit element
            "[data-baseweb]",  # Base web components
            "header",  # Header section
            "nav",  # Navigation
            "main"  # Main content
        ]
        
        for selector in selectors:
            try:
                element = page.wait_for_selector(selector, timeout=10000)
                print(f"Debug: Found element with selector: {selector}") # noqa: golden-principles
                if element:
                    break
            except Exception: # noqa: golden-principles
                print(f"Debug: Selector not found: {selector}") # noqa: golden-principles
        
        # Wait for network activity to settle
        print("Debug: Waiting for network idle...") # noqa: golden-principles
        page.wait_for_load_state("networkidle")
        
        # Final check for basic interactivity
        print("Debug: Checking for basic interactivity...") # noqa: golden-principles
        has_content = page.evaluate("""
            () => {
                const body = document.body;
                const hasContent = body.textContent.length > 0;
                const isInteractive = document.querySelector('button, select, input') !== null;
                return {
                    hasContent,
                    isInteractive,
                    text: body.textContent.slice(0, 100)  // First 100 chars for debugging
                };
            }
        """)
        
        print(f"Debug: Page has content: {has_content['hasContent']}") # noqa: golden-principles
        print(f"Debug: Page is interactive: {has_content['isInteractive']}") # noqa: golden-principles
        print(f"Debug: First 100 chars: {has_content['text']}") # noqa: golden-principles
        
        if not has_content['hasContent'] or not has_content['isInteractive']:
            print("Warning: Page might not be fully loaded") # noqa: golden-principles
            page.screenshot(path="not_ready.png")
        
        print("Debug: Basic load complete") # noqa: golden-principles
        
    except Exception as e: # noqa: golden-principles
        print(f"Error during page load: {str(e)}") # noqa: golden-principles
        print("Debug: Taking screenshot of error state...") # noqa: golden-principles
        page.screenshot(path="load_error.png")
        print("Debug: Attempting to capture page source...") # noqa: golden-principles
        try:
            source = page.content()
            with open("error_page.html", "w") as f:
                f.write(source)
            print("Debug: Page source saved to error_page.html") # noqa: golden-principles
        except Exception as e2: # noqa: golden-principles
            print(f"Debug: Failed to capture page source: {str(e2)}") # noqa: golden-principles
        raise e

def select_app_mode(page: Page, mode: str):
    """Helper function to select an app mode from the sidebar."""
    print(f"\nDebug: Starting to select app mode: {mode}") # noqa: golden-principles
    
    # Wait for the initial page load
    page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
    page.wait_for_load_state("networkidle")
    
    try:
        # Wait for the selectbox to be present
        print("Debug: Waiting for selectbox...") # noqa: golden-principles
        selectbox = page.locator("div[data-testid='stSelectbox']")
        selectbox.wait_for(timeout=30000)
        
        # Find and click the current value container
        print("Debug: Opening dropdown...") # noqa: golden-principles
        value_container = selectbox.locator("div[role='combobox']").first
        value_container.click()
        page.wait_for_timeout(1000)
        
        # Type the desired mode name to filter options
        print(f"Debug: Typing mode name: {mode}") # noqa: golden-principles
        input_element = page.locator("input[role='combobox']")
        input_element.fill(mode)
        page.wait_for_timeout(500)
        
        # Press Enter to select the option
        print("Debug: Pressing Enter...") # noqa: golden-principles
        input_element.press("Enter")
        page.wait_for_timeout(1000)
        
        # Wait for the page to update
        print("Debug: Waiting for page update...") # noqa: golden-principles
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
    except Exception as e: # noqa: golden-principles
        print(f"Debug: First attempt failed: {str(e)}") # noqa: golden-principles
        print("Debug: Trying alternative approach...") # noqa: golden-principles
        
        try:
            # Alternative approach: Use the arrow keys
            value_container = page.locator("div[data-testid='stSelectbox']")
            value_container.click()
            page.wait_for_timeout(500)
            
            # Press arrow keys to navigate through options
            input_element = page.locator("input[role='combobox']")
            input_element.press("ArrowDown")  # First option
            input_element.press("ArrowDown")  # Second option
            input_element.press("ArrowDown")  # Third option
            input_element.press("Enter")
            
        except Exception as e2: # noqa: golden-principles
            print(f"Debug: Alternative approach failed: {str(e2)}") # noqa: golden-principles
            raise e2
    
    # Final wait for the page to stabilize
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
