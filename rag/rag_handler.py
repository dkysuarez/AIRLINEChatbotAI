# rag_handler.py - VERSION MEJORADA Y CORREGIDA

"""
Simplified RAG Handler for Air India Chatbot.
Now with country-based filtering and MULTI-LANGUAGE support.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RAGHandler")

# Add to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings
    from langchain_core.documents import Document

    LANGCHAIN_AVAILABLE = True
    logger.info("✅ LangChain dependencies loaded")
except ImportError as e:
    logger.error(f"❌ Missing dependency: {e}")
    LANGCHAIN_AVAILABLE = False


class SimpleRAGHandler:
    """
    Improved RAG Handler with country-based filtering and multi-language support.

    Key improvements:
    1. Filters results by country when query mentions specific countries
    2. Better metadata handling
    3. More relevant search results
    4. Responds in the SAME LANGUAGE as user query (English/Hindi)
    """

    def __init__(self):
        """Initializes the improved RAG handler."""
        # Path configuration
        self.project_root = Path(__file__).parent.parent
        self.chroma_db_path = self.project_root / "rag" / "chroma_db"
        self.collection_name = "air_india_intelligent"

        # Components
        self.embeddings = None
        self.db = None
        self.is_initialized = False

        # Configuration
        self.k_results = 5
        self.search_k = 10  # Search more, filter down

        # Country detection patterns
        self.country_patterns = {
            "canada": [r"\bcanada\b", r"\bcanadian\b"],
            "usa": [r"\busa\b", r"\bus\b", r"\bunited states\b", r"\bamerica\b", r"\bu\.s\.\b", r"\bu\.s\.a\.\b"],
            "india": [r"\bindia\b", r"\bindian\b", r"\bdomestic\b"],
            "sri lanka": [r"\bsri lanka\b", r"\bsri lankan\b"],
            "bangladesh": [r"\bbangladesh\b"],
            "nepal": [r"\bnepal\b"],
            "maldives": [r"\bmaldives\b"],
            "australia": [r"\baustralia\b"],
            "europe": [r"\beurope\b", r"\beuropean\b", r"\buk\b", r"\bfrance\b", r"\bgermany\b"],
            "japan": [r"\bjapan\b"],
            "south korea": [r"\bsouth korea\b", r"\bkorea\b"]
        }

        logger.info(f"📁 Initializing RAG Handler")
        logger.info(f"📂 DB path: {self.chroma_db_path}")
        logger.info(f"📦 Collection: {self.collection_name}")

        self._initialize_chroma()

    def _initialize_chroma(self) -> bool:
        """Initializes ChromaDB. Returns True on success."""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available")
            return False

        try:
            # 1. Configure embeddings
            logger.info("🔤 Configuring embeddings...")
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            logger.info("✅ Embeddings ready")

            # 2. Verify database exists
            if not self.chroma_db_path.exists():
                logger.error(f"❌ Database not found at: {self.chroma_db_path}")
                logger.info("💡 First run: python -m rag.indexer")
                return False

            # 3. Load ChromaDB
            logger.info("🗄️  Loading database...")
            self.db = Chroma(
                persist_directory=str(self.chroma_db_path),
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )

            # 4. Verify it contains data
            info = self.db.get()
            count = len(info.get('ids', []))

            if count > 0:
                logger.info(f"✅ Database loaded ({count} documents)")
                self.is_initialized = True
                return True
            else:
                logger.error("❌ Database is empty")
                return False

        except Exception as e:
            logger.error(f"❌ Error initializing Chroma: {e}")
            return False

    def _detect_language(self, text: str) -> str:
        """
        Detects the language of the user query.
        Returns 'en' (English) or 'hi' (Hindi) based on content.
        """
        if not text:
            return 'en'

        text_lower = text.lower()

        # Check for Hindi characters (Devanagari Unicode range)
        hindi_chars = any('\u0900' <= char <= '\u097F' for char in text)

        # Common Hindi words (transliterated)
        hindi_indicators = [
            'namaste', 'kya', 'hai', 'kaise', 'ho', 'mein', 'aap',
            'kyun', 'kahan', 'kab', 'kitna', 'ka', 'ki', 'nahi',
            'haan', 'shukriya', 'dhanyavad', 'kripya', 'madad'
        ]

        # Check for Hindi words
        hindi_words = any(word in text_lower for word in hindi_indicators)

        # Check for English indicators (if it's definitely English)
        english_indicators = [
            'what', 'how', 'when', 'where', 'why', 'which',
            'can', 'could', 'would', 'should', 'please',
            'flight', 'baggage', 'check-in', 'air india'
        ]

        english_words = sum(1 for word in english_indicators if word in text_lower)

        # Decision logic
        if hindi_chars:
            return 'hi'
        elif hindi_words and english_words < 2:
            return 'hi'
        else:
            return 'en'  # Default to English

    def _extract_country_from_query(self, query: str) -> Optional[str]:
        """
        Extracts country mentions from query.
        Returns the first country found or None.
        """
        query_lower = query.lower()

        for country, patterns in self.country_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.debug(f"🌍 Country detected in query: {country}")
                    return country

        return None

    def _filter_by_country(self, documents: List[Document], country: str) -> List[Document]:
        """
        Filters documents by country metadata.
        Prioritizes documents with exact country match.
        """
        if not documents:
            return []

        # Three tiers of relevance
        exact_matches = []
        partial_matches = []
        no_match = []

        for doc in documents:
            countries_mentioned = doc.metadata.get('countries_mentioned', '').lower()

            if not countries_mentioned or countries_mentioned == 'none':
                no_match.append(doc)
            elif country in countries_mentioned:
                exact_matches.append(doc)
            elif any(keyword in countries_mentioned for keyword in [country.split()[0] if ' ' in country else country]):
                partial_matches.append(doc)
            else:
                no_match.append(doc)

        # Return in order of relevance
        return exact_matches + partial_matches + no_match

    def _filter_by_content_type(self, documents: List[Document], content_type: Optional[str] = None) -> List[Document]:
        """
        Filters documents by content type.
        """
        if not content_type or not documents:
            return documents

        filtered = [d for d in documents if d.metadata.get('content_type', '').lower() == content_type.lower()]
        return filtered if filtered else documents  # Return original if no matches

    def search(self, query: str, k: Optional[int] = None, filter_by_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Improved search with country and content type filtering.

        Args:
            query: User query
            k: Number of results (optional)
            filter_by_type: Filter by content type (optional)

        Returns:
            Dictionary with search results
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "RAG not initialized",
                "found": False,
                "documents": [],
                "count": 0
            }

        try:
            logger.info(f"🔍 Searching: '{query}'")

            # Extract country from query
            country = self._extract_country_from_query(query)
            k = k or self.k_results

            # Search more documents than needed (we'll filter)
            all_documents = self.db.similarity_search(query, k=self.search_k)

            if not all_documents:
                logger.info(f"⚠️  No documents found for: '{query}'")
                return {
                    "success": True,
                    "found": False,
                    "documents": [],
                    "count": 0,
                    "query": query,
                    "country_filter": country
                }

            # Apply filters in order of priority
            filtered_documents = all_documents

            # 1. Filter by country if mentioned
            if country:
                filtered_documents = self._filter_by_country(filtered_documents, country)
                logger.info(f"🌍 Applied country filter: {country}")

            # 2. Filter by content type if specified
            if filter_by_type:
                filtered_documents = self._filter_by_content_type(filtered_documents, filter_by_type)
                logger.info(f"📄 Applied content type filter: {filter_by_type}")

            # Take top k after filtering
            final_documents = filtered_documents[:k]

            logger.info(f"✅ Found {len(final_documents)} documents (searched {len(all_documents)})")

            # Format results
            formatted_docs = []
            for i, doc in enumerate(final_documents):
                formatted_docs.append({
                    "id": i + 1,
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get('filename', 'Unknown'),
                    "type": doc.metadata.get('content_type', 'general'),
                    "countries": doc.metadata.get('countries_mentioned', 'none')
                })

            return {
                "success": True,
                "found": True,
                "documents": formatted_docs,
                "count": len(final_documents),
                "query": query,
                "country_filter": country,
                "content_type_filter": filter_by_type,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "found": False,
                "documents": [],
                "count": 0
            }

    def get_context(self, query: str) -> str:
        """
        Gets formatted context for the LLM with improved filtering.
        """
        # Determine content type based on query
        content_type = None
        query_lower = query.lower()

        if any(x in query_lower for x in ["frequently asked", "faq", "question"]):
            content_type = "faq"
        elif any(x in query_lower for x in ["table", "economy class", "business class"]):
            content_type = "baggage_table"
        elif "flight status" in query_lower:
            content_type = "general"

        search_result = self.search(query, filter_by_type=content_type)

        if not search_result["success"] or not search_result["found"]:
            return "No specific information found in Air India policies."

        # Build context
        context_parts = ["✈️ **AIR INDIA INFORMATION (from official policies):**\n"]

        # Add filter info if applied
        if search_result.get("country_filter"):
            context_parts.append(f"🌍 **Filtered for: {search_result['country_filter'].title()}**\n")

        if search_result.get("content_type_filter"):
            context_parts.append(f"📄 **Content type: {search_result['content_type_filter']}**\n")

        for doc in search_result["documents"]:
            source = doc["source"]
            content = doc["content"]
            countries = doc.get("countries", "none")

            context_parts.append(f"📄 **Source: {source}**")
            if countries and countries != "none":
                context_parts.append(f"🌍 **Countries: {countries}**")
            context_parts.append(content)
            context_parts.append("---")

        # Add instructions for LLM - CORREGIDO: NO en español
        context_parts.append("\n💡 **INSTRUCTIONS FOR THE ASSISTANT:**")
        context_parts.append("1. Use this information to answer the question")
        context_parts.append("2. Be precise and concise")
        context_parts.append("3. If information is insufficient, state it clearly")
        context_parts.append("4. Respond in the SAME LANGUAGE as the user question")
        context_parts.append("5. If the query is in Hindi, respond in Hindi")

        return "\n".join(context_parts)

    def get_answer(self, query: str) -> str:
        """
        Gets answer using improved RAG + LLM with language detection.
        """
        if not self.is_initialized:
            return "✈️ The policy query system is currently unavailable."

        try:
            # Get context with filtering
            context = self.get_context(query)

            # Detect language
            lang = self._detect_language(query)

            # Set language instruction
            if lang == 'hi':
                language_instruction = "Respond in Hindi (हिन्दी में उत्तर दें)"
            else:
                language_instruction = "Respond in English"

            # Build LLM prompt - CORREGIDO: NO en español
            prompt = f"""You are 'Maharaja', the official Air India assistant.

AIR INDIA POLICY CONTEXT:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer BASED on the provided context
2. If information is not in the context, say: "I didn't find that specific information"
3. Be helpful and professional
4. {language_instruction}
5. Use relevant emojis ✈️ 🧳 🎫
6. Keep responses clear and concise

ANSWER:"""

            # Call Ollama
            import ollama

            response = ollama.chat(
                model='phi3:mini',
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "num_predict": 400}
            )

            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"❌ Error getting answer: {e}")
            return "✈️ There was an error consulting the policies. Please try again."

    def test_queries(self):
        """Runs system tests with country filtering."""
        test_cases = [
            ("baggage allowance for Canada", "country_specific"),
            ("check-in policy", "general"),
            ("flight cancellation", "general"),
            ("carry-on luggage", "general"),
            ("frequently asked questions about baggage", "faq"),
            ("economy class baggage", "class_specific"),
            ("what is the baggage allowance for Sri Lanka", "country_specific")
        ]

        logger.info("\n" + "=" * 60)
        logger.info("🧪 TESTING IMPROVED RAG SYSTEM")
        logger.info("=" * 60)

        for query, category in test_cases:
            logger.info(f"\n📝 Query: '{query}' ({category})")
            result = self.search(query, k=2)

            if result["success"]:
                status = "✅" if result["found"] else "⚠️ "
                logger.info(f"   {status} Found: {result['count']}")

                if result.get("country_filter"):
                    logger.info(f"   🌍 Country filter: {result['country_filter']}")

                if result["found"]:
                    for doc in result["documents"][:1]:  # Show only first
                        logger.info(f"   📄 Source: {doc['source']}")
                        logger.info(f"   📝 Type: {doc['type']}")
                        if doc.get("countries") and doc["countries"] != "none":
                            logger.info(f"   🌍 Countries: {doc['countries']}")
            else:
                logger.error(f"   ❌ Error: {result.get('error', 'Unknown')}")

    def _get_timestamp(self) -> str:
        """Utility for timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """Gets system statistics."""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        try:
            info = self.db.get()
            return {
                "status": "initialized",
                "document_count": len(info.get('ids', [])),
                "collection": self.collection_name,
                "embeddings_model": "nomic-embed-text",
                "chroma_path": str(self.chroma_db_path)
            }
        except:
            return {"status": "error_getting_stats"}


def create_rag_handler():
    """
    Factory function to create improved RAG handler.
    """
    logger.info("\n" + "=" * 60)
    logger.info("🚀 CREATING IMPROVED RAG HANDLER (WITH COUNTRY FILTERING)")
    logger.info("=" * 60)

    handler = SimpleRAGHandler()

    if handler.is_initialized:
        logger.info("✅ RAG Handler initialized correctly")
        logger.info(f"📊 Documents in DB: {handler.get_stats().get('document_count', 'N/A')}")

        # Run quick test
        handler.test_queries()

        return handler
    else:
        logger.error("❌ Failed to initialize RAG Handler")
        return None


if __name__ == "__main__":
    # Standalone mode for testing
    logger.info("🧪 TEST MODE - Improved RAG Handler")

    handler = create_rag_handler()

    if handler and handler.is_initialized:
        # Test specific queries
        test_queries = [
            "baggage allowance for Canada",
            "frequently asked questions about baggage",
            "economy class baggage limits"
        ]

        for query in test_queries:
            print(f"\n🎯 Testing: '{query}'")
            result = handler.search(query, k=3)

            if result["success"] and result["found"]:
                print(f"📊 Results: {len(result['documents'])}")
                for doc in result["documents"]:
                    print(f"  • {doc['source']} ({doc['type']}) - Countries: {doc.get('countries', 'none')}")
            else:
                print(f"❌ No results or error")