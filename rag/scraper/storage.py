# storage.py: Handles saving scraped data to files (TXT, JSON) and error logs.
# Why: Isolates file I/O for better testability and potential extension (e.g., to cloud storage).

import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def save_text_file(url: str, content: str, filename: str, data_dir: str) -> None:
    """
    Save scraped data in plain text format with header (for RAG compatibility).

    Args:
        url (str): Source URL.
        content (str): Extracted content.
        filename (str): Output filename.
        data_dir (str): Directory to save in.
    """
    txt_path = os.path.join(data_dir, filename)
    header = f"""SOURCE URL: {url}
SCRAPE DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
CONTENT LENGTH: {len(content)} characters
{'=' * 80}

"""

    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(content)
        logger.info(f"[TEXT] Saved text file: {filename}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to save text file: {e}")


def save_structured_data(url: str, content: str, filename: str, data_dir: str) -> None:
    """
    Save scraped data in structured JSON format with metadata.

    Args:
        url (str): Source URL.
        content (str): Extracted content.
        filename (str): Output filename.
        data_dir (str): Directory to save in.
    """
    json_filename = filename.replace('.txt', '.json')
    json_path = os.path.join(data_dir, json_filename)

    structured_data = {
        "metadata": {
            "source_url": url,
            "scrape_date": datetime.now().isoformat(),
            "filename": filename,
            "domain": "airindia.com",
            "content_type": "airline_policy"
        },
        "content": {
            "text": content,
            "length_chars": len(content),
            "length_words": len(content.split()),
            "tables_present": "**TABLE**" in content
        },
        "processing_info": {
            "cleaned": True,
            "format": "text_with_tables"
        }
    }

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        logger.info(f"[FILE] Saved structured data: {json_filename}")
    except Exception as e:
        logger.error(f"[ERROR] Failed to save JSON: {e}")


def save_error_file(url: str, filename: str, error_msg: str, data_dir: str) -> None:
    """
    Save error information when scraping fails.

    Args:
        url (str): Failed URL.
        filename (str): Intended filename.
        error_msg (str): Error message.
        data_dir (str): Directory to save in.
    """
    error_filename = f"ERROR_{filename}"
    error_path = os.path.join(data_dir, error_filename)

    error_content = f"""ERROR SCRAPING PAGE
{'=' * 40}
URL: {url}
Timestamp: {datetime.now().isoformat()}
Error: {error_msg}

Troubleshooting:
1. Check if the URL is correct
2. Verify website accessibility
3. Check for authentication requirements
4. Verify network connection
"""

    try:
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(error_content)
        logger.info(f"[WARN] Saved error log: {error_filename}")
    except Exception as e:
        logger.error(f"[ERROR] Could not save error file: {e}")


def save_stats(stats: dict, data_dir: str) -> None:
    """
    Save scraping statistics to JSON.

    Args:
        stats (dict): Statistics dictionary.
        data_dir (str): Directory to save in.
    """
    stats_file = os.path.join(data_dir, "scraping_statistics.json")
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"[FILE] Statistics saved to: {stats_file}")
    except Exception as e:
        logger.error(f"[ERROR] Could not save statistics: {e}")