# flight_data/mock_flights.py
"""
Base de datos simulada de vuelos de Air India
Basada en rutas reales y horarios comunes
VERSIÓN CORREGIDA - Compatible con app.py
"""

import datetime
from typing import List, Dict, Any, Optional
import random


class MockFlightDatabase:
    """Base de datos simulada de vuelos de Air India - VERSIÓN CORREGIDA"""

    # Aeropuertos principales de India
    AIRPORTS = {
        "DEL": {"code": "DEL", "name": "Indira Gandhi International", "city": "Delhi"},
        "BOM": {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj", "city": "Mumbai"},
        "BLR": {"code": "BLR", "name": "Kempegowda International", "city": "Bengaluru"},
        "MAA": {"code": "MAA", "name": "Chennai International", "city": "Chennai"},
        "HYD": {"code": "HYD", "name": "Rajiv Gandhi International", "city": "Hyderabad"},
        "CCU": {"code": "CCU", "name": "Netaji Subhash Chandra Bose", "city": "Kolkata"},
        "AMD": {"code": "AMD", "name": "Sardar Vallabhbhai Patel", "city": "Ahmedabad"},
        "GOI": {"code": "GOI", "name": "Dabolim", "city": "Goa"},
        "JAI": {"code": "JAI", "name": "Jaipur International", "city": "Jaipur"},
        "LKO": {"code": "LKO", "name": "Chaudhary Charan Singh", "city": "Lucknow"}
    }

    # Rutas comunes de Air India con frecuencias
    COMMON_ROUTES = [
        {"from": "DEL", "to": "BOM", "duration_min": 130, "typical_price": 4500},
        {"from": "DEL", "to": "BLR", "duration_min": 155, "typical_price": 6500},
        {"from": "DEL", "to": "MAA", "duration_min": 165, "typical_price": 7000},
        {"from": "BOM", "to": "DEL", "duration_min": 130, "typical_price": 4500},
        {"from": "BOM", "to": "BLR", "duration_min": 100, "typical_price": 4000},
        {"from": "BOM", "to": "HYD", "duration_min": 80, "typical_price": 3500},
        {"from": "BLR", "to": "DEL", "duration_min": 155, "typical_price": 6500},
        {"from": "BLR", "to": "BOM", "duration_min": 100, "typical_price": 4000},
        {"from": "DEL", "to": "GOI", "duration_min": 180, "typical_price": 5500},
        {"from": "DEL", "to": "JAI", "duration_min": 60, "typical_price": 3000},
    ]

    # Tipos de avión
    AIRCRAFT_TYPES = [
        {"model": "Airbus A320", "seats": 180, "speed": "840 km/h"},
        {"model": "Airbus A321", "seats": 220, "speed": "840 km/h"},
        {"model": "Boeing 787-8", "seats": 256, "speed": "903 km/h"},
        {"model": "Boeing 777-300ER", "seats": 342, "speed": "905 km/h"},
        {"model": "Airbus A319", "seats": 144, "speed": "828 km/h"}
    ]

    # Clases de servicio
    CLASSES = [
        {"code": "Y", "name": "Economy", "multiplier": 1.0},
        {"code": "S", "name": "Premium Economy", "multiplier": 1.5},
        {"code": "J", "name": "Business", "multiplier": 3.0},
        {"code": "F", "name": "First", "multiplier": 5.0}
    ]

    def __init__(self):
        """Inicializa la base de datos de vuelos"""
        pass

    def generate_flight_number(self):
        """Genera un número de vuelo de Air India realista"""
        prefixes = ["AI", "AIX"]
        numbers = random.choice([
            f"{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            f"{random.randint(1, 9)}{random.randint(0, 9)}"
        ])
        return f"{random.choice(prefixes)} {numbers}"

    def generate_flights_for_route(self, origin: str, destination: str, date_str: str, num_flights: int = 3) -> List[
        Dict]:
        """
        Genera vuelos simulados para una ruta y fecha específica

        Args:
            origin: Código IATA de origen (ej: "DEL")
            destination: Código IATA de destino (ej: "BOM")
            date_str: Fecha en formato "YYYY-MM-DD" o "tomorrow", "today"
            num_flights: Número de vuelos a generar

        Returns:
            Lista de diccionarios con información de vuelos
        """
        # Parsear fecha
        if date_str.lower() == "today":
            flight_date = datetime.date.today()
        elif date_str.lower() == "tomorrow":
            flight_date = datetime.date.today() + datetime.timedelta(days=1)
        else:
            try:
                flight_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                flight_date = datetime.date.today() + datetime.timedelta(days=random.randint(1, 30))

        # Buscar información de la ruta
        route_info = next(
            (r for r in self.COMMON_ROUTES
             if r["from"] == origin and r["to"] == destination),
            None
        )

        if not route_info:
            # Si no es una ruta común, crear una genérica
            route_info = {
                "from": origin,
                "to": destination,
                "duration_min": random.randint(60, 240),
                "typical_price": random.randint(3000, 10000)
            }

        flights = []

        # Generar horarios de vuelo (típicamente 3-4 vuelos por día en rutas principales)
        base_times = ["06:00", "09:30", "14:15", "18:45", "21:00"]
        available_times = random.sample(base_times, min(num_flights, len(base_times)))

        for i, departure_time in enumerate(available_times):
            # Calcular hora de llegada
            departure_dt = datetime.datetime.strptime(departure_time, "%H:%M")
            arrival_dt = departure_dt + datetime.timedelta(minutes=route_info["duration_min"])
            arrival_time = arrival_dt.strftime("%H:%M")

            # Seleccionar avión
            aircraft = random.choice(self.AIRCRAFT_TYPES)

            # Generar precios con variación
            base_price = route_info["typical_price"]
            price_variation = random.randint(-500, 500)
            economy_price = max(2000, base_price + price_variation)

            # Crear información del vuelo
            flight = {
                "flight_number": self.generate_flight_number(),
                "airline": "Air India",
                "origin": {
                    "code": origin,
                    "name": self.AIRPORTS.get(origin, {}).get("name", f"{origin} Airport"),
                    "city": self.AIRPORTS.get(origin, {}).get("city", origin)
                },
                "destination": {
                    "code": destination,
                    "name": self.AIRPORTS.get(destination, {}).get("name", f"{destination} Airport"),
                    "city": self.AIRPORTS.get(destination, {}).get("city", destination)
                },
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": f"{route_info['duration_min'] // 60}h {route_info['duration_min'] % 60}m",
                "duration_minutes": route_info["duration_min"],
                "date": flight_date.strftime("%Y-%m-%d"),
                "day_name": flight_date.strftime("%A"),
                "aircraft": aircraft["model"],
                "seats_capacity": aircraft["seats"],
                "status": random.choice(["Scheduled", "On Time", "Boarding"]),
                "terminal": random.choice(["T1", "T2", "T3"]),
                "gate": f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 50)}",
                "prices": {
                    "Economy": f"₹{economy_price:,}",
                    "Premium Economy": f"₹{int(economy_price * 1.5):,}",
                    "Business": f"₹{int(economy_price * 3.0):,}",
                    "First": f"₹{int(economy_price * 5.0):,}"
                },
                "base_price": economy_price,
                "currency": "INR",
                "available_seats": random.randint(10, aircraft["seats"] - 20),
                "booking_class": random.choice(["Y", "S", "J", "F"]),
                "baggage_allowance": {
                    "cabin": "7 kg",
                    "checked": random.choice(["15 kg", "23 kg", "25 kg", "30 kg"])
                },
                "amenities": random.sample([
                    "In-flight entertainment",
                    "Meal service",
                    "WiFi (paid)",
                    "USB charging",
                    "Blanket & pillow"
                ], 3)
            }

            flights.append(flight)

        # Ordenar por hora de salida
        flights.sort(key=lambda x: x["departure_time"])

        return flights

    def search_flights(self, origin: str, destination: str, date: str = "tomorrow") -> Dict[str, Any]:
        """
        Busca vuelos según parámetros - VERSIÓN CORREGIDA para app.py

        Returns:
            Diccionario con formato compatible con app.py:
            {
                "success": True/False,
                "search_params": {...},
                "total_flights": N,
                "flights": [...],
                ...
            }
        """
        origin = origin.upper().strip()
        destination = destination.upper().strip()

        # Validar aeropuertos
        if origin not in self.AIRPORTS:
            return {
                "success": False,
                "error": f"Código de aeropuerto no válido: {origin}",
                "flights": [],
                "total_flights": 0
            }

        if destination not in self.AIRPORTS:
            return {
                "success": False,
                "error": f"Código de aeropuerto no válido: {destination}",
                "flights": [],
                "total_flights": 0
            }

        # Generar vuelos
        flights = self.generate_flights_for_route(origin, destination, date)

        # Formatear respuesta EXACTAMENTE como app.py lo espera
        origin_info = self.AIRPORTS[origin]
        destination_info = self.AIRPORTS[destination]

        return {
            "success": True,
            "search_params": {
                "origin": origin,
                "destination": destination,
                "date": date,
                "origin_city": origin_info["city"],
                "destination_city": destination_info["city"]
            },
            "total_flights": len(flights),
            "flights": flights,
            "currency": "INR",
            "timestamp": datetime.datetime.now().isoformat(),
            "disclaimer": "Mock data for demonstration purposes. Real flight data may vary."
        }

    def get_flight_details(self, flight_number: str, date: str = None) -> Dict[str, Any]:
        """
        Obtiene detalles específicos de un vuelo

        Args:
            flight_number: Número de vuelo (ej: "AI 865")
            date: Fecha opcional

        Returns:
            Detalles del vuelo
        """
        # Para simplificar, generamos un vuelo ficticio
        if not date:
            date = (datetime.date.today() + datetime.timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")

        # Rutas comunes para el número de vuelo
        common_routes = [
            ("DEL", "BOM"),
            ("BOM", "DEL"),
            ("DEL", "BLR"),
            ("BLR", "DEL")
        ]

        origin, destination = random.choice(common_routes)
        flights = self.generate_flights_for_route(origin, destination, date, num_flights=1)

        if flights:
            flight = flights[0]
            flight["flight_number"] = flight_number  # Sobrescribir con el número solicitado

            # Añadir información adicional
            flight.update({
                "checkin_counters": f"{random.randint(1, 10)}-{random.randint(11, 30)}",
                "checkin_close": "60 minutes before departure",
                "boarding_close": "30 minutes before departure",
                "operational_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "meal_options": ["Vegetarian", "Non-Vegetarian", "Special Meal (request in advance)"],
                "special_services": ["Wheelchair assistance", "Unaccompanied minor", "Pet transport"],
                "contact_info": {
                    "airline": "Air India",
                    "reservations": "1-800-180-1407",
                    "website": "https://www.airindia.com"
                }
            })

            return {
                "success": True,
                "flight": flight,
                "additional_info": "Flight details retrieved successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Flight {flight_number} not found for date {date}",
                "flight": None
            }

    def format_flight_response(self, flight_results: Dict, params: Dict = None) -> str:
        """
        Formatea los resultados de vuelos para respuesta del chatbot
        COMPATIBILIDAD con app.py que busca este método
        """
        if not flight_results.get("success", False):
            return "✈️ No se encontraron vuelos para esa ruta y fecha."

        flights = flight_results.get("flights", [])
        if not flights:
            return "✈️ No hay vuelos disponibles para esa ruta."

        origin = params.get("origin", "Unknown") if params else "Unknown"
        destination = params.get("destination", "Unknown") if params else "Unknown"
        date = params.get("date", "tomorrow") if params else "tomorrow"

        response = f"✈️ **Air India Flights from {origin} to {destination} for {date}:**\n\n"

        for i, flight in enumerate(flights[:5]):  # Mostrar máximo 5 vuelos
            flight_num = flight.get("flight_number", "N/A")
            departure = flight.get("departure_time", "N/A")
            arrival = flight.get("arrival_time", "N/A")
            duration = flight.get("duration", "N/A")
            price = flight.get("prices", {}).get("Economy", "₹N/A")
            status = flight.get("status", "Scheduled")
            aircraft = flight.get("aircraft", "Unknown")

            response += f"**{flight_num}** - {departure} → {arrival} ({duration})\n"
            response += f"   • Aircraft: {aircraft}\n"
            response += f"   • Price: {price} (Economy)\n"
            response += f"   • Status: {status}\n"
            response += f"   • Available seats: {flight.get('available_seats', 'N/A')}\n"

            if i < len(flights[:5]) - 1:
                response += "\n"

        response += "\n💡 *Para más detalles o reservas, visita www.airindia.com*"

        return response