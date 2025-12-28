"""
Conversation Context Manager.
Handles multi-turn conversations by maintaining conversation state.
Essential for handling references like "What about the 9:30 flight?"
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class IntentType(Enum):
    """Enum for intent types."""
    FLIGHT_SEARCH = "flight_search"
    POLICY_QUESTION = "policy_question"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    intent: Optional[IntentType] = None
    parameters: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "intent": self.intent.value if self.intent else None,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat()
        }


class ConversationContext:
    """
    Manages conversation state across multiple turns.

    Key features:
    1. Maintains conversation history
    2. Tracks current flight search results
    3. Resolves references like "the 9:30 flight"
    4. Handles context switching
    """

    def __init__(self, session_id: str = "default", max_history: int = 10):
        """
        Initialize a new conversation context.

        Args:
            session_id: Unique identifier for this conversation session
            max_history: Maximum number of messages to keep in history
        """
        self.session_id = session_id
        self.max_history = max_history
        self.history: List[Message] = []

        # Current state
        self.current_flight_search: Optional[Dict] = None
        self.last_intent: Optional[IntentType] = None
        self.last_parameters: Optional[Dict] = None

        # Flight results for reference resolution
        self.last_flight_results: List[Dict] = []

    def add_message(self,
                    role: str,
                    content: str,
                    intent: Optional[IntentType] = None,
                    parameters: Optional[Dict] = None) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: Message content
            intent: Detected intent (if known)
            parameters: Extracted parameters (if any)
        """
        message = Message(
            role=role,
            content=content,
            intent=intent,
            parameters=parameters
        )

        self.history.append(message)

        # Keep history within limits
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # Update current state
        if intent:
            self.last_intent = intent
            self.last_parameters = parameters

            # If this is a flight search, store the results when they come
            if intent == IntentType.FLIGHT_SEARCH and parameters:
                self.current_flight_search = {
                    "search_params": parameters.copy(),
                    "results": []  # Will be populated when flights are found
                }

    def update_flight_results(self, flight_results: List[Dict]) -> None:
        """
        Update the context with flight search results.
        Called after a flight search returns results.

        Args:
            flight_results: List of flight dictionaries
        """
        self.last_flight_results = flight_results

        if self.current_flight_search:
            self.current_flight_search["results"] = flight_results

    def resolve_reference(self, current_message: str) -> Dict[str, Any]:
        """
        Resolve references in the current message to previous context.

        Examples:
        - "What about the 9:30 flight?" → Finds flight at 9:30
        - "The first one" → Returns first flight from last results
        - "Show me details" → Returns context for detailed view

        Args:
            current_message: The current user message

        Returns:
            Dictionary with resolved reference information
        """
        message_lower = current_message.lower()
        resolved = {"has_reference": False}

        # If no flight results, nothing to reference
        if not self.last_flight_results:
            return resolved

        # Reference by time (e.g., "the 9:30 flight")
        time_pattern = r"(\d{1,2}):?(\d{2})?\s*(?:am|pm)?"
        time_match = re.search(time_pattern, message_lower)

        if time_match:
            hour = time_match.group(1)

            # Find flight with matching departure time
            for flight in self.last_flight_results:
                dep_time = flight.get("departure_time", "")
                if dep_time.startswith(hour):
                    resolved.update({
                        "has_reference": True,
                        "reference_type": "time",
                        "referenced_flight": flight,
                        "flight_number": flight.get("flight_number"),
                        "departure_time": dep_time
                    })
                    return resolved

        # Reference by ordinal (e.g., "the first one", "second flight")
        ordinal_map = {
            "first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4,
            "last": -1, "previous": -1
        }

        for ordinal, index in ordinal_map.items():
            if ordinal in message_lower:
                if index >= 0 and index < len(self.last_flight_results):
                    flight = self.last_flight_results[index]
                elif index == -1 and self.last_flight_results:
                    flight = self.last_flight_results[-1]
                else:
                    continue

                resolved.update({
                    "has_reference": True,
                    "reference_type": "ordinal",
                    "referenced_flight": flight,
                    "flight_number": flight.get("flight_number"),
                    "ordinal": ordinal
                })
                return resolved

        # Reference by flight number (e.g., "AI 865")
        flight_num_pattern = r"(?:AI|AIX)\s*\d+"
        flight_match = re.search(flight_num_pattern, current_message.upper())

        if flight_match:
            flight_num = flight_match.group(0)
            for flight in self.last_flight_results:
                if flight.get("flight_number", "") == flight_num:
                    resolved.update({
                        "has_reference": True,
                        "reference_type": "flight_number",
                        "referenced_flight": flight,
                        "flight_number": flight_num
                    })
                    return resolved

        # Generic reference (e.g., "that flight", "it")
        generic_refs = ["that", "it", "this", "the flight"]
        if any(ref in message_lower for ref in generic_refs):
            if self.last_flight_results:
                # Return the most relevant (first) flight
                flight = self.last_flight_results[0]
                resolved.update({
                    "has_reference": True,
                    "reference_type": "generic",
                    "referenced_flight": flight,
                    "flight_number": flight.get("flight_number")
                })
                return resolved

        return resolved

    def get_conversation_summary(self) -> Dict:
        """
        Get a summary of the current conversation state.

        Returns:
            Dictionary with conversation summary
        """
        return {
            "session_id": self.session_id,
            "message_count": len(self.history),
            "last_intent": self.last_intent.value if self.last_intent else None,
            "has_flight_search": self.current_flight_search is not None,
            "flight_results_count": len(self.last_flight_results)
        }

    def clear(self) -> None:
        """Clear the conversation context (start fresh)."""
        self.history.clear()
        self.current_flight_search = None
        self.last_intent = None
        self.last_parameters = None
        self.last_flight_results = []

    def to_dict(self) -> Dict:
        """Serialize context to dictionary."""
        return {
            "session_id": self.session_id,
            "history": [msg.to_dict() for msg in self.history],
            "current_flight_search": self.current_flight_search,
            "last_intent": self.last_intent.value if self.last_intent else None,
            "last_flight_results": self.last_flight_results
        }