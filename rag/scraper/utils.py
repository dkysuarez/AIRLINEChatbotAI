# utils.py: Utility functions for logging and other helpers.
# Why: Keeps auxiliary code separate, reusable across modules.

import logging
import sys


class ASCIIFilter(logging.Filter):
    """
    Logging filter to replace non-ASCII characters with ASCII equivalents.
    Why: Ensures compatibility with Windows consoles that may crash on Unicode.
    """

    def filter(self, record):
        if hasattr(record, 'msg'):
            record.msg = self.sanitize_text(record.msg)
        if hasattr(record, 'args'):
            record.args = tuple(
                self.sanitize_text(str(arg)) if isinstance(arg, str) else arg for arg in record.args
            )
        return True

    def sanitize_text(self, text: str) -> str:
        """Replace non-ASCII characters with ASCII equivalents."""
        replacements = {
            '[OK]': '[OK]',
            '[ERROR]': '[ERROR]',
            '[WARN]': '[WARN]',
            '[WEB]': '[WEB]',
            '[FILE]': '[FILE]',
            '[TEXT]': '[TEXT]',
            '[STATS]': '[STATS]',
            '[SUCCESS]': '[SUCCESS]',
            '[START]': '[START]',
            '[PROCESS]': '[PROCESS]',
            '[TIME]': '[TIME]',
            '[SECURITY]': '[SECURITY]',
            '[UNLOCK]': '[UNLOCK]',
            '[LAUNCH]': '[LAUNCH]',
            '[PAUSE]': '[PAUSE]',
            '[RESUME]': '[RESUME]'
        }
        for emoji, ascii_text in replacements.items():
            text = text.replace(emoji, ascii_text)
        return text


def setup_logging() -> logging.Logger:
    """
    Configure logging with UTF-8 encoding and ASCII filter for Windows compatibility.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Remove existing handlers to avoid duplicates.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Basic configuration.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler('scraper.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )

    logger = logging.getLogger(__name__)

    # Apply ASCII filter to all handlers.
    ascii_filter = ASCIIFilter()
    for handler in logger.handlers:
        handler.addFilter(ascii_filter)

    return logger