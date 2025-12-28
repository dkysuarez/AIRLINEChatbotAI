"""
CHATBOT ENGINE - MAIN ORCHESTRATOR
========================================

Responsibility: Coordinate all components to process user queries.
Contains no UI logic, only business logic.

Flow:
1. Receive user query
2. Detect intent
3. Execute specific action (flights, policies, general chat)
4. Return structured result for UI
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ChatbotResponse:
    """Data structure for standardized responses."""
    raw_response: str  # Formatted text to display to user
    intent: str  # Detected intent
    confidence: float  # Confidence score (0.0 to 1.0)
    raw_data: Optional[Dict] = None  # Raw data (flights, policies, etc.)
    metadata: Optional[Dict] = None  # Additional metadata
    processing_time: Optional[float] = None  # Processing time in seconds
    source: Optional[str] = None  # Response source (RAG, FlightDB, etc.)


class ChatbotEngine:
    """
    Main engine for Air India chatbot.
    """

    def __init__(self, debug_mode: bool = False):
        """
        Initialize the chatbot engine.
        """
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)

        if debug_mode:
            logging.basicConfig(level=logging.DEBUG)

        # Initialize components
        self._initialize_components()

        # Statistics
        self.stats = {
            "total_queries": 0,
            "intent_distribution": {},
            "average_processing_time": 0.0
        }

        # Conversation context (optional)
        self.context = None

        self.logger.info("ChatbotEngine initialized successfully")

    def _initialize_components(self) -> None:
        """Initialize and verify all necessary components."""
        self.logger.info("Initializing components...")

        # 1. Intent Detector (delayed import to avoid circular dependencies)
        try:
            from core.intent_detector import IntentDetector
            self.intent_detector = IntentDetector()
            self.logger.info("IntentDetector ready")
        except ImportError as e:
            self.logger.error(f"Cannot import IntentDetector: {e}")
            self.intent_detector = self._create_fallback_intent_detector()

        # 2. Mock flight database
        try:
            from flight_data.mock_flights import MockFlightDatabase
            self.flight_db = MockFlightDatabase()
            self.logger.info("Flight Database ready")
        except ImportError as e:
            self.logger.error(f"Cannot import FlightDatabase: {e}")
            self.flight_db = self._create_fallback_flight_db()

        # 3. RAG system for policies
        self.rag_handler = None
        try:
            from rag.rag_handler import create_rag_handler
            self.rag_handler = create_rag_handler()
            if self.rag_handler and hasattr(self.rag_handler, 'is_initialized') and self.rag_handler.is_initialized:
                self.logger.info("RAG Handler ready")
            else:
                self.logger.warning("RAG Handler not initialized (fallback mode)")
        except ImportError as e:
            self.logger.error(f"Cannot import RAG Handler: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing RAG: {e}")

        self.logger.info("All components initialized")

    def _create_fallback_intent_detector(self):
        """Create a fallback intent detector when main one fails."""
        class FallbackIntentDetector:
            def detect_intent(self, user_message: str) -> Dict[str, any]:
                return {
                    "intent": "general_chat",
                    "confidence": 0.1,
                    "parameters": {},
                    "reason": "fallback"
                }
        return FallbackIntentDetector()

    def _create_fallback_flight_db(self):
        """Create a fallback flight database."""
        class FallbackFlightDB:
            def search_flights(self, origin: str, destination: str, date: str = "tomorrow") -> Dict[str, Any]:
                return {
                    "success": False,
                    "error": "Flight database unavailable",
                    "flights": [],
                    "total_flights": 0
                }
        return FallbackFlightDB()

    def process_query(
            self,
            user_query: str,
            conversation_history: Optional[List[Dict]] = None,
            context_manager=None,  # Optional context manager
            **kwargs
    ) -> ChatbotResponse:
        """
        Process a user query and return a structured response.
        """
        start_time = time.time()
        self.stats["total_queries"] += 1

        self.logger.debug(f"Processing query: '{user_query}'")

        # Basic validation
        if not user_query or not user_query.strip():
            return self._build_empty_response()

        user_query = user_query.strip()

        try:
            # Use context manager if provided
            if context_manager and hasattr(context_manager, 'resolve_reference'):
                # Check if this is a reference to previous context
                reference = context_manager.resolve_reference(user_query)
                if reference.get("has_reference", False):
                    self.logger.info(f"Context reference detected: {reference.get('reference_type')}")
                    # Handle reference-based query
                    return self._handle_context_reference(reference, user_query)

            # STEP 1: DETECT INTENT
            intent_result = self._detect_intent(user_query, conversation_history)
            intent = intent_result.get("intent", "general_chat")
            confidence = intent_result.get("confidence", 0.0)

            # Update context manager if provided
            if context_manager and hasattr(context_manager, 'add_message'):
                context_manager.add_message(
                    role="user",
                    content=user_query,
                    intent=intent,
                    parameters=intent_result.get("parameters", {})
                )

            self._update_intent_stats(intent)

            # STEP 2: EXECUTE ACTION BASED ON INTENT
            action_result = self._execute_action(intent, intent_result, user_query)

            # STEP 3: FORMAT RESPONSE
            formatted_response = self._format_response(intent, action_result, user_query)

            # STEP 4: BUILD STRUCTURED RESPONSE
            processing_time = time.time() - start_time
            self._update_processing_stats(processing_time)

            response = ChatbotResponse(
                raw_response=formatted_response,
                intent=intent,
                confidence=confidence,
                raw_data=action_result,
                metadata={
                    "processing_time": round(processing_time, 3),
                    "query_length": len(user_query),
                    "has_history": bool(conversation_history),
                    "context_used": context_manager is not None
                },
                processing_time=processing_time,
                source=self._get_response_source(intent, action_result)
            )

            # Update context with flight results if applicable
            if context_manager and intent == "flight_search":
                if action_result.get("type") == "flight_results":
                    flights = action_result.get("data", {}).get("flights", [])
                    if flights:
                        context_manager.update_flight_results(flights)

            self.logger.info(f"Query processed: {intent} ({processing_time:.2f}s)")
            return response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return self._build_error_response(user_query, str(e))

    def _handle_context_reference(self, reference: Dict, user_query: str) -> ChatbotResponse:
        """Handle queries that reference previous context."""
        try:
            reference_type = reference.get("reference_type")
            flight = reference.get("referenced_flight")

            if reference_type in ["time", "ordinal", "flight_number", "generic"] and flight:
                # User is asking about a specific flight from previous results
                flight_info = self._format_flight_details(flight)

                return ChatbotResponse(
                    raw_response=flight_info,
                    intent="flight_details",
                    confidence=0.9,
                    raw_data={"flight": flight, "reference_type": reference_type},
                    metadata={"reference": reference_type},
                    source="flight_database"
                )

        except Exception as e:
            self.logger.error(f"Error handling context reference: {e}")

        # Fallback to normal processing
        return self._build_error_response(user_query, "Could not process reference")

    def _format_flight_details(self, flight: Dict) -> str:
        """Format detailed flight information."""
        flight_num = flight.get("flight_number", "N/A")
        departure = flight.get("departure_time", "N/A")
        arrival = flight.get("arrival_time", "N/A")
        duration = flight.get("duration", "N/A")
        aircraft = flight.get("aircraft", "N/A")
        status = flight.get("status", "Scheduled")

        # Handle price
        prices = flight.get("prices", {})
        if isinstance(prices, dict):
            price = prices.get("Economy", "₹ N/A")
        else:
            price = prices if prices else "₹ N/A"

        response = f"✈️ **Flight {flight_num} Details:**\n\n"
        response += f"**Departure:** {departure}\n"
        response += f"**Arrival:** {arrival} ({duration})\n"
        response += f"**Aircraft:** {aircraft}\n"
        response += f"**Status:** {status}\n"
        response += f"**Price:** {price} (Economy)\n\n"

        # Add optional fields if they exist
        if flight.get("terminal"):
            response += f"**Terminal:** {flight['terminal']}\n"
        if flight.get("gate"):
            response += f"**Gate:** {flight['gate']}\n"
        if flight.get("baggage_allowance"):
            response += f"**Baggage:** {flight['baggage_allowance'].get('checked', 'N/A')} checked\n"

        response += "\n💡 *For bookings, visit www.airindia.com or call 1-800-180-1407*"

        return response

    def _detect_intent(
            self,
            user_query: str,
            conversation_history: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Detect user intent."""
        try:
            # Use intent detector
            result = self.intent_detector.detect_intent(user_query)
            return result
        except Exception as e:
            self.logger.error(f"Error in intent detection: {e}")
            return {"intent": "general_chat", "confidence": 0.1, "parameters": {}}

    def _execute_action(
            self,
            intent: str,
            intent_result: Dict[str, Any],
            user_query: str
    ) -> Dict[str, Any]:
        """Execute action corresponding to the intent."""

        if intent == "flight_search":
            return self._handle_flight_search(intent_result, user_query)

        elif intent == "policy_question":
            return self._handle_policy_query(user_query)

        else:  # general_chat or others
            return self._handle_general_chat(user_query)

    def _handle_flight_search(
            self,
            intent_result: Dict[str, Any],
            user_query: str
    ) -> Dict[str, Any]:
        """Handle flight searches."""
        try:
            params = intent_result.get("parameters", {})
            origin = params.get("origin")
            destination = params.get("destination")
            date = params.get("date", "tomorrow")

            if not origin or not destination:
                return {
                    "type": "error",
                    "message": "Missing origin or destination",
                    "suggestion": "Please specify both cities (e.g., 'DEL to BOM')"
                }

            # Search flights
            flight_results = self.flight_db.search_flights(origin, destination, date)

            return {
                "type": "flight_results",
                "data": flight_results,
                "query": user_query,
                "params": params
            }

        except Exception as e:
            self.logger.error(f"Error in flight search: {e}")
            return {
                "type": "error",
                "message": "Error searching flights",
                "details": str(e)
            }

    def _handle_policy_query(self, user_query: str) -> Dict:
        """Handle policy questions with robust error handling."""
        try:
            if self.rag_handler and self.rag_handler.is_initialized:
                answer = self.rag_handler.get_answer(user_query)
                source = "rag_system"
            else:
                answer = ("I couldn't access detailed policies right now. "
                          "Common Economy international allowance: 1 checked bag up to 23 kg + 1 carry-on up to 8 kg.")
                source = "fallback"
        except Exception as e:
            logger.error(f"Policy handler error: {e}")
            answer = "Sorry, policy information is temporarily unavailable. Please try again."
            source = "error"

        return {
            "type": "policy_answer",
            "answer": answer,
            "source": source
        }
    def _handle_general_chat(self, user_query: str) -> Dict[str, Any]:
        """Handle general chat."""
        # Simple response object
        return {
            "type": "general_chat",
            "query": user_query,
            "requires_llm": True
        }

    def _format_response(
            self,
            intent: str,
            action_result: Dict[str, Any],
            user_query: str
    ) -> str:
        """Format response for user."""

        if intent == "flight_search":
            data = action_result.get("data", {})
            if data.get("success", False):
                flights = data.get("flights", [])
                if flights:
                    return f"Found {len(flights)} flights for your search."
                else:
                    return "No flights found for that route."
            else:
                return "Could not search flights at this time."

        elif intent == "policy_question":
            answer = action_result.get("answer", "")
            if answer:
                return answer[:500] + "..." if len(answer) > 500 else answer
            else:
                return "Consulting Air India policies..."

        elif intent == "flight_details":
            # This is for context references
            flight = action_result.get("flight", {})
            flight_num = flight.get("flight_number", "flight")
            return f"Here are the details for {flight_num}."

        else:
            return "How can I help you with Air India today?"

    def _build_empty_response(self) -> ChatbotResponse:
        """Build response for empty queries."""
        return ChatbotResponse(
            raw_response="Please enter your question about Air India.",
            intent="general_chat",
            confidence=0.0,
            metadata={"reason": "empty_query"}
        )

    def _build_error_response(self, user_query: str, error: str) -> ChatbotResponse:
        """Build error response."""
        return ChatbotResponse(
            raw_response=f"An error occurred processing your query: '{user_query}'. Please try again.",
            intent="error",
            confidence=0.0,
            metadata={"error": error, "query": user_query}
        )

    def _update_intent_stats(self, intent: str) -> None:
        """Update intent statistics."""
        self.stats["intent_distribution"][intent] = \
            self.stats["intent_distribution"].get(intent, 0) + 1

    def _update_processing_stats(self, processing_time: float) -> None:
        """Update processing time statistics."""
        total = self.stats["total_queries"]
        current_avg = self.stats["average_processing_time"]

        # Moving average
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.stats["average_processing_time"] = new_avg

    def _get_response_source(self, intent: str, action_result: Dict) -> str:
        """Determine response source."""
        if intent == "flight_search":
            return "flight_database"
        elif intent == "policy_question":
            return action_result.get("source", "rag_system")
        else:
            return "general_chat"

    def get_stats_summary(self) -> Dict[str, Any]:
        """Return statistics summary."""
        return {
            "total_queries": self.stats["total_queries"],
            "intent_distribution": self.stats["intent_distribution"],
            "avg_processing_time": round(self.stats["average_processing_time"], 3),
            "rag_available": bool(self.rag_handler and hasattr(self.rag_handler, 'is_initialized') and self.rag_handler.is_initialized)
        }


# Factory function for easy creation
def create_chatbot_engine(debug_mode: bool = False) -> ChatbotEngine:
    """
    Create and configure a ChatbotEngine instance.
    """
    return ChatbotEngine(debug_mode=debug_mode)


if __name__ == "__main__":
    # Usage example
    engine = create_chatbot_engine(debug_mode=True)

    # Test with different queries
    test_queries = [
        "flights from Delhi to Mumbai tomorrow",
        "baggage policy for international flights",
        "hello, how are you?"
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: '{query}'")
        response = engine.process_query(query)
        print(f"Intent: {response.intent} (confidence: {response.confidence})")
        print(f"Response: {response.raw_response[:100]}...")
        print(f"Time: {response.processing_time:.3f}s")

    print(f"\nStatistics: {engine.get_stats_summary()}")