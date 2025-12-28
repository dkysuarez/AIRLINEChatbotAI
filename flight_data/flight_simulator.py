"""
Flight Simulator for Air India Chatbot.
Generates realistic mock flight data for demonstration purposes.
Now with caching and better organization.
"""

import random
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .constants import AIRPORTS, COMMON_ROUTES, AIRCRAFT_TYPES
from .utils import format_currency, parse_date_string

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class Flight:
    """Data class representing a flight."""
    flight_number: str
    airline: str
    origin: Dict[str, str]
    destination: Dict[str, str]
    departure_time: str
    arrival_time: str
    duration: str
    date: str
    aircraft: str
    status: str
    prices: Dict[str, str]
    available_seats: int
    baggage_allowance: Dict[str, str]

    def to_dict(self) -> Dict:
        """Convert flight to dictionary."""
        return {
            "flight_number": self.flight_number,
            "airline": self.airline,
            "origin": self.origin,
            "destination": self.destination,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "duration": self.duration,
            "date": self.date,
            "aircraft": self.aircraft,
            "status": self.status,
            "prices": self.prices,
            "available_seats": self.available_seats,
            "baggage_allowance": self.baggage_allowance
        }


class FlightSimulator:
    """
    Simulates Air India flight data.

    Features:
    1. Generates realistic flight data for common routes
    2. Caches results for better performance
    3. Simulates real-world variations (prices, availability)
    4. Provides detailed flight information
    """

    def __init__(self):
        """Initialize the flight simulator."""
        self.airlines = ["Air India", "Air India Express"]
        self.statuses = ["Scheduled", "On Time", "Boarding", "Delayed", "Cancelled"]

        # Flight number prefixes
        self.flight_prefixes = {
            "Air India": "AI",
            "Air India Express": "IX"
        }

        logger.info("FlightSimulator initialized")

    def _generate_flight_number(self, airline: str) -> str:
        """
        Generate a realistic flight number.

        Args:
            airline: Airline name

        Returns:
            Flight number string
        """
        prefix = self.flight_prefixes.get(airline, "AI")
        number = random.randint(100, 999)
        return f"{prefix} {number}"

    def _calculate_arrival_time(self, departure: str, duration_min: int) -> str:
        """
        Calculate arrival time based on departure and duration.

        Args:
            departure: Departure time (HH:MM)
            duration_min: Duration in minutes

        Returns:
            Arrival time (HH:MM)
        """
        dep_hour, dep_min = map(int, departure.split(":"))

        total_minutes = dep_hour * 60 + dep_min + duration_min

        arr_hour = (total_minutes // 60) % 24
        arr_min = total_minutes % 60

        return f"{arr_hour:02d}:{arr_min:02d}"

    def _generate_flight_prices(self, base_price: int) -> Dict[str, str]:
        """
        Generate realistic prices for different classes.

        Args:
            base_price: Economy class base price

        Returns:
            Dictionary with prices for all classes
        """
        # Price multipliers for different classes
        multipliers = {
            "Economy": 1.0,
            "Premium Economy": 1.5,
            "Business": 3.0,
            "First": 5.0
        }

        # Add some random variation (±10%)
        variation = random.uniform(0.9, 1.1)

        prices = {}
        for class_name, multiplier in multipliers.items():
            price = int(base_price * multiplier * variation)
            # Round to nearest 100
            price = round(price / 100) * 100
            prices[class_name] = format_currency(price)

        return prices

    @lru_cache(maxsize=100)
    def search_flights(self,
                      origin: str,
                      destination: str,
                      date: str = "tomorrow",
                      passengers: int = 1,
                      travel_class: str = "economy") -> Dict[str, Any]:
        """
        Search for flights between two airports.
        Results are cached for identical searches.

        Args:
            origin: IATA code of origin airport
            destination: IATA code of destination airport
            date: Travel date (relative or absolute)
            passengers: Number of passengers
            travel_class: Travel class

        Returns:
            Dictionary with search results
        """
        logger.info(f"Searching flights: {origin}→{destination} on {date}")

        # Validate airports
        if origin not in AIRPORTS:
            return self._build_error_response(f"Invalid origin airport: {origin}")

        if destination not in AIRPORTS:
            return self._build_error_response(f"Invalid destination airport: {destination}")

        # Parse date
        try:
            parsed_date = parse_date_string(date)
            date_str = parsed_date.strftime("%Y-%m-%d")
            day_name = parsed_date.strftime("%A")
        except Exception as e:
            logger.error(f"Error parsing date '{date}': {e}")
            date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_name = "tomorrow"

        # Find route information
        route_info = self._get_route_info(origin, destination)

        # Generate flights for this route
        flights = self._generate_flights_for_route(
            origin=origin,
            destination=destination,
            date=date_str,
            day_name=day_name,
            route_info=route_info
        )

        # Filter by class if specified
        if travel_class.lower() != "economy":
            # In a real system, we would filter by available classes
            # For now, we just note the requested class
            pass

        # Build response
        return self._build_success_response(
            origin=origin,
            destination=destination,
            date=date_str,
            flights=flights,
            passengers=passengers,
            travel_class=travel_class
        )

    def _get_route_info(self, origin: str, destination: str) -> Dict:
        """
        Get information about a specific route.

        Args:
            origin: Origin airport code
            destination: Destination airport code

        Returns:
            Route information dictionary
        """
        # Look for exact route
        for route in COMMON_ROUTES:
            if route["from"] == origin and route["to"] == destination:
                return route.copy()

        # If not found, generate reasonable defaults
        return {
            "from": origin,
            "to": destination,
            "duration_min": random.randint(60, 240),  # 1-4 hours
            "base_price": random.randint(3000, 10000),
            "daily_flights": random.randint(2, 6)
        }

    def _generate_flights_for_route(self,
                                   origin: str,
                                   destination: str,
                                   date: str,
                                   day_name: str,
                                   route_info: Dict) -> List[Dict]:
        """
        Generate flights for a specific route and date.

        Args:
            origin: Origin airport
            destination: Destination airport
            date: Travel date
            day_name: Day of week
            route_info: Route information

        Returns:
            List of flight dictionaries
        """
        flights = []
        num_flights = min(route_info.get("daily_flights", 3), 5)

        # Common departure times for Indian domestic flights
        departure_times = ["06:00", "09:30", "12:15", "15:45", "18:30", "21:00"]

        # Select random times for this day (some variation)
        selected_times = random.sample(
            departure_times,
            min(num_flights, len(departure_times))
        )
        selected_times.sort()

        for i, dep_time in enumerate(selected_times):
            # Calculate arrival time
            arr_time = self._calculate_arrival_time(dep_time, route_info["duration_min"])

            # Select airline and aircraft
            airline = random.choice(self.airlines)
            aircraft = random.choice(AIRCRAFT_TYPES)

            # Generate flight number
            flight_number = self._generate_flight_number(airline)

            # Generate prices with some variation
            base_price = route_info["base_price"]

            # Weekend/holiday pricing
            if day_name in ["Friday", "Saturday", "Sunday"]:
                base_price = int(base_price * 1.2)  # 20% higher on weekends

            # Last-minute booking (if date is today or tomorrow)
            if date in ["today", "tomorrow"]:
                base_price = int(base_price * 1.3)  # 30% higher for last-minute

            # Add some random variation
            base_price += random.randint(-500, 500)
            base_price = max(2000, base_price)  # Minimum price

            # Create flight
            flight = Flight(
                flight_number=flight_number,
                airline=airline,
                origin=AIRPORTS[origin],
                destination=AIRPORTS[destination],
                departure_time=dep_time,
                arrival_time=arr_time,
                duration=f"{route_info['duration_min'] // 60}h {route_info['duration_min'] % 60}m",
                date=date,
                aircraft=aircraft["model"],
                status=random.choices(
                    self.statuses,
                    weights=[0.7, 0.2, 0.05, 0.04, 0.01]  # Mostly on time
                )[0],
                prices=self._generate_flight_prices(base_price),
                available_seats=random.randint(5, aircraft["seats"] - 20),
                baggage_allowance={
                    "cabin": "7 kg",
                    "checked": random.choice(["15 kg", "23 kg", "25 kg", "30 kg"])
                }
            )

            flights.append(flight.to_dict())

        return flights

    def get_flight_details(self, flight_number: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific flight.

        Args:
            flight_number: Flight number (e.g., "AI 865")
            date: Optional date

        Returns:
            Detailed flight information
        """
        logger.info(f"Getting details for flight: {flight_number}")

        if not date:
            date = (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")

        # Extract airline from flight number
        if flight_number.startswith("AI "):
            airline = "Air India"
            origin, destination = random.choice([("DEL", "BOM"), ("BOM", "DEL")])
        elif flight_number.startswith("IX "):
            airline = "Air India Express"
            origin, destination = random.choice([("DEL", "BLR"), ("BLR", "DEL")])
        else:
            airline = "Air India"
            origin, destination = "DEL", "BOM"

        # Generate a flight
        route_info = self._get_route_info(origin, destination)
        flights = self._generate_flights_for_route(
            origin=origin,
            destination=destination,
            date=date,
            day_name=datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
            route_info=route_info
        )

        if flights:
            # Use the first flight and update its flight number
            flight = flights[0]
            flight["flight_number"] = flight_number

            # Add additional details
            flight.update({
                "checkin_counters": f"{random.randint(1, 10)}-{random.randint(11, 30)}",
                "checkin_close": "60 minutes before departure",
                "boarding_close": "30 minutes before departure",
                "meal_options": ["Vegetarian", "Non-Vegetarian", "Special Meal (request 24h in advance)"],
                "special_services": [
                    "Wheelchair assistance",
                    "Unaccompanied minor service",
                    "Pet transport",
                    "Medical assistance"
                ],
                "contact_info": {
                    "airline": airline,
                    "reservations": "1-800-180-1407",
                    "website": "https://www.airindia.com"
                }
            })

            return {
                "success": True,
                "flight": flight,
                "message": "Flight details retrieved successfully"
            }
        else:
            return self._build_error_response(f"Flight {flight_number} not found")

    def format_flight_response(self, search_results: Dict[str, Any]) -> str:
        """
        Format flight search results for chatbot response.
        Compatible with the existing app.py interface.

        Args:
            search_results: Flight search results dictionary

        Returns:
            Formatted string response
        """
        if not search_results.get("success", False):
            error = search_results.get("error", "Unknown error")
            return f"❌ I couldn't find any flights. {error}"

        flights = search_results.get("flights", [])
        search_params = search_results.get("search_params", {})

        if not flights:
            origin_city = search_params.get("origin_city", "Unknown")
            destination_city = search_params.get("destination_city", "Unknown")
            date = search_params.get("date", "Unknown")

            return f"✈️ No flights available from {origin_city} to {destination_city} on {date}."

        # Build response
        origin_city = search_params.get("origin_city", "Unknown")
        destination_city = search_params.get("destination_city", "Unknown")
        date = search_params.get("date", "Unknown")
        passengers = search_params.get("passengers", 1)

        response = [
            f"✈️ **Air India Flights from {origin_city} to {destination_city}**",
            f"**Date:** {date} | **Passengers:** {passengers}",
            ""
        ]

        for i, flight in enumerate(flights[:4]):  # Show max 4 flights
            flight_num = flight.get("flight_number", "N/A")
            departure = flight.get("departure_time", "N/A")
            arrival = flight.get("arrival_time", "N/A")
            duration = flight.get("duration", "N/A")
            price = flight.get("prices", {}).get("Economy", "₹N/A")
            status = flight.get("status", "Scheduled")
            aircraft = flight.get("aircraft", "Unknown")

            flight_text = [
                f"**{flight_num}** - {departure} → {arrival} ({duration})",
                f"   • Aircraft: {aircraft}",
                f"   • Price: {price} (Economy)",
                f"   • Status: {status}",
                f"   • Baggage: {flight.get('baggage_allowance', {}).get('checked', 'N/A')} checked"
            ]

            response.extend(flight_text)

            if i < len(flights[:4]) - 1:
                response.append("")  # Empty line between flights

        response.extend([
            "",
            "💡 **Tip:** For more details on a specific flight, ask about it by time or flight number.",
            "📞 **Need help?** Call Air India at 1-800-180-1407"
        ])

        return "\n".join(response)

    def _build_success_response(self,
                               origin: str,
                               destination: str,
                               date: str,
                               flights: List[Dict],
                               passengers: int,
                               travel_class: str) -> Dict[str, Any]:
        """Build a success response dictionary."""
        return {
            "success": True,
            "search_params": {
                "origin": origin,
                "destination": destination,
                "date": date,
                "origin_city": AIRPORTS[origin]["city"],
                "destination_city": AIRPORTS[destination]["city"],
                "passengers": passengers,
                "class": travel_class
            },
            "total_flights": len(flights),
            "flights": flights,
            "currency": "INR",
            "timestamp": datetime.now().isoformat(),
            "disclaimer": "Mock data for demonstration. Real flight data may vary."
        }

    def _build_error_response(self, error_message: str) -> Dict[str, Any]:
        """Build an error response dictionary."""
        return {
            "success": False,
            "error": error_message,
            "flights": [],
            "total_flights": 0,
            "timestamp": datetime.now().isoformat()
        }