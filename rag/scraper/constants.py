# constants.py: Centralizes all configurable values for the scraper.
# This includes URLs to scrape, CSS selectors for interactions, and common noise patterns to clean.
# Why: Makes maintenance easier—if the website changes, update here only.

from typing import Dict, List

# Dictionary of pages to scrape: filename as key, URL as value.
# These are key Air India pages for policies and info, suitable for RAG indexing.
PAGES: Dict[str, str] = {
    "baggage_guidelines.txt": "https://www.airindia.com/in/en/travel-information/baggage-guidelines.html",
    "checked_baggage.txt": "https://www.airindia.com/in/en/travel-information/baggage-guidelines/checked-baggage-allowance.html",
    "faq_baggage.txt": "https://www.airindia.com/in/en/frequently-asked-questions/baggage.html",
    "web_checkin.txt": "https://www.airindia.com/in/en/manage/web-check-in.html",
    "flight_status.txt": "https://www.airindia.com/in/en/manage/flight-status.html",
    "travel_advisory.txt": "https://www.airindia.com/in/en/travel-advisory.html",
    "special_assistance.txt": "https://www.airindia.com/in/en/travel-information/special-assistance.html",
    "cancellation_policy.txt": "https://www.airindia.com/in/en/refund-and-cancellation.html",
    "checkin_options.txt": "https://www.airindia.com/in/en/checkin-options.html",
    "flight_booking_info.txt": "https://www.airindia.com/in/en/book-flights"
}

# CSS selectors for main content extraction, in priority order.
# Why: Targets relevant sections like 'main' or '.content' to avoid headers/footers.
CONTENT_SELECTORS: List[str] = [
    "main",
    "article",
    ".content",
    ".main-content",
    ".container",
    "#content",
    ".page-content",
    ".faq-section",
    ".baggage-info",
    ".travel-info",
    ".policy-content",
    "[role='main']",
    ".body-content",
    ".text-content"
]

# Selectors for cookie banners to accept/close.
# Why: Websites often use standard libraries like OneTrust; these are broad to handle variations.
COOKIE_SELECTORS: List[str] = [
    "button[id*='onetrust-accept']",
    "button:has-text('Accept all')",
    "button:has-text('Accept')",
    "button[aria-label*='cookie']",
    "button[class*='cookie']",
    "#accept-cookies",
    ".cookie-accept",
    ".accept-cookies"
]

# Selectors for closing chat/modals/popups.
# Why: Air India has chatbots; these target common close buttons.
CLOSE_SELECTORS: List[str] = [
    "button[aria-label='Close']",
    "button.close",
    ".close-chat",
    ".modal-close",
    "[data-dismiss='modal']"
]

# Common noise phrases to filter out during text cleaning (e.g., navigation links).
# Why: Removes irrelevant text like menus or footers to improve RAG quality.
COMMON_NOISE: List[str] = [
    "home", "about", "contact", "login", "sign up", "signup", "search",
    "copyright", "all rights reserved", "privacy policy", "terms of use",
    "terms and conditions", "sitemap", "follow us", "subscribe", "newsletter",
    "facebook", "twitter", "instagram", "linkedin", "youtube", "whatsapp",
    "cookie policy", "accessibility", "careers", "media", "investors",
    "feedback", "help", "support", "faq", "contact us", "blog", "news",
    "press", "advertise", "affiliates", "partners", "mobile app", "download",
    "book now", "reservations", "manage booking", "flight status", "check-in"
]

# Header keywords to bold in table extraction.
# Why: Helps format tables readably for RAG (e.g., mark headers like "allowance").
TABLE_HEADER_KEYWORDS: List[str] = [
    "cabin", "from", "to", "brand", "class", "type",
    "allowance", "weight", "fee", "route", "destination",
    "baggage", "luggage", "policy"
]