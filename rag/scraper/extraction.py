# extraction.py: Handles extraction of relevant text and tables from the webpage,
# including cleaning to remove noise for better RAG usability.
# Why: Ensures extracted data is clean and focused, avoiding duplicates or irrelevant sections.

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import logging


from .constants import CONTENT_SELECTORS, COMMON_NOISE, TABLE_HEADER_KEYWORDS

logger = logging.getLogger(__name__)


def get_relevant_text_content(driver: WebDriver) -> str:
    """
    Extract text content from relevant page sections only (e.g., main content),
    avoiding headers, footers, and navigation.

    Args:
        driver (WebDriver): The Selenium driver instance.

    Returns:
        str: Extracted and cleaned text content.
    """
    logger.info("Extracting relevant text content...")

    all_text = ""
    extracted_selectors = []

    # Try priority selectors for main content.
    for selector in CONTENT_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                if text and len(text) > 100:  # Only substantial content.
                    all_text += text + "\n\n"
                    extracted_selectors.append(selector)
                    break
        except:
            continue

    # Fallback to general containers if nothing found.
    if not all_text.strip():
        logger.info("No content found with selectors, trying general text extraction")
        try:
            main_elements = driver.find_elements(By.CSS_SELECTOR, "div.container, div.main, div#main")
            for elem in main_elements:
                text = elem.text.strip()
                if text and len(text) > 100:
                    all_text += text + "\n\n"
                    extracted_selectors.append("container/main")
        except:
            pass

    # Final fallback to body.
    if not all_text.strip():
        logger.warning("Using body text as fallback")
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            all_text = body.text
            extracted_selectors.append("body")
        except:
            all_text = "No text content could be extracted"

    # Clean and return.
    cleaned_text = clean_extracted_text(all_text)
    if extracted_selectors:
        logger.info(f"Extracted text from: {', '.join(set(extracted_selectors))}")
    return cleaned_text


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted text by removing duplicates, empty lines, and common noise.

    Args:
        text (str): Raw extracted text.

    Returns:
        str: Cleaned text.
    """
    if not text:
        return ""

    lines = text.split('\n')
    cleaned_lines = []
    seen_lines = set()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 10:  # Skip empty/short lines.
            continue

        line_lower = line_clean.lower()
        is_noise = any(noise in line_lower and len(line_clean) < 50 for noise in COMMON_NOISE)
        if is_noise:
            continue

        # Skip URLs or emails.
        if line_clean.startswith('http://') or line_clean.startswith('https://') or (
                '@' in line_clean and '.' in line_clean):
            continue

        # Normalize for duplicate check.
        line_normalized = ' '.join(line_lower.split())
        if line_normalized not in seen_lines:
            seen_lines.add(line_normalized)
            cleaned_lines.append(line_clean)

    return '\n'.join(cleaned_lines)


def extract_tables_formatted(driver: WebDriver) -> str:
    """
    Extract all tables and format them as readable text with headers bolded.

    Args:
        driver (WebDriver): The Selenium driver instance.

    Returns:
        str: Formatted table text.
    """
    logger.info("Extracting and formatting tables...")

    tables = driver.find_elements(By.TAG_NAME, "table")
    if not tables:
        logger.info("No tables found on this page")
        return ""

    table_text = ""
    for i, table in enumerate(tables):
        try:
            table_text += f"\n{'=' * 80}\nTABLE {i + 1}\n{'=' * 80}\n"
            rows = table.find_elements(By.TAG_NAME, "tr")

            for j, row in enumerate(rows):
                # Get th and td cells.
                cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
                cell_texts = [cell.text.strip() for cell in cells if cell.text.strip()]

                if cell_texts:
                    row_line = " | ".join(cell_texts)
                    # Check if row is a header.
                    is_header = (j == 0 or any(keyword in row_line.lower() for keyword in TABLE_HEADER_KEYWORDS))
                    if is_header:
                        table_text += f"**{row_line}**\n"
                    else:
                        table_text += f"{row_line}\n"

            table_text += "\n"
        except Exception as e:
            logger.warning(f"[WARN] Error extracting table {i + 1}: {e}")
            continue

    return table_text