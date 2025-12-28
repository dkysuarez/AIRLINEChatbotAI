"""
Simplified RAG Handler for Air India Chatbot.
With robust error handling and graceful fallbacks.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import re
import time  # For retry delay

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RAGHandler")

# Add to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from langchain_chroma import Chroma
    from langchain_ollama import OllamaEmbeddings

    LANGCHAIN_AVAILABLE = True
    logger.info("LangChain dependencies loaded successfully")
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    LANGCHAIN_AVAILABLE = False


class SimpleRAGHandler:
    """
    Improved RAG Handler with country-based filtering, multi-language support,
    and robust error handling.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.chroma_db_path = self.project_root / "rag" / "chroma_db"
        self.collection_name = "air_india_intelligent"

        self.embeddings = None
        self.db = None
        self.is_initialized = False

        self.k_results = 5
        self.search_k = 10

        self.country_patterns = {
            "canada": [r"\bcanada\b", r"\bcanadian\b"],
            "usa": [r"\busa\b", r"\bus\b", r"\bunited states\b", r"\bamerica\b", r"\bu\.s\.\b", r"\bu\.s\.a\.\b", r"\bunitedstates\b"],
            "india": [r"\bindia\b", r"\bindian\b", r"\bdomestic\b"],
            "sri lanka": [r"\bsri lanka\b", r"\bsri lankan\b"],
            "bangladesh": [r"\bbangladesh\b"],
            "nepal": [r"\bnepal\b"],
            "maldives": [r"\bmaldives\b"],
            "australia": [r"\baustralia\b"],
            "europe": [r"\beurope\b", r"\beuropean\b", r"\buk\b", r"\bfrance\b", r"\bgermany\b"],
            "japan": [r"\bjapan\b"],
            "south korea": [r"\bsouth korea\b", r"\bkorea\b"],
            "mexico": [r"\bmexico\b", r"\bmexican\b"],
            "delhi": [r"\bdelhi\b"],
            "mumbai": [r"\bmumbai\b"]
        }

        logger.info("Initializing RAG Handler")
        logger.info(f"Database path: {self.chroma_db_path}")

        self._initialize_chroma()

    def _initialize_chroma(self) -> bool:
        """Initialize ChromaDB with graceful fallback if failed."""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available - RAG disabled")
            return False

        try:
            logger.info("Configuring embeddings...")
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

            if not self.chroma_db_path.exists():
                logger.warning(f"Chroma database not found at {self.chroma_db_path}")
                logger.info("Run 'python -m rag.indexer' to create it")
                self.is_initialized = False
                return False

            logger.info("Loading Chroma database...")
            self.db = Chroma(
                persist_directory=str(self.chroma_db_path),
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )

            info = self.db.get()
            count = len(info.get('ids', []))

            if count > 0:
                logger.info(f"RAG database loaded successfully ({count} documents)")
                self.is_initialized = True
                return True
            else:
                logger.warning("RAG database is empty")
                self.is_initialized = False
                return False

        except Exception as e:
            logger.error(f"Failed to initialize RAG database: {e}")
            self.is_initialized = False
            return False

    def _detect_language(self, text: str) -> str:
        if not text:
            return 'en'
        text_lower = text.lower()
        hindi_chars = any('\u0900' <= char <= '\u097F' for char in text)
        hindi_words = any(word in text_lower for word in ['kya', 'hai', 'kaise', 'ho', 'mein', 'aap', 'nahi'])
        return 'hi' if hindi_chars or hindi_words else 'en'

    def _extract_country_from_query(self, query: str) -> Optional[str]:
        query_lower = query.lower()
        for country, patterns in self.country_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return country
        return None

    def search(self, query: str, k: int = None) -> Dict[str, Any]:
        """Search with permissive country filter and error handling."""
        if not self.is_initialized:
            return {"success": False, "error": "RAG not initialized", "fallback": True}

        try:
            country = self._extract_country_from_query(query)
            search_k = k or self.search_k
            results = self.db.similarity_search(query, k=search_k)

            # Permissive filter
            filtered_results = results
            if country:
                permissive = []
                for doc in results:
                    meta = doc.metadata.get('countries_mentioned', 'none').lower()
                    content = doc.page_content.lower()
                    if country in meta or country in content:
                        permissive.append(doc)
                filtered_results = permissive if permissive else results

            final_results = filtered_results[:k or self.k_results]

            documents = []
            for doc in final_results:
                documents.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get('filename', 'unknown'),
                    "type": doc.metadata.get('content_type', 'unknown'),
                    "countries": doc.metadata.get('countries_mentioned', 'none')
                })

            return {
                "success": True,
                "found": len(documents) > 0,
                "count": len(documents),
                "documents": documents
            }

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return {"success": False, "error": str(e), "fallback": True}

    def get_context(self, query: str) -> str:
        result = self.search(query, k=8)
        if not result["success"] or not result["found"]:
            return "No specific policy information available at the moment."

        parts = ["IMPORTANT AIR INDIA BAGGAGE RULES:\n"]
        seen = set()
        for doc in result["documents"]:
            content = doc['content'].strip()
            if content in seen:
                continue
            seen.add(content)
            parts.append(f"• From {doc['source']} (applies to: {doc['countries']})")
            parts.append(content)
            parts.append("")
        return "\n".join(parts)

    def get_answer(self, query: str) -> str:
        """Get answer with retry logic and graceful fallbacks."""
        try:
            if not self.is_initialized:
                return ("I'm having trouble accessing detailed policies right now. "
                        "Common international allowance in Economy: 1 checked bag up to 23 kg + 1 carry-on up to 8 kg. "
                        "Rules may vary by route.")

            context = self.get_context(query)
            if "No specific" in context:
                return ("I couldn't find exact details for your query. "
                        "Typical international Economy allowance: 1 checked bag up to 23 kg and 1 carry-on up to 8 kg.")

            lang = self._detect_language(query)
            lang_inst = "Respond in Hindi (हिन्दी में उत्तर दें)" if lang == 'hi' else "Respond in English"

            prompt = f"""You are Maharaja, the precise and helpful Air India assistant.

RELEVANT POLICY INFORMATION:
{context}

USER QUESTION: {query}

Answer directly using the information above:
- Give exact numbers (pieces, kg)
- Mention class differences if available
- Be concise and professional
- {lang_inst}

ANSWER:"""

            import ollama

            # Retry up to 3 times
            for attempt in range(3):
                try:
                    response = ollama.chat(
                        model='phi3:mini',
                        messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0.3, "num_predict": 400}
                    )
                    return response['message']['content'].strip()
                except Exception as e:
                    logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(1)  # Wait before retry
                    else:
                        break

            # Final fallback if all retries fail
            return ("I'm currently experiencing connection issues with the policy system. "
                    "Please try again in a few moments or contact Air India support at 1-800-180-1407.")

        except Exception as e:
            logger.error(f"Critical error in get_answer: {e}")
            return "Sorry, I'm having technical difficulties. Please try your question again shortly."

    def get_stats(self) -> Dict[str, Any]:
        if not self.is_initialized:
            return {"status": "not_initialized"}
        try:
            info = self.db.get()
            return {
                "status": "initialized",
                "document_count": len(info.get('ids', [])),
                "collection": self.collection_name
            }
        except:
            return {"status": "error"}


def create_rag_handler():
    handler = SimpleRAGHandler()
    if handler.is_initialized:
        logger.info("RAG Handler ready")
    else:
        logger.warning("RAG Handler running in fallback mode")
    return handler