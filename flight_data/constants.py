"""
Constants for the flight system.
All hardcoded lists and configurations extracted from intent_detector.py and mock_flights.py
"""

# ============================================================================
# AIRPORT DATA (IATA codes for Air India destinations)
# ============================================================================

AIRPORTS = {
    "DEL": {
        "code": "DEL",
        "name": "Indira Gandhi International Airport",
        "city": "Delhi",
        "country": "India"
    },
    "BOM": {
        "code": "BOM", 
        "name": "Chhatrapati Shivaji Maharaj International Airport",
        "city": "Mumbai", 
        "country": "India"
    },
    "BLR": {
        "code": "BLR",
        "name": "Kempegowda International Airport",
        "city": "Bangalore",
        "country": "India"
    },
    "MAA": {
        "code": "MAA",
        "name": "Chennai International Airport",
        "city": "Chennai",
        "country": "India"
    },
    "HYD": {
        "code": "HYD",
        "name": "Rajiv Gandhi International Airport",
        "city": "Hyderabad",
        "country": "India"
    },
}

# ============================================================================
# COMMON FLIGHT ROUTES (based on real Air India frequencies)
# ============================================================================

COMMON_ROUTES = [
    {
        "from": "DEL",
        "to": "BOM",
        "duration_min": 130,
        "base_price": 4500,
        "daily_flights": 8
    },
    {
        "from": "DEL",
        "to": "BLR", 
        "duration_min": 155,
        "base_price": 6500,
        "daily_flights": 6
    },
    {
        "from": "BOM",
        "to": "DEL",
        "duration_min": 130,
        "base_price": 4500,
        "daily_flights": 8
    },
    {
        "from": "BOM",
        "to": "BLR",
        "duration_min": 100,
        "base_price": 4000,
        "daily_flights": 10
    },
    # Add more routes...
]

# ============================================================================
# INTENT DETECTION KEYWORDS (multi-language support)
# ============================================================================

# Flight-related keywords (English, Spanish, Hindi for bonus)
FLIGHT_KEYWORDS = [
    # English
    "flight", "flights", "fly", "flying", "airplane", "plane",
    "booking", "book", "reservation", "ticket", "fare",
    "departure", "arrival", "destination", "origin", "route",
    "schedule", "time", "availability", "price", "cost",
    # Spanish  
    "vuelo", "vuelos", "volar", "reservar", "reserva", "billete", "pasaje",
    # Hindi (bonus feature)
    "उड़ान", "टिकट", "बुकिंग", "आरक्षण"
]

# Policy-related keywords
POLICY_KEYWORDS = [
    # English
    "baggage", "luggage", "allowance", "weight", "size", "dimension",
    "carry-on", "hand luggage", "checked baggage", "excess", "overweight",
    "checkin", "check-in", "boarding pass", "cancel", "cancellation", "refund",
    "policy", "policies", "rule", "rules", "regulation", "information",
    # Spanish
    "equipaje", "maleta", "facturación", "cancelación", "reembolso",
    "política", "peso", "tamaño", "regla", "información",
    # Hindi
    "सामान", "भार", "नियम", "जानकारी"
]

# Greeting keywords
GREETING_KEYWORDS = [
    "hello", "hi", "hey", "hola", "buenos", "buenas", "namaste", "नमस्ते",
    "thanks", "thank you", "gracias", "धन्यवाद",
    "goodbye", "bye", "adiós", "अलविदा"
]

# ============================================================================
# INVALID IATA CODES (common 3-letter words to filter out)
# ============================================================================

INVALID_IATA_CODES = {
    "THE", "AND", "FOR", "YOU", "CAN", "GET", "AIR", "IND", "ALL", "ANY",
    "ONE", "TWO", "SIX", "TEN", "FLY", "NOW", "DAY", "WEEK", "NEXT", "YES",
    # Add more common words...
}

# ============================================================================
# REGEX PATTERNS FOR INTENT DETECTION
# ============================================================================

# Patterns for flight searches
FLIGHT_PATTERNS = [
    r"flights?\s+(?:from|between)\s+\w+\s+(?:to|and)\s+\w+",
    r"\b(?:find|search|show|look for)\s+flights?\s+\w+",
    r"\w+\s+to\s+\w+\s+flights?",
    r"flights?\s+\w+\s+\w+",
]

# Patterns for policy questions  
POLICY_PATTERNS = [
    r"baggage\s+(?:allowance|policy|rules?)\s+(?:for|to|in)\s+\w+",
    r"what(?:\s+is|\s+are)?\s+the\s+\w+\s+(?:allowance|policy|rules?)\s+for\s+\w+",
    r"how\s+much\s+\w+\s+(?:allowance|can|do)\s+I\s+\w+\s+for\s+\w+",
]

# Patterns for city/code extraction
CITY_PATTERNS = [
    (r'([A-Z]{3})[-\s]+([A-Z]{3})[-\s]*flights?\b', 'both_codes_flights'),
    (r'flights?\s+from\s+([A-Z]{3})\s+to\s+([A-Z]{3})', 'both_codes_with_flights'),
    (r"(\b[A-Z]{3}\b)[\s\-]+(?:to[\s\-]+)?(\b[A-Z]{3}\b)", "both_codes"),
]

# ============================================================================
# AIRCRAFT TYPES (Air India fleet)
# ============================================================================

AIRCRAFT_TYPES = [
    {
        "model": "Airbus A320",
        "seats": 180,
        "speed": "840 km/h",
        "range": "6150 km"
    },
    {
        "model": "Boeing 787-8 Dreamliner",
        "seats": 256,
        "speed": "903 km/h",
        "range": "14140 km"
    },
    {
        "model": "Boeing 777-300ER",
        "seats": 342,
        "speed": "905 km/h", 
        "range": "14685 km"
    },
]# ============================================================================
# CITY TO IATA CODE MAPPING (CRÍTICO para entender "Delhi to Mumbai")
# ============================================================================

CITY_TO_IATA = {
    # India
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "madras": "MAA",
    "hyderabad": "HYD",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "goa": "GOI",
    "ahmedabad": "AMD",
    "pune": "PNQ",
    "jaipur": "JAI",
    "lucknow": "LKO",
    "kochi": "COK",
    "guwahati": "GAU",

    # Internacional
    "new york": "JFK",
    "london": "LHR",
    "dubai": "DXB",
    "singapore": "SIN",
    "tokyo": "NRT",
    "sydney": "SYD",
    "toronto": "YYZ",
    "paris": "CDG",
    "frankfurt": "FRA",
    "hong kong": "HKG",
    "bangkok": "BKK"
}

# Añadir estos aeropuertos a AIRPORTS si no existen
ADDITIONAL_AIRPORTS = {
    "CCU": {
        "code": "CCU",
        "name": "Netaji Subhash Chandra Bose International Airport",
        "city": "Kolkata",
        "country": "India"
    },
    "GOI": {
        "code": "GOI",
        "name": "Goa International Airport",
        "city": "Goa",
        "country": "India"
    },
    "AMD": {
        "code": "AMD",
        "name": "Sardar Vallabhbhai Patel International Airport",
        "city": "Ahmedabad",
        "country": "India"
    },
    "PNQ": {
        "code": "PNQ",
        "name": "Pune Airport",
        "city": "Pune",
        "country": "India"
    },
    "JAI": {
        "code": "JAI",
        "name": "Jaipur International Airport",
        "city": "Jaipur",
        "country": "India"
    }
}

# Actualizar AIRPORTS con los adicionales
for code, airport in ADDITIONAL_AIRPORTS.items():
    if code not in AIRPORTS:
        AIRPORTS[code] = airport