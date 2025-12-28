import sys
sys.path.append('.')
from core.intent_detector import IntentDetector

detector = IntentDetector()

test_queries = [
    "Flight cancellation policy",
    "Seat selection process",
    "Baggage allowance for USA flights",
    "How to check in online",
    "Mumbai to Delhi flights",
    "What is web check-in"
]

print("=" * 60)
print("TEST DE DETECCIÓN DE INTENTS")
print("=" * 60)

for query in test_queries:
    result = detector.detect_intent(query)
    print(f"\nQuery: '{query}'")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reason: {result['reason']}")
    print(f"Params: {result.get('parameters', {})}")