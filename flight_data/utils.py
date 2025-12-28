"""
Utility functions for flight data processing.
Shared helper functions extracted from intent_detector.py and mock_flights.py.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def normalize_city_name(city_input: str) -> str:
    """
    Normalize city names for consistent matching.
    Converts variations like 'New Delhi' to standard 'Delhi'.

    Args:
        city_input: Raw city name from user input

    Returns:
        Normalized city name
    """
    if not city_input:
        return ""

    city = city_input.lower().strip()

    # Common city name variations
    variations = {
        "new delhi": "delhi",
        "newdelhi": "delhi",
        "bombay": "mumbai",
        "madras": "chennai",
        "calcutta": "kolkata",
        "calcuta": "kolkata",
        "bangalore": "bengaluru",
        "banglore": "bengaluru",
        "cochin": "kochi",
        "baroda": "vadodara",
        "ahmadabad": "ahmedabad",
    }

    # Check for variations
    for variant, standard in variations.items():
        if variant in city:
            return standard

    return city


def is_valid_iata_code(code: str) -> bool:
    """
    Check if a 3-letter string is a valid IATA airport code.
    Filters out common words that happen to be 3 letters.

    Args:
        code: 3-letter string to check

    Returns:
        True if valid IATA code, False otherwise
    """
    from .constants import INVALID_IATA_CODES, AIRPORTS

    if not code or len(code) != 3:
        return False

    if not code.isalpha() or not code.isupper():
        return False

    # Filter out common words
    if code in INVALID_IATA_CODES:
        return False

    # Check if it's in our known airports (optional)
    # Remove this check if you want to accept any valid-looking code
    if code not in AIRPORTS:
        return False

    return True


def parse_date_string(date_str: str) -> datetime:
    """
    Parse date strings like 'tomorrow', 'next Monday' into actual dates.
    Supports relative dates and absolute dates.

    Args:
        date_str: Date string from user input

    Returns:
        Parsed datetime object
    """
    today = datetime.now().date()

    # Convert to lowercase for case-insensitive matching
    date_lower = date_str.lower().strip()

    # Relative dates
    if date_lower == "today":
        return today
    elif date_lower == "tomorrow":
        return today + timedelta(days=1)
    elif date_lower == "day after tomorrow":
        return today + timedelta(days=2)
    elif date_lower == "next week":
        return today + timedelta(days=7)

    # Day names (next Monday, this Friday)
    day_mapping = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    for day_name, day_num in day_mapping.items():
        if day_name in date_lower:
            if "next" in date_lower:
                days_ahead = (day_num - today.weekday() + 7) % 7
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            else:
                days_ahead = (day_num - today.weekday() + 7) % 7
                return today + timedelta(days=days_ahead)

    # Try parsing as absolute date (YYYY-MM-DD, DD/MM/YYYY, etc.)
    date_formats = [
        "%Y-%m-%d",  # 2024-12-25
        "%d/%m/%Y",  # 25/12/2024
        "%d-%m-%Y",  # 25-12-2024
        "%d %B %Y",  # 25 December 2024
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_str, date_format).date()
        except ValueError:
            continue

    # Default: tomorrow
    return today + timedelta(days=1)


def extract_iata_codes(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract IATA airport codes from text.
    Looks for patterns like "DEL to BOM" or "flights from DEL to BOM".

    Args:
        text: User input text

    Returns:
        Tuple of (origin_code, destination_code) or (None, None)
    """
    text_upper = text.upper()

    # Find all potential IATA codes
    potential_codes = re.findall(r'\b[A-Z]{3}\b', text_upper)
    valid_codes = [code for code in potential_codes if is_valid_iata_code(code)]

    if len(valid_codes) >= 2:
        return valid_codes[0], valid_codes[1]

    return None, None


def format_currency(amount: int, currency: str = "INR") -> str:
    """
    Format currency amounts nicely.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    if currency == "INR":
        return f"₹{amount:,}"
    elif currency == "USD":
        return f"${amount:,}"
    else:
        return f"{amount:,} {currency}"


def extract_city_names(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrae nombres de ciudades del texto y los convierte a IATA.

    Ejemplo: "Flights from Delhi to Mumbai" -> ("DEL", "BOM")

    Args:
        text: Texto del usuario

    Returns:
        Tuple (origin_code, destination_code) o (None, None)
    """
    from .constants import CITY_TO_IATA

    if not text:
        return None, None

    text_lower = text.lower()
    found_cities = []

    # Buscar todas las ciudades mencionadas
    for city_name, iata_code in CITY_TO_IATA.items():
        if city_name in text_lower:
            # Encontrar posición para ordenar
            position = text_lower.find(city_name)
            found_cities.append((position, city_name, iata_code))

    # Ordenar por posición en el texto
    found_cities.sort(key=lambda x: x[0])

    # Tomar las primeras 2 ciudades encontradas
    if len(found_cities) >= 2:
        print(
            f"DEBUG extract_city_names: Encontradas ciudades: {found_cities[0][1]}->{found_cities[0][2]}, {found_cities[1][1]}->{found_cities[1][2]}")
        return found_cities[0][2], found_cities[1][2]
    elif len(found_cities) == 1:
        print(f"DEBUG extract_city_names: Solo 1 ciudad encontrada: {found_cities[0][1]}->{found_cities[0][2]}")
        return found_cities[0][2], None

    print("DEBUG extract_city_names: No se encontraron ciudades")
    return None, None


def extract_flight_parameters(text: str) -> dict:
    """
    Extrae todos los parámetros de búsqueda de vuelos.
    Combina extracción por códigos IATA y por nombres de ciudades.

    Args:
        text: Texto del usuario

    Returns:
        Diccionario con parámetros extraídos
    """
    from .constants import AIRPORTS

    params = {
        "origin": None,
        "destination": None,
        "origin_city": None,
        "destination_city": None,
        "date": "tomorrow",
        "passengers": 1,
        "class": "economy"
    }

    # 1. Primero intentar extraer códigos IATA
    origin_iata, dest_iata = extract_iata_codes(text)

    # 2. Si no encontró códigos IATA, buscar nombres de ciudades
    if not origin_iata or not dest_iata:
        origin_city, dest_city = extract_city_names(text)
        if origin_city and dest_city:
            origin_iata, dest_iata = origin_city, dest_city

    # 3. Asignar resultados
    if origin_iata and dest_iata:
        params["origin"] = origin_iata
        params["destination"] = dest_iata
        params["origin_city"] = AIRPORTS.get(origin_iata, {}).get("city", origin_iata)
        params["destination_city"] = AIRPORTS.get(dest_iata, {}).get("city", dest_iata)

    # 4. Extraer fecha
    if "today" in text.lower():
        params["date"] = "today"
    elif "tomorrow" in text.lower():
        params["date"] = "tomorrow"
    elif "next week" in text.lower():
        params["date"] = "next_week"

    # 5. Extraer pasajeros
    passenger_match = re.search(r'(\d+)\s+(?:passenger|person|people|adult)', text.lower())
    if passenger_match:
        try:
            passengers = int(passenger_match.group(1))
            if 1 <= passengers <= 9:
                params["passengers"] = passengers
        except:
            pass

    print(f"DEBUG extract_flight_parameters: {params}")
    return params