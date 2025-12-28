import unittest
import time
from core.chatbot_engine import create_chatbot_engine


class TestChatbotQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup shared engine"""
        cls.engine = create_chatbot_engine(debug_mode=True)

    def test_policy_queries(self):
        """Test policy questions - accuracy and latency"""
        test_cases = [
            {
                "query": "What's the baggage allowance for international flights?",
                "expected_keywords": ["23kg", "checked", "carry-on"],
                "max_latency": 5.0
            },
            {
                "query": "Baggage allowance for USA flights",
                "expected_keywords": ["2 pieces", "23kg each", "USA/Canada"],
                "max_latency": 5.0
            },
            {
                "query": "Baggage policy for Sri Lanka",
                "expected_keywords": ["30kg", "weight concept"],
                "max_latency": 5.0
            },
            {
                "query": "Check-in policy",
                "expected_keywords": ["online", "airport", "time"],
                "max_latency": 5.0
            }
        ]

        for case in test_cases:
            with self.subTest(query=case["query"]):
                start = time.time()
                response = self.engine.process_query(case["query"])
                latency = time.time() - start

                # Accuracy: check keywords
                accuracy = all(kw.lower() in response.raw_response.lower() for kw in case["expected_keywords"])
                self.assertTrue(accuracy, f"Missing keywords in response for {case['query']}")

                # Latency
                self.assertLess(latency, case["max_latency"], f"Latency too high: {latency}s")

                # Relevance: not fallback/vague
                self.assertNotIn("unavailable", response.raw_response.lower())
                self.assertGreater(len(response.raw_response), 50)  # Not too short

    def test_flight_queries(self):
        """Test flight searches - accuracy and latency"""
        test_cases = [
            {
                "query": "Flights from Delhi to Mumbai tomorrow",
                "expected_keywords": ["DEL", "BOM", "AI", "price", "time"],
                "max_latency": 3.0
            },
            {
                "query": "Flights from Mumbai to Bangalore next week",
                "expected_keywords": ["BOM", "BLR", "flight", "duration"],
                "max_latency": 3.0
            }
        ]

        for case in test_cases:
            with self.subTest(query=case["query"]):
                start = time.time()
                response = self.engine.process_query(case["query"])
                latency = time.time() - start

                accuracy = all(kw.lower() in response.raw_response.lower() for kw in case["expected_keywords"])
                self.assertTrue(accuracy)
                self.assertLess(latency, case["max_latency"])
                self.assertNotIn("no flights", response.raw_response.lower())  # Relevance

    def test_general_queries(self):
        """Test general chat - relevance and latency"""
        test_cases = [
            {
                "query": "Tell me about Air India",
                "expected_keywords": ["Maharaja", "airline", "India"],
                "max_latency": 2.0
            },
            {
                "query": "Can you book a hotel?",
                "expected_keywords": ["specialize in flights", "recommend"],
                "max_latency": 2.0
            }
        ]

        for case in test_cases:
            with self.subTest(query=case["query"]):
                start = time.time()
                response = self.engine.process_query(case["query"])
                latency = time.time() - start

                accuracy = all(kw.lower() in response.raw_response.lower() for kw in case["expected_keywords"])
                self.assertTrue(accuracy)
                self.assertLess(latency, case["max_latency"])
                self.assertGreater(len(response.raw_response), 50)  # Relevant length

    def test_multi_turn_queries(self):
        """Test multi-turn conversation"""
        # Simulate multi-turn
        self.engine.process_query("Flights from Delhi to Mumbai tomorrow")  # First query to set context

        test_cases = [
            {
                "query": "What about the 9:30 flight?",
                "expected_keywords": ["AI 677", "9:30", "details"],
                "max_latency": 3.0
            }
        ]

        for case in test_cases:
            with self.subTest(query=case["query"]):
                start = time.time()
                response = self.engine.process_query(case["query"])
                latency = time.time() - start

                accuracy = all(kw.lower() in response.raw_response.lower() for kw in case["expected_keywords"])
                self.assertTrue(accuracy)
                self.assertLess(latency, case["max_latency"])


if __name__ == '__main__':
    unittest.main()