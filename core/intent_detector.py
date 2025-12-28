"""
Intent Detector for Air India Chatbot.
Classifies user messages into flight search, policy questions, or general chat.
Now refactored to use constants and utilities from separate modules.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

from flight_data.constants import (
    FLIGHT_KEYWORDS, POLICY_KEYWORDS, GREETING_KEYWORDS,
    FLIGHT_PATTERNS, POLICY_PATTERNS, CITY_PATTERNS,
    INVALID_IATA_CODES, AIRPORTS
)
from flight_data.utils import (
    normalize_city_name, is_valid_iata_code, parse_date_string, extract_iata_codes
)
from flight_data.context_manager import IntentType, ConversationContext

# Set up logging
logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Intelligent intent detection for airline chatbot.

    Features:
    1. Pattern-based detection (fast and accurate)
    2. Keyword-based fallback
    3. Parameter extraction (cities, dates, IATA codes)
    4. Confidence scoring
    5. Optional LLM fallback for ambiguous cases
    """

    def __init__(self, use_llm_fallback: bool = False, context: Optional[ConversationContext] = None):
        """
        Initialize the intent detector.

        Args:
            use_llm_fallback: Whether to use LLM for ambiguous cases
            context: Optional conversation context for multi-turn
        """
        self.use_llm_fallback = use_llm_fallback
        self.context = context

        # Compile regex patterns for better performance
        self.compiled_patterns = {
            "flight": [re.compile(pattern, re.IGNORECASE) for pattern in FLIGHT_PATTERNS],
            "policy": [re.compile(pattern, re.IGNORECASE) for pattern in POLICY_PATTERNS]
        }

        logger.info("IntentDetector initialized")

    def detect_intent(self, user_message: str) -> Dict[str, any]:
        """
        Main intent detection method.

        Args:
            user_message: Raw user input

        Returns:
            Dictionary with intent, confidence, parameters, etc.
        """
        if not user_message or not user_message.strip():
            return self._build_response(
                intent=IntentType.GENERAL_CHAT,
                confidence=0.1,
                parameters={},
                reason="empty_message"
            )

        message = user_message.strip()
        message_lower = message.lower()

        logger.debug(f"Detecting intent for: '{message}'")

        # ====================================================================
        # STEP 1: PATTERN-BASED DETECTION (Highest priority)
        # ====================================================================

        # Check flight patterns
        for pattern in self.compiled_patterns["flight"]:
            if pattern.search(message):
                params = self._extract_flight_parameters(message)
                logger.info(f"Flight pattern matched: {pattern.pattern}")
                return self._build_response(
                    intent=IntentType.FLIGHT_SEARCH,
                    confidence=0.95,
                    parameters=params,
                    reason="flight_pattern"
                )

        # Check policy patterns
        for pattern in self.compiled_patterns["policy"]:
            if pattern.search(message):
                logger.info(f"Policy pattern matched: {pattern.pattern}")
                return self._build_response(
                    intent=IntentType.POLICY_QUESTION,
                    confidence=0.92,
                    parameters={},
                    reason="policy_pattern"
                )

        # ====================================================================
        # STEP 2: CONTEXT-AWARE DETECTION (if context is available)
        # ====================================================================

        if self.context and self.context.last_intent == IntentType.FLIGHT_SEARCH:
            # Check if this is a follow-up to a flight search
            reference = self.context.resolve_reference(message)
            if reference.get("has_reference", False):
                logger.info("Context reference detected")
                return self._build_response(
                    intent=IntentType.FLIGHT_SEARCH,
                    confidence=0.88,
                    parameters=reference,
                    reason="context_reference"
                )

        # ====================================================================
        # STEP 3: KEYWORD-BASED DETECTION
        # ====================================================================

        # Count keyword occurrences
        flight_score = self._count_keywords(message_lower, FLIGHT_KEYWORDS)
        policy_score = self._count_keywords(message_lower, POLICY_KEYWORDS)
        greeting_score = self._count_keywords(message_lower, GREETING_KEYWORDS)

        logger.debug(f"Keyword scores - Flight: {flight_score}, Policy: {policy_score}, Greeting: {greeting_score}")

        # Rule 1: If it's clearly a greeting with no other intent
        if greeting_score >= 1 and flight_score == 0 and policy_score == 0:
            logger.info("Greeting detected")
            return self._build_response(
                intent=IntentType.GENERAL_CHAT,
                confidence=0.90,
                parameters={},
                reason="greeting"
            )

        # Rule 2: Flight keywords with IATA codes
        if flight_score >= 2:
            params = self._extract_flight_parameters(message)

            # Extra confidence if we found valid IATA codes
            if params.get("origin") and params.get("destination"):
                confidence = 0.89
                reason = "flight_keywords_with_codes"
            else:
                confidence = 0.75
                reason = "flight_keywords_no_codes"

            logger.info(f"Flight keywords detected: {reason}")
            return self._build_response(
                intent=IntentType.FLIGHT_SEARCH,
                confidence=confidence,
                parameters=params,
                reason=reason
            )

        # Rule 3: Policy keywords
        if policy_score >= 2:
            logger.info("Policy keywords detected")
            return self._build_response(
                intent=IntentType.POLICY_QUESTION,
                confidence=0.80,
                parameters={},
                reason="policy_keywords"
            )

        # Rule 4: Baggage without flight context
        if ("baggage" in message_lower or "luggage" in message_lower) and flight_score == 0:
            logger.info("Baggage query without flight context")
            return self._build_response(
                intent=IntentType.POLICY_QUESTION,
                confidence=0.85,
                parameters={},
                reason="baggage_only"
            )

        # ====================================================================
        # STEP 4: FALLBACK DETECTION
        # ====================================================================

        # Check for IATA codes even without explicit flight keywords
        origin, destination = extract_iata_codes(message)
        if origin and destination:
            logger.info("IATA codes detected without flight keywords")
            params = self._extract_flight_parameters(message)
            return self._build_response(
                intent=IntentType.FLIGHT_SEARCH,
                confidence=0.70,
                parameters=params,
                reason="iata_codes_only"
            )

        # ====================================================================
        # STEP 5: LLM FALLBACK (if enabled and still uncertain)
        # ====================================================================

        if self.use_llm_fallback:
            # This would call Ollama or another LLM for ambiguous cases
            llm_intent = self._llm_intent_fallback(message)
            if llm_intent:
                logger.info(f"LLM fallback used: {llm_intent}")
                return llm_intent

        # ====================================================================
        # STEP 6: DEFAULT (general chat)
        # ====================================================================

        logger.info("Defaulting to general chat")
        return self._build_response(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.30,
            parameters={},
            reason="default"
        )

    def _extract_flight_parameters(self, message: str) -> Dict[str, any]:
        """
        Extrae parámetros de búsqueda de vuelos.
        AHORA SÍ funciona con nombres de ciudades.
        """
        from flight_data.utils import extract_flight_parameters

        print(f"DEBUG _extract_flight_parameters: Procesando: '{message}'")

        # Usar la nueva función mejorada
        params = extract_flight_parameters(message)

        # Asegurar que tenemos los campos necesarios
        params["raw_message"] = message

        print(
            f"DEBUG _extract_flight_parameters: Resultado: origin={params.get('origin')}, dest={params.get('destination')}")

        return params

    def _count_keywords(self, text: str, keywords: list) -> int:
        """
        Count how many keywords from the list appear in the text.

        Args:
            text: Text to search in
            keywords: List of keywords to search for

        Returns:
            Count of unique keywords found
        """
        found_keywords = set()

        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_keywords.add(keyword.lower())

        return len(found_keywords)

    def _llm_intent_fallback(self, message: str) -> Optional[Dict]:
        """
        Use LLM (Ollama) for intent classification in ambiguous cases.
        This is an optional feature that can be enabled.

        Args:
            message: User message

        Returns:
            Intent dictionary or None if LLM is not available
        """
        # This would integrate with your Ollama setup
        # For now, return None (not implemented)
        return None

    def _build_response(self,
                        intent: IntentType,
                        confidence: float,
                        parameters: Dict,
                        reason: str) -> Dict[str, any]:
        """
        Build a standardized response dictionary.

        Args:
            intent: Detected intent
            confidence: Confidence score (0.0 to 1.0)
            parameters: Extracted parameters
            reason: Why this intent was chosen

        Returns:
            Standardized intent response dictionary
        """
        return {
            "intent": intent.value,
            "confidence": round(confidence, 3),
            "parameters": parameters,
            "raw_message": parameters.get("raw_message", ""),
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "success": True
        }