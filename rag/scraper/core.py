# core.py: Main scraper class that orchestrates the scraping process.
# Why: Acts as the central coordinator, using functions from other modules for modularity.

import os
import time
import json
import argparse
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

import logging

from .constants import PAGES
from .driver import init_driver, get_wait
from .interaction import close_popups_and_cookies, force_expand_all_accordions, scroll_page_completely
from .extraction import get_relevant_text_content, extract_tables_formatted
from .storage import save_text_file, save_structured_data, save_error_file, save_stats
from .utils import setup_logging


class AirIndiaSeleniumScraper:
    def __init__(self, headless: bool = False):
        """
        Initialize the Air India scraper.

        Args:
            headless (bool): Run in headless mode.
        """
        self.data_dir = os.path.join("data", "raw")  # Relative to rag/ for output.
        os.makedirs(self.data_dir, exist_ok=True)

        # Setup logging.
        self.logger = setup_logging()
        self.logger.info("AirIndiaScraper initialized successfully")

        # Initialize driver and wait.
        self.driver: WebDriver = init_driver(headless)
        self.wait: WebDriverWait = get_wait(self.driver)

        # Track scraping statistics.
        self.stats = {
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "total_pages": 0,
            "start_time": datetime.now().isoformat()
        }

    def scrape_page(self, url: str, filename: str) -> bool:
        """
        Scrape a single page: load, interact, extract, and save.

        Args:
            url (str): URL to scrape.
            filename (str): Output filename.

        Returns:
            bool: True if successful.
        """
        self.logger.info(f"[WEB] Scraping: {url}")
        self.stats["total_pages"] += 1

        try:
            # Load page with timeout.
            self.driver.get(url)
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                self.logger.info("Page loaded successfully")
            except TimeoutException:
                self.logger.warning("Page load timeout, continuing anyway")

            # Interact with page.
            close_popups_and_cookies(self.driver)
            force_expand_all_accordions(self.driver)
            scroll_page_completely(self.driver)

            # Extract content.
            page_text = get_relevant_text_content(self.driver)
            tables_text = extract_tables_formatted(self.driver)
            full_content = f"{page_text}\n\n{tables_text}"

            if not full_content.strip() or len(full_content.strip()) < 50:
                self.logger.warning(f"[WARN] Very little content extracted from {url} ({len(full_content)} chars)")
                save_error_file(url, filename, f"Insufficient content: {len(full_content)} characters", self.data_dir)
                self.stats["failed_scrapes"] += 1
                return False

            # Save files.
            save_structured_data(url, full_content, filename, self.data_dir)
            save_text_file(url, full_content, filename, self.data_dir)

            self.logger.info(f"[OK] Successfully scraped: {filename} ({len(full_content)} characters)")
            self.stats["successful_scrapes"] += 1
            return True

        except TimeoutException:
            self.logger.error(f"[TIMEOUT] While loading {url}")
            save_error_file(url, filename, "Page load timeout", self.data_dir)
            self.stats["failed_scrapes"] += 1
            return False

        except WebDriverException as e:
            self.logger.error(f"[WEB ERROR] Could not load {url}: {str(e)[:100]}")
            save_error_file(url, filename, f"WebDriver error: {str(e)[:200]}", self.data_dir)
            self.stats["failed_scrapes"] += 1
            return False

        except Exception as e:
            self.logger.error(f"[ERROR] Scraping {url}: {str(e)}")
            save_error_file(url, filename, f"General error: {str(e)[:200]}", self.data_dir)
            self.stats["failed_scrapes"] += 1
            return False

    def run_all(self) -> None:
        """
        Run the scraper for all defined Air India pages.
        """
        self.logger.info("=" * 80)
        self.logger.info("[START] AIR INDIA WEB SCRAPER")
        self.logger.info("=" * 80)

        total_pages = len(PAGES)
        self.logger.info(f"Total pages to scrape: {total_pages}")

        successful = 0
        failed = 0

        for i, (filename, url) in enumerate(PAGES.items(), 1):
            self.logger.info(f"[PROCESS] ({i}/{total_pages}) Processing: {filename}")

            if self.scrape_page(url, filename):
                successful += 1
            else:
                failed += 1

            if i < total_pages:
                self.logger.info(f"[PAUSE] Waiting 3 seconds before next page...")
                time.sleep(3)

        # Close driver.
        self.logger.info("Closing browser...")
        self.driver.quit()

        # Final stats.
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["duration_seconds"] = (
                datetime.now() - datetime.fromisoformat(self.stats["start_time"])
        ).total_seconds()

        self.logger.info("=" * 80)
        self.logger.info("[STATS] SCRAPING COMPLETE - FINAL STATISTICS")
        self.logger.info("=" * 80)
        self.logger.info(f"Successful scrapes: {successful}")
        self.logger.info(f"Failed scrapes: {failed}")
        self.logger.info(f"Success rate: {(successful / total_pages) * 100:.1f}%")
        self.logger.info(f"Total time: {self.stats['duration_seconds']:.1f} seconds")
        self.logger.info(f"Files saved in: {os.path.abspath(self.data_dir)}")

        save_stats(self.stats, self.data_dir)

        self.logger.info("=" * 80)
        self.logger.info("[SUCCESS] All files are ready for RAG vector store creation!")
        self.logger.info("You can now use the scraped data to build your chatbot's knowledge base.")
        self.logger.info("=" * 80)


def run_quick_test() -> None:
    """
    Run a quick test with a single page to verify the scraper works.
    """
    print("=" * 80)
    print("QUICK TEST - AIR INDIA SCRAPER")
    print("=" * 80)

    test_pages = {
        "test_baggage.txt": "https://www.airindia.com/in/en/travel-information/baggage-guidelines.html"
    }

    try:
        scraper = AirIndiaSeleniumScraper(headless=True)
        for filename, url in test_pages.items():
            print(f"\nTesting: {url}")
            success = scraper.scrape_page(url, filename)
            if success:
                print(f"[OK] Test passed! Check rag/data/raw/{filename}")
            else:
                print(f"[ERROR] Test failed for {url}")
        scraper.driver.quit()
        print("\n" + "=" * 80)
        print("QUICK TEST COMPLETE")
        print("=" * 80)
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Air India Web Scraper - Modular Version")
    parser.add_argument("--test", action="store_true", help="Run quick test with one page")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--url", type=str, help="Scrape a single specific URL")
    parser.add_argument("--output", type=str, help="Output filename for single URL scrape")

    args = parser.parse_args()

    if args.test:
        run_quick_test()
    elif args.url:
        if not args.output:
            print("[ERROR] Please specify --output filename for single URL scraping")
            sys.exit(1)
        print(f"[INFO] Scraping single URL: {args.url}")
        scraper = AirIndiaSeleniumScraper(headless=args.headless)
        success = scraper.scrape_page(args.url, args.output)
        scraper.driver.quit()
        if success:
            print(f"[OK] Successfully scraped to: rag/data/raw/{args.output}")
        else:
            print(f"[ERROR] Failed to scrape {args.url}")
    else:
        print("[INFO] Starting full Air India scraper...")
        print(f"[INFO] Headless mode: {args.headless}")
        scraper = AirIndiaSeleniumScraper(headless=args.headless)
        scraper.run_all()