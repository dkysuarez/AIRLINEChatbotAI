"""
RESPONSE BUILDER - RESPONSE FORMATTER
=====================================

Responsibility: Transform raw data into formatted responses for the user.
This module handles ONLY presentation, NOT business logic.

Principles:
1. Separation of concerns: Data comes from ChatbotEngine, presentation is here
2. Reusable templates: For consistent responses
3. Intelligent formatting: Adapts response based on content type
4. Professional formatting: Clear, professional presentation
"""

import re
import textwrap
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging


class ResponseBuilder:
    """
    Builder for formatted responses for Air India chatbot.

    This module is responsible for:
    - Formatting flight results into readable text
    - Presenting policy responses clearly
    - Generating general chat responses
    - Applying consistent templates
    - Handling professional formatting
    """

    def __init__(self, max_length: int = 2000):
        """
        Initialize the ResponseBuilder.

        Args:
            max_length: Maximum response length (characters)
        """
        self.max_length = max_length
        self.logger = logging.getLogger(__name__)

        # Predefined templates
        self.templates = {
            "flight_header": self._get_flight_header_template(),
            "flight_item": self._get_flight_item_template(),
            "policy_response": self._get_policy_response_template(),
            "general_chat": self._get_general_chat_template(),
            "error": self._get_error_template()
        }

        self.logger.info("ResponseBuilder initialized")

    def build_response(
            self,
            intent: str,
            action_result: Dict[str, Any],
            user_query: Optional[str] = None
    ) -> str:
        """
        Build a formatted response based on intent and data.

        Args:
            intent: Intent type (flight_search, policy_question, etc.)
            action_result: Raw data from ChatbotEngine
            user_query: Original user query (optional)

        Returns:
            Formatted string to display to user
        """
        self.logger.debug(f"Building response for intent: {intent}")

        try:
            if intent == "flight_search":
                return self._build_flight_response(action_result, user_query)

            elif intent == "policy_question":
                return self._build_policy_response(action_result, user_query)

            elif intent == "general_chat":
                return self._build_general_response(user_query)

            elif intent == "error":
                return self._build_error_response(action_result)

            else:
                return self._build_fallback_response(intent, user_query)

        except Exception as e:
            self.logger.error(f"Error building response: {e}")
            return self._build_error_response({
                "type": "builder_error",
                "details": str(e)
            })

    def _build_flight_response(
            self,
            action_result: Dict[str, Any],
            user_query: Optional[str] = None
    ) -> str:
        """Build formatted response for flight searches."""

        result_type = action_result.get("type", "")

        if result_type == "error":
            error_msg = action_result.get("message", "Error in flight search")
            suggestion = action_result.get("suggestion", "")

            response = "✈️ ERROR IN FLIGHT SEARCH\n\n"
            response += f"{error_msg}\n"
            if suggestion:
                response += f"\n💡 SUGGESTION: {suggestion}"

            return response

        elif result_type == "flight_results":
            data = action_result.get("data", {})

            if not data.get("success", False):
                return "✈️ No flights found for your search."

            # Extract information
            flights = data.get("flights", [])
            search_params = data.get("search_params", {})

            # Build response
            response = self._build_flight_results_header(search_params)

            if not flights:
                response += "\n✈️ No flights available for this route and date."
            else:
                # Limit to maximum 5 flights
                flights_to_show = flights[:5]

                for i, flight in enumerate(flights_to_show, 1):
                    response += self._build_flight_item(flight, i)

                if len(flights) > 5:
                    response += f"\n📊 AND {len(flights) - 5} MORE FLIGHTS..."

            # Add disclaimer and footer
            response += self._build_flight_footer(search_params, len(flights))

            return response

        else:
            return "✈️ Processing your flight search..."

    def _build_flight_results_header(self, search_params: Dict[str, Any]) -> str:
        """Build header for flight results."""
        origin_city = search_params.get("origin_city", search_params.get("origin", "Origin"))
        dest_city = search_params.get("destination_city", search_params.get("destination", "Destination"))
        date = search_params.get("date", "selected date")

        header = "✈️ **AIR INDIA - FLIGHT SEARCH RESULTS**\n\n"
        header += f"**ROUTE:** {origin_city} → {dest_city}\n"
        header += f"**DATE:** {date}\n"
        header += "─" * 40 + "\n\n"

        return header

    def _build_flight_item(self, flight: Dict[str, Any], index: int) -> str:
        """Build individual flight item."""
        # Extraer datos del vuelo con valores por defecto
        flight_num = flight.get("flight_number", "N/A")
        departure = flight.get("departure_time", "N/A")
        arrival = flight.get("arrival_time", "N/A")
        duration = flight.get("duration", "N/A")

        # Manejar precio: puede ser dict o string
        prices = flight.get("prices", {})
        if isinstance(prices, dict):
            price = prices.get("Economy", "₹ N/A")
        else:
            price = prices if prices else "₹ N/A"

        status = flight.get("status", "Scheduled")
        aircraft = flight.get("aircraft", "N/A")
        available_seats = flight.get("available_seats", "N/A")

        # Valores opcionales con defaults
        terminal = flight.get("terminal", "TBD")
        gate = flight.get("gate", "To be assigned")

        # Formato de item CORREGIDO (sin campos obligatorios que falten)
        item = f"{index}. **{flight_num}** - {departure} → {arrival} ({duration})\n"
        item += f"   • **Price:** {price} (Economy)\n"
        item += f"   • **Status:** {status}\n"
        item += f"   • **Aircraft:** {aircraft}\n"
        item += f"   • **Available seats:** {available_seats}\n"

        # Solo mostrar terminal/gate si existen
        if terminal != "TBD":
            item += f"   • **Terminal:** {terminal}\n"
        if gate != "To be assigned":
            item += f"   • **Gate:** {gate}\n"

        return item + "\n"

    def _build_flight_footer(self, search_params: Dict[str, Any], flight_count: int) -> str:
        """Build footer for flight results."""
        footer = "\n" + "─" * 40 + "\n\n"
        footer += "**ℹ️ INFORMATION:**\n"
        footer += "• Simulated results for demonstration\n"
        footer += "• Prices in Indian Rupees (INR)\n"
        footer += f"• **{flight_count} flights found**\n\n"

        footer += "**📞 FOR ACTUAL BOOKINGS:**\n"
        footer += "• **Phone:** 1-800-180-1407\n"
        footer += "• **Web:** https://www.airindia.com\n"
        footer += "• **App:** Air India mobile app\n"

        return footer

    def _build_policy_response(
            self,
            action_result: Dict[str, Any],
            user_query: Optional[str] = None
    ) -> str:
        """Build formatted response for policy queries."""

        result_type = action_result.get("type", "")

        if result_type == "policy_answer":
            answer = action_result.get("answer", "")
            context = action_result.get("context", {})

            # Build structured response
            response = "🧳 **AIR INDIA - POLICY INFORMATION**\n\n"

            # Add search context if available
            if context and context.get("found", False):
                docs_count = context.get("count", 0)
                response += f"_Based on {docs_count} official documents_\n\n"

            # Add main answer
            if answer:
                # Limit length if too long
                if len(answer) > 1500:
                    answer = answer[:1500] + "...\n\n_(response truncated for length)_"
                response += answer
            else:
                response += "ℹ️ No specific information found for your query.\n\n"
                response += "**💡 SUGGESTIONS:**\n"
                response += "• Visit https://www.airindia.com for complete policies\n"
                response += "• Call 1-800-180-1407 for assistance\n"

            # Add disclaimer
            response += "\n" + "─" * 30 + "\n"
            response += "_Information provided by Air India RAG system_"

            return response

        elif result_type == "policy_fallback":
            # Fallback when RAG is not available
            response = "⚠️ **POLICY SYSTEM TEMPORARILY UNAVAILABLE**\n\n"
            response += f"**QUERY:** {user_query}\n\n"
            response += "**ℹ️ GENERAL AIR INDIA INFORMATION:**\n"
            response += "• **Checked baggage:** 23kg (international) / 15kg (domestic)\n"
            response += "• **Cabin baggage:** 7kg maximum\n"
            response += "• **Online check-in:** 48 hours before flight\n"
            response += "• **Airport check-in:** Closes 60min (intl) / 45min (dom)\n\n"
            response += "**🔗 FOR EXACT INFORMATION:**\n"
            response += "https://www.airindia.com/in/en/travel-information/baggage.html"

            return response

        else:
            return "🧳 Consulting Air India policies..."

    def _build_general_response(self, user_query: Optional[str] = None) -> str:
        """Build response for general chat."""

        if not user_query:
            return "👋 **NAMASTE!**\n\nI am Maharaja, your Air India assistant. How can I help you today?"

        user_query_lower = user_query.lower()

        # Predefined responses for common cases
        if any(greeting in user_query_lower for greeting in ["hi", "hello", "hey", "namaste", "hola"]):
            return self._build_greeting_response()

        elif any(bye in user_query_lower for bye in ["bye", "thanks", "thank you", "gracias"]):
            return self._build_farewell_response()

        elif any(help_word in user_query_lower for help_word in ["help", "what can you do", "capabilities"]):
            return self._build_help_response()

        elif any(word in user_query_lower for word in ["maharaja club", "loyalty", "benefits", "frequent flyer"]):
            return self._build_maharaja_club_response()

        else:
            # Use template for general responses
            template = self.templates["general_chat"]
            return template.format(query=user_query)

    def _build_greeting_response(self) -> str:
        """Build greeting response."""
        greeting = "👋 **NAMASTE!**\n\n"
        greeting += "I am **Maharaja**, your virtual assistant for **Air India**.\n\n"
        greeting += "**🛠️ I CAN HELP YOU WITH:**\n\n"
        greeting += "• ✈️ **Flight search** and bookings\n"
        greeting += "• 🧳 **Baggage policies** and allowances\n"
        greeting += "• 🎫 **Check-in information** and procedures\n"
        greeting += "• ℹ️ **General questions** about Air India services\n\n"
        greeting += "**How may I assist you today?**"

        return greeting

    def _build_farewell_response(self) -> str:
        """Build farewell response."""
        farewell = "🙏 **THANK YOU FOR USING AIR INDIA ASSISTANT**\n\n"
        farewell += "We look forward to welcoming you on board.\n\n"
        farewell += "**📱 USEFUL RESOURCES:**\n"
        farewell += "• **Web:** https://www.airindia.com\n"
        farewell += "• **Phone:** 1-800-180-1407\n"
        farewell += "• **App:** Air India mobile app (iOS/Android)\n\n"
        farewell += "**🛫 Safe travels!**"

        return farewell

    def _build_help_response(self) -> str:
        """Build help response."""
        help_text = "❓ **HOW CAN I HELP YOU?**\n\n"

        help_text += "**📋 EXAMPLES OF WHAT YOU CAN ASK:**\n\n"

        help_text += "**✈️ FLIGHTS:**\n"
        help_text += "• 'Flights from Delhi to Mumbai tomorrow'\n"
        help_text += "• 'Search flights DEL to BOM'\n"
        help_text += "• 'Flight schedules to Bangalore'\n\n"

        help_text += "**🧳 BAGGAGE:**\n"
        help_text += "• 'Baggage policy for USA flights'\n"
        help_text += "• 'Cabin baggage limit'\n"
        help_text += "• 'Special baggage (bicycles, pets)'\n\n"

        help_text += "**🎫 CHECK-IN:**\n"
        help_text += "• 'How to do online check-in'\n"
        help_text += "• 'Airport check-in procedures'\n"
        help_text += "• 'Required documentation'\n\n"

        help_text += "**🏆 MAHARAJA CLUB:**\n"
        help_text += "• 'Mahaaraja Club benefits'\n"
        help_text += "• 'Loyalty program details'\n"
        help_text += "• 'How to earn miles'\n\n"

        help_text += "**💬 JUST TELL ME WHAT YOU NEED!**"

        return help_text

    def _build_maharaja_club_response(self) -> str:
        """Build response for Maharaja Club queries."""
        response = "🏆 **MAHARAJA CLUB - LOYALTY PROGRAM**\n\n"

        response += "**🌟 BENEFITS:**\n"
        response += "• Earn miles on every flight\n"
        response += "• Priority check-in and boarding\n"
        response += "• Extra baggage allowance\n"
        response += "• Lounge access at select airports\n"
        response += "• Seat selection preference\n\n"

        response += "**📊 TIERS:**\n"
        response += "• **Red:** Entry level\n"
        response += "• **Silver:** 25,000+ miles/year\n"
        response += "• **Gold:** 50,000+ miles/year\n"
        response += "• **Platinum:** 100,000+ miles/year\n\n"

        response += "**🔗 FOR DETAILED INFORMATION:**\n"
        response += "• Visit: https://www.airindia.com/maharaja-club\n"
        response += "• Call: 1-800-180-1407\n"
        response += "• Email: maharajaclub@airindia.com\n\n"

        response += "_Note: Specific benefits vary by tier and route_"

        return response

    def _build_error_response(self, action_result: Dict[str, Any]) -> str:
        """Build error response."""
        error_type = action_result.get("type", "unknown_error")
        details = action_result.get("details", "Unknown error")

        # Template simplificado sin campos problemáticos
        response = "⚠️ **SOMETHING WENT WRONG**\n\n"
        response += f"**Error type:** {error_type}\n"

        if details and "terminal" not in str(details).lower():
            response += f"**Details:** {details}\n\n"

        response += "**🔄 PLEASE TRY:**\n"
        response += "1. Rephrasing your question\n"
        response += "2. Checking your internet connection\n"
        response += "3. Trying again in a few minutes\n\n"

        response += "**📞 IF THE PROBLEM PERSISTS:**\n"
        response += "**Air India Support:** 1-800-180-1407"

        return response

    def _build_fallback_response(self, intent: str, user_query: Optional[str] = None) -> str:
        """Build fallback response for unrecognized intents."""
        response = "🤔 **I'M NOT SURE HOW TO HELP WITH THAT**\n\n"

        if user_query:
            response += f"**Your query:** '{user_query}'\n\n"

        response += "**💡 PERHAPS YOU WANTED TO ASK ABOUT:**\n"
        response += "• ✈️ Flights and bookings\n"
        response += "• 🧳 Baggage policies\n"
        response += "• 🎫 Check-in and documentation\n"
        response += "• 🏆 Maharaja Club benefits\n"
        response += "• 🍽️ In-flight services\n\n"

        response += "**🔄 OR TRY REPHRASING YOUR QUESTION.**"

        return response

    # ==================== TEMPLATES ====================

    def _get_flight_header_template(self) -> str:
        """Template for flight results header."""
        return """✈️ AIR INDIA - SEARCH RESULTS

ROUTE: {origin} → {destination}
DATE: {date}

{line}

"""

    def _get_flight_item_template(self) -> str:
        """Template for individual flight item - CORREGIDO."""
        return """{index}. {flight_number} - {departure} → {arrival} ({duration})
   PRICE: {price}
   STATUS: {status}
   AIRCRAFT: {aircraft}
   SEATS: {seats}"""

    def _get_policy_response_template(self) -> str:
        """Template for policy responses."""
        return """🧳 AIR INDIA - POLICY INFORMATION

{content}

{line}

Based on official Air India documents"""

    def _get_general_chat_template(self) -> str:
        """Template for general chat."""
        return """**QUERY:** {query}

As an Air India assistant, I specialize in:
• ✈️ Flight information and bookings
• 🧳 Baggage policies and check-in procedures
• 🏆 Maharaja Club loyalty program
• ℹ️ General Air India services

For queries outside these topics, I recommend:
🔗 **Web:** https://www.airindia.com
📞 **Phone:** 1-800-180-1407"""

    def _get_error_template(self) -> str:
        """Template for errors."""
        return """⚠️ SOMETHING WENT WRONG

ERROR TYPE: {error_type}

Please try:
1. Rephrasing your question
2. Checking your internet connection
3. Trying again in a few minutes

If the problem persists, contact:
📞 AIR INDIA SUPPORT: 1-800-180-1407"""

    # ==================== UTILITY METHODS ====================

    def truncate_text(self, text: str, max_length: int = None) -> str:
        """Truncate text if too long."""
        if max_length is None:
            max_length = self.max_length

        if len(text) <= max_length:
            return text

        # Truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > 0:
            truncated = truncated[:last_space]

        return truncated + "..."

    def wrap_text(self, text: str, width: int = 80) -> str:
        """Wrap text to specific width."""
        return '\n'.join(textwrap.wrap(text, width=width))

    def add_timestamp(self, text: str) -> str:
        """Add timestamp to response."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{text}\n\n_[Generated: {timestamp}]_"


# Factory function
def create_response_builder(max_length: int = 2000) -> ResponseBuilder:
    """
    Create and configure a ResponseBuilder.

    Args:
        max_length: Maximum response length

    Returns:
        Configured ResponseBuilder instance
    """
    return ResponseBuilder(max_length=max_length)


if __name__ == "__main__":
    # Usage example
    builder = create_response_builder()

    # Test with different response types
    test_data = {
        "flight_search": {
            "type": "flight_results",
            "data": {
                "success": True,
                "flights": [
                    {
                        "flight_number": "AI 865",
                        "departure_time": "06:00",
                        "arrival_time": "08:10",
                        "duration": "2h 10m",
                        "prices": {"Economy": "₹4,500"},
                        "status": "On Time",
                        "aircraft": "Airbus A320",
                        "available_seats": 45
                    }
                ],
                "search_params": {
                    "origin": "DEL",
                    "destination": "BOM",
                    "date": "tomorrow",
                    "origin_city": "Delhi",
                    "destination_city": "Mumbai"
                }
            }
        },
        "policy_question": {
            "type": "policy_answer",
            "answer": "For Air India international flights, the allowed baggage is 23kg for checked baggage and 7kg for cabin baggage in Economy class."
        }
    }

    for intent, data in test_data.items():
        print(f"\n{'=' * 60}")
        print(f"Test: {intent}")
        response = builder.build_response(intent, data)
        print(response[:200] + "...")