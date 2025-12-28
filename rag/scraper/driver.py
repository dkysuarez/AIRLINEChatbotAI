# driver.py: Handles initialization and configuration of the Selenium WebDriver.
# Why: Separates browser setup from main logic, making it easier to switch browsers or add options.

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import logging

logger = logging.getLogger(__name__)


def init_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Initialize and configure Chrome WebDriver with enhanced robustness options:
    - Anti-detection measures
    - Proxy bypass (to avoid localhost tunnels, VPNs, etc.)
    - Performance and stability improvements
    - Implicit wait for better element handling

    Args:
        headless (bool): Run in headless mode (no visible window).

    Returns:
        webdriver.Chrome: Fully configured Chrome driver instance.

    Raises:
        Exception: If driver initialization fails.
    """
    chrome_options = Options()

    # Headless mode if requested
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")  # Required in headless on some systems

    # Core stability options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")

    # === Anti-detection options (very important for sites like Air India) ===
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # Hide webdriver property
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")

    # === Fix proxy/VPN/localhost tunnel issues (e.g. localhost:3493 timeout) ===
    chrome_options.add_argument("--proxy-server='direct://'")  # Use direct connection
    chrome_options.add_argument("--proxy-bypass-list=*")  # Bypass proxy for all domains

    # Additional performance and compatibility options
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    # Realistic user agent (mimic real browser)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Hide Selenium indicators via JavaScript
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
            """
        })

        # Add implicit wait for better reliability when finding elements
        driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to appear

        logger.info("[OK] Chrome WebDriver initialized successfully with enhanced robustness")
        return driver

    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize Chrome WebDriver: {e}")
        raise


def get_wait(driver: webdriver.Chrome) -> WebDriverWait:
    """
    Create a WebDriverWait instance for explicit waits.

    Args:
        driver (webdriver.Chrome): The initialized driver.

    Returns:
        WebDriverWait: Wait object with 30-second timeout.
    """
    return WebDriverWait(driver, 30)