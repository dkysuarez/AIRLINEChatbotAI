# interaction.py: Handles dynamic interactions with the webpage, such as closing popups,
# expanding accordions, and scrolling for lazy loading.
# Why: Websites like Air India have interactive elements; this module ensures all content is visible before extraction.

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

from .constants import COOKIE_SELECTORS, CLOSE_SELECTORS

logger = logging.getLogger(__name__)


def close_popups_and_cookies(driver: WebDriver) -> bool:
    """
    Close cookie banners, chat bots, and other popups.

    Args:
        driver (WebDriver): The Selenium driver instance.

    Returns:
        bool: True if any popup was closed, False otherwise.
    """
    logger.info("Closing popups and cookie banners...")
    time.sleep(2)  # Wait for page to load popups.

    # Try to accept cookies using predefined selectors.
    for selector in COOKIE_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    driver.execute_script("arguments[0].click();", element)
                    logger.info("[OK] Accepted cookies")
                    time.sleep(1)
                    return True
        except:
            continue

    # Try to close chat/notification popups.
    for selector in CLOSE_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    logger.info("[OK] Closed chat/notification popup")
                    time.sleep(1)
                    return True
        except:
            continue

    return False


def force_expand_all_accordions(driver: WebDriver) -> None:
    """
    Expand all accordion sections using JavaScript to reveal hidden content.

    Args:
        driver (WebDriver): The Selenium driver instance.
    """
    logger.info("Expanding all accordion sections...")

    expansion_script = """
    // Expand Bootstrap accordions
    var accordionButtons = document.querySelectorAll('button.accordion-button, .accordion-button, [data-toggle="collapse"]');
    accordionButtons.forEach(function(btn) {
        if (btn.getAttribute('aria-expanded') === 'false' || btn.classList.contains('collapsed')) {
            try {
                btn.click();
            } catch (e) {
                console.log('Could not click button:', e);
            }
        }
    });

    // Force show all collapse elements
    var collapseElements = document.querySelectorAll('.collapse:not(.show), .accordion-collapse:not(.show)');
    collapseElements.forEach(function(collapse) {
        collapse.classList.add('show');
        collapse.style.display = 'block';
        collapse.style.height = 'auto';
    });

    // Return count for logging
    return 'Expanded ' + accordionButtons.length + ' accordions and ' + collapseElements.length + ' collapse elements';
    """

    try:
        result = driver.execute_script(expansion_script)
        time.sleep(3)  # Wait for content to load after expansion.
        logger.info(f"[OK] Accordions expanded: {result}")
    except Exception as e:
        logger.warning(f"[WARN] Could not expand accordions: {e}")


def scroll_page_completely(driver: WebDriver) -> None:
    """
    Scroll through the entire page to trigger lazy loading of content.

    Args:
        driver (WebDriver): The Selenium driver instance.
    """
    logger.info("Scrolling page to load all content...")

    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_attempts = 10

    while scroll_attempts < max_attempts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)  # Wait for new content to load.
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1

    # Scroll back to top for consistent extraction.
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    logger.info(f"Scrolled {scroll_attempts} times")