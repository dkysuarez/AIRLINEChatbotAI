# rag/intelligent_indexer.py - IMPROVED VERSION WITH INTELLIGENT CHUNKING
"""
Intelligent Indexer for Air India RAG - IMPROVED VERSION
- Intelligent chunking for FAQs (extracts specific Q/A)
- Better country detection in context (improved to handle phrases like 'United States and Canada')
- Improved metadata for more precise searches
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntelligentIndexer")

# Add to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    from langchain_ollama import OllamaEmbeddings
    from langchain_chroma import Chroma

    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.error(f"Missing LangChain dependencies: {e}")
    LANGCHAIN_AVAILABLE = False


class IntelligentIndexer:
    """
    IMPROVED Intelligent indexer - with intelligent chunking for FAQs
    """

    # Key documents - files we expect to process
    USEFUL_FILES = {
        "checked_baggage.txt": {
            "min_size": 10000,
            "expected_type": "baggage_table"
        },
        "faq_baggage.txt": {
            "min_size": 30000,
            "expected_type": "faq"
        },
        "baggage_guidelines.txt": {
            "min_size": 3000,
            "expected_type": "general"
        },
        "flight_status.txt": {
            "min_size": 1000,
            "expected_type": "general"
        }
    }

    # Keywords for country detection - IMPROVED with more variants
    COUNTRY_KEYWORDS = {
        "canada": ["canada", "canadian"],
        "usa": ["united states", "usa", "us", "america", "u.s.", "u.s.a."],
        "india": ["india", "indian", "domestic"],
        "sri lanka": ["sri lanka", "sri lankan"],
        "bangladesh": ["bangladesh", "bangladeshi"],
        "nepal": ["nepal", "nepalese"],
        "maldives": ["maldives", "maldivian"],
        "japan": ["japan", "japanese"],
        "australia": ["australia", "australian"],
        "europe": ["europe", "european"],
        "uk": ["uk", "united kingdom", "britain"],
        "myanmar": ["myanmar", "burma"],
        "israel": ["israel", "israeli"],
        "thailand": ["thailand", "thai"],
        "singapore": ["singapore", "singaporean"],
        "hongkong": ["hongkong", "hong kong"],
        "indonesia": ["indonesia", "indonesian"],
        "malaysia": ["malaysia", "malaysian"],
        "philippines": ["philippines", "filipino"],
        "vietnam": ["vietnam", "vietnamese"],
        "south korea": ["south korea", "korea", "korean"],
        "new zealand": ["new zealand", "zealand"]
    }

    # Priority multipliers for different content types
    CONTENT_PRIORITY_MULTIPLIER = {
        "baggage_table": 2.0,  # Maximum priority for tables
        "faq": 1.5,  # High priority for FAQs
        "general": 1.0,
        "flight_status": 1.3
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """Initializes the intelligent indexer."""
        self.project_root = Path(__file__).parent.parent
        self.data_dir = data_dir or (self.project_root / "data" / "raw")
        self.chroma_dir = self.project_root / "rag" / "chroma_db"

        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Chroma directory: {self.chroma_dir}")

        # Statistics
        self.stats = {
            "total_files_checked": 0,
            "useful_files_found": 0,
            "useless_files_skipped": 0,
            "total_chunks_created": 0,
            "chunks_by_type": {},
            "indexing_time": None
        }

    def filter_useful_files(self) -> List[Path]:
        """Filters only useful files."""
        useful_files = []

        logger.info("Filtering useful files...")

        for filename, criteria in self.USEFUL_FILES.items():
            file_path = self.data_dir / filename

            if not file_path.exists():
                logger.warning(f"File not found: {filename}")
                self.stats["useless_files_skipped"] += 1
                continue

            file_size = file_path.stat().st_size
            if file_size < criteria["min_size"]:
                logger.warning(f"File too small: {filename} ({file_size} < {criteria['min_size']})")
                self.stats["useless_files_skipped"] += 1
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # Basic content type validation
            if criteria["expected_type"] == "baggage_table" and "kg" not in content:
                logger.warning(f"Invalid content for {filename}")
                self.stats["useless_files_skipped"] += 1
                continue
            elif criteria["expected_type"] == "faq" and "?" not in content:
                logger.warning(f"Invalid content for {filename}")
                self.stats["useless_files_skipped"] += 1
                continue

            useful_files.append(file_path)
            logger.info(f"Useful file: {filename}")

        return useful_files

    def clean_chroma_directory(self) -> bool:
        """Cleans the ChromaDB directory."""
        try:
            if self.chroma_dir.exists():
                for file in self.chroma_dir.glob('*'):
                    file.unlink()
                logger.info("Chroma directory cleaned")
            else:
                self.chroma_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Chroma directory created")
            return True
        except Exception as e:
            logger.error(f"Error cleaning Chroma directory: {e}")
            return False

    def _detect_content_type(self, file_path: Path) -> str:
        """Detects content type based on file name and content."""
        filename = file_path.name

        if "table" in filename or "allowance" in filename:
            return "baggage_table"
        elif "faq" in filename:
            return "faq"
        else:
            return "general"

    def _extract_countries(self, text: str) -> str:
        """Improved country detection - more robust to handle phrases like 'United States and Canada'."""
        text_lower = text.lower()
        found_countries = set()

        # Standard keyword matching
        for country, keywords in self.COUNTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_countries.add(country)
                    break

        # Special case for common phrases in Air India docs
        if "united states and canada" in text_lower or ("united states" in text_lower and "canada" in text_lower):
            found_countries.add("usa")
            found_countries.add("canada")

        # Additional special cases if needed (e.g. for Sri Lanka or Japan)
        if "sri lanka" in text_lower or "sri lankan" in text_lower:
            found_countries.add("sri lanka")
        if "japan" in text_lower or "japanese" in text_lower:
            found_countries.add("japan")

        return ", ".join(sorted(found_countries)) if found_countries else "none"

    def _extract_faqs(self, text: str) -> List[str]:
        """Intelligent FAQ extraction - splits by Q/A pairs."""
        # Pattern for Q/A (assumes format like "Question? Answer")
        faq_pattern = r"(\b[A-Z][^?]*\?)\s*(.+?)(?=\b[A-Z][^?]*\?|$)"
        matches = re.findall(faq_pattern, text, re.DOTALL | re.IGNORECASE)

        faqs = []
        for question, answer in matches:
            faq_text = f"{question.strip()} {answer.strip()}"
            if len(faq_text) > 50:
                faqs.append(faq_text)

        return faqs if faqs else [text]  # Fallback to full text if no Q/A found

    def _extract_tables(self, text: str) -> List[str]:
        """Table-aware chunking - splits by table markers."""
        table_pattern = r"(\|.+?\|(?:\n\|.+?\|)+)"
        tables = re.findall(table_pattern, text, re.DOTALL)

        return tables if tables else [text]  # Fallback

    def create_documents(self, file_path: Path) -> List[Document]:
        """Creates documents with improved chunking and metadata."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        content_type = self._detect_content_type(file_path)
        priority = self.CONTENT_PRIORITY_MULTIPLIER.get(content_type, 1.0)

        # Intelligent chunking based on type
        if content_type == "faq":
            chunks = self._extract_faqs(text)
        elif content_type == "baggage_table":
            chunks = self._extract_tables(text)
        else:
            # General recursive splitting
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=150,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = splitter.split_text(text)

        documents = []
        total_chunks = len(chunks)

        for chunk_id, chunk in enumerate(chunks, 1):
            countries = self._extract_countries(chunk)
            has_baggage = "baggage" in chunk.lower() or "kg" in chunk.lower()
            question_count = chunk.count("?")
            is_question = chunk.strip().endswith("?")

            metadata = {
                "filename": file_path.name,
                "content_type": content_type,
                "chunk_id": chunk_id,
                "total_chunks": total_chunks,
                "char_count": len(chunk),
                "source": "air_india",
                "airline": "air_india",
                "has_baggage_info": has_baggage,
                "countries_mentioned": countries,
                "question_count": question_count,
                "is_question": is_question,
                "content_priority": priority,
                "processed_at": datetime.now().isoformat()
            }

            documents.append(Document(page_content=chunk, metadata=metadata))

            # Update stats
            self.stats["chunks_by_type"][content_type] = self.stats["chunks_by_type"].get(content_type, 0) + 1

        logger.info(f"Created {len(documents)} documents from {file_path.name}")

        return documents

    def create_vector_store(self, documents: List[Document]) -> Optional[Chroma]:
        """Creates vector store with improved embeddings."""
        try:
            embeddings = OllamaEmbeddings(model="nomic-embed-text")

            db = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=str(self.chroma_dir),
                collection_name="air_india_intelligent"
            )

            logger.info("Vector store created successfully")
            return db

        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return None

    def test_retrieval(self, db: Chroma):
        """Tests retrieval with sample queries."""
        test_queries = [
            "baggage allowance for usa",
            "baggage allowance for canada",
            "baggage allowance for sri lanka",
            "check-in policy",
            "economy class baggage"
        ]

        logger.info("\nTESTING RETRIEVAL:")

        for query in test_queries:
            try:
                results = db.similarity_search(query, k=3)
                if results:
                    logger.info(f"'{query}' -> Found {len(results)} results")
                    for doc in results:
                        logger.debug(f"  • {doc.metadata['filename']} ({doc.metadata['content_type']}) - Countries: {doc.metadata['countries_mentioned']}")
                else:
                    logger.warning(f"'{query}' -> No results")
            except Exception as e:
                logger.error(f"Error in test '{query}': {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generates report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "data_directory": str(self.data_dir),
            "chroma_directory": str(self.chroma_dir),
            "stats": self.stats.copy(),
            "useful_files_indexed": list(self.USEFUL_FILES.keys()),
            "chunking_strategy": {
                "baggage_table": "Table-aware chunking (1000 chars)",
                "faq": "Intelligent Q/A extraction",
                "general": "Adaptive recursive chunking"
            },
            "content_priorities": self.CONTENT_PRIORITY_MULTIPLIER,
            "metadata_fields": [
                "filename", "content_type", "chunk_id", "total_chunks",
                "char_count", "source", "airline", "has_baggage_info",
                "countries_mentioned", "question_count", "is_question",
                "content_priority", "processed_at"
            ]
        }

        return report

    def save_report(self, report: Dict[str, Any]):
        """Saves report."""
        report_path = self.project_root / "rag" / "intelligent_indexing_report.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved: {report_path}")

    def run(self):
        """Executes indexing."""
        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("INTELLIGENT INDEXER - AIR INDIA RAG (IMPROVED VERSION)")
        logger.info("=" * 70)

        # 1. Dependencies
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available")
            return

        # 2. Clean directory
        if not self.clean_chroma_directory():
            return

        # 3. Filter files
        useful_files = self.filter_useful_files()

        if not useful_files:
            logger.error("No useful files found")
            logger.info("First run: python -m rag.scraper.core")
            return

        self.stats["total_files_checked"] = len(self.USEFUL_FILES)
        self.stats["useful_files_found"] = len(useful_files)
        self.stats["useless_files_skipped"] = len(self.USEFUL_FILES) - len(useful_files)

        logger.info(f"Useful files found: {len(useful_files)}/{len(self.USEFUL_FILES)}")

        # 4. Process files
        all_documents = []

        for file_path in useful_files:
            documents = self.create_documents(file_path)
            all_documents.extend(documents)

        self.stats["total_chunks_created"] = len(all_documents)

        if not all_documents:
            logger.error("Could not create documents")
            return

        logger.info(f"Total chunks created: {len(all_documents)}")

        # 5. Create DB
        db = self.create_vector_store(all_documents)

        if not db:
            return

        # 6. Test
        self.test_retrieval(db)

        # 7. Report
        self.stats["indexing_time"] = str(datetime.now() - start_time)

        report = self.generate_report()
        self.save_report(report)

        # 8. Summary
        logger.info("\n" + "=" * 70)
        logger.info("INDEXING COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"Files indexed: {len(useful_files)}")
        logger.info(f"Total chunks: {len(all_documents)}")
        logger.info(f"Total time: {self.stats['indexing_time']}")
        logger.info(f"Distribution by type: {self.stats['chunks_by_type']}")
        logger.info(f"Chroma DB: {self.chroma_dir}")
        logger.info("=" * 70)


def main():
    """Main function."""
    indexer = IntelligentIndexer()
    indexer.run()


if __name__ == "__main__":
    main()