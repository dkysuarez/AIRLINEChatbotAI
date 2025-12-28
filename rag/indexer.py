# rag/intelligent_indexer.py - VERSIÓN MEJORADA CON CHUNKING INTELIGENTE
"""
Intelligent Indexer for Air India RAG - VERSIÓN MEJORADA
- Chunking inteligente para FAQs (extrae Q/A específicas)
- Mejor detección de países en contexto
- Metadata mejorada para búsquedas más precisas
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
    Intelligent indexer MEJORADO - con chunking inteligente para FAQs
    """

    # Key documents
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

    # Keywords for country detection - MEJORADO
    COUNTRY_KEYWORDS = {
        "canada": ["canada", "canadian"],
        "usa": ["united states", "usa", "us", "america"],
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
        "baggage_table": 2.0,  # Máxima prioridad para tablas
        "faq": 1.5,  # Alta prioridad para FAQs
        "general": 1.0,
        "flight_status": 1.3
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """Initializes the intelligent indexer."""
        self.project_root = Path(__file__).parent.parent
        self.data_dir = data_dir or (self.project_root / "rag" / "data" / "raw")
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
                logger.warning(f"Expected file not found: {filename}")
                continue

            # Verify size
            file_size = os.path.getsize(file_path)
            min_size = criteria["min_size"]

            if file_size < min_size:
                logger.warning(f"{filename} too small: {file_size} < {min_size} chars")
                continue

            useful_files.append(file_path)
            logger.info(f"{filename}: {file_size:,} chars (useful)")

        return useful_files

    def detect_content_type(self, content: str, filename: str) -> str:
        """Detects content type with improved table detection."""
        content_lower = content.lower()
        filename_lower = filename.lower()

        # 1. FAQ detection (HIGH PRIORITY)
        question_count = content.count("?")

        if "faq" in filename_lower:
            return "faq"

        if question_count >= 5 and ("frequently asked" in content_lower or "question" in content_lower):
            return "faq"

        if question_count >= 10:
            return "faq"

        # 2. Baggage table detection - MEJORADO
        table_indicators = [
            ("|", 10),  # Pipelines indican tablas
            ("cabin class", 8),
            ("economy", 5),
            ("business", 5),
            ("first class", 5),
            ("kg", 5) or ("lb", 5),
            ("weight", 3),
            ("allowance", 3),
            ("checked bag", 3),
            ("carry-on", 2)
        ]

        table_score = 0
        for keyword, weight in table_indicators:
            table_score += content_lower.count(keyword) * weight

        if table_score >= 15:
            return "baggage_table"

        # 3. Flight status detection
        if "flight status" in content_lower or "check flight" in content_lower:
            return "flight_status"

        # 4. Filename patterns
        if "checked_baggage" in filename_lower:
            return "baggage_table"
        elif "flight_status" in filename_lower:
            return "flight_status"
        elif "guidelines" in filename_lower:
            return "general"
        elif "faq" in filename_lower:
            return "faq"

        # 5. Default
        if len(content) > 10000:
            return "large_text"

        return "general"

    def extract_countries_from_content(self, content: str, filename: Optional[str] = None) -> str:
        """
        MEJORADO: Extraer países REALMENTE mencionados en contexto.

        Busca patrones como:
        - "for flights to Canada"
        - "traveling from India"
        - "in the USA"
        - "baggage allowance for Sri Lanka"
        """
        content_lower = content.lower()
        countries_found = set()

        # Estrategia 1: Países en contexto específico
        lines = content.split('\n')

        for line in lines:
            line_lower = line.lower()

            # Patrones de contexto específico
            context_patterns = [
                # "to Canada", "from USA", "in India"
                r'\bto\s+(canada|usa|united states|india|sri lanka|bangladesh|nepal|maldives|australia|japan)\b',
                r'\bfrom\s+(canada|usa|united states|india|sri lanka|bangladesh|nepal|maldives|australia|japan)\b',
                r'\bin\s+(canada|usa|united states|india|sri lanka|bangladesh|nepal|maldives|australia|japan)\b',
                r'\bfor\s+(canada|usa|united states|india|sri lanka|bangladesh|nepal|maldives|australia|japan)\b',

                # Combinado con keywords de baggage
                r'\b(canada|usa|united states|india|sri lanka)\s+(baggage|allowance|policy|flight|travel|destination)\b',
                r'\b(baggage|allowance|policy)\s+(for|to|from|in)\s+(canada|usa|united states|india|sri lanka)\b'
            ]

            for pattern in context_patterns:
                matches = re.findall(pattern, line_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        country = match[0]
                    else:
                        country = match
                    countries_found.add(country)

        # Estrategia 2: Países individuales mencionados
        for country, keywords in self.COUNTRY_KEYWORDS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, content_lower, re.IGNORECASE):
                    countries_found.add(country)
                    break

        # Estrategia 3: Países en FAQs sobre "country of arrival and departure"
        if "country of arrival" in content_lower or "country of departure" in content_lower:
            # Si menciona países en este contexto, asumimos que aplica a todos
            if "international" in content_lower:
                countries_found.update(["canada", "usa", "uk", "australia", "europe"])

        # Limpiar y retornar
        unique_countries = sorted(countries_found)

        # Excluir países demasiado genéricos
        filtered_countries = [
            c for c in unique_countries
            if c not in ["gulf", "middle east", "africa"]  # "europe" lo mantenemos
        ]

        return ", ".join(filtered_countries) if filtered_countries else "none"

    def chunk_baggage_table(self, content: str) -> List[str]:
        """Chunking for baggage tables - preserva estructura."""
        chunks = []

        # Limpiar headers scrapeados
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith("SOURCE URL:") or line.startswith("SCRAPE DATE:") or line.startswith("CONTENT LENGTH:"):
                continue
            if line:
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines)

        # Usar text splitter estándar para tablas
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", "|", " "]
        )

        return splitter.split_text(content)

    def chunk_faq(self, content: str) -> List[str]:
        """
        CHUNKING INTELIGENTE para FAQs - extrae Q/A específicas.

        Identifica preguntas reales y sus respuestas, ignorando contenido no relevante.
        """
        # Limpiar contenido irrelevante
        if "MORE POPULAR FLIGHTS" in content:
            content = content.split("MORE POPULAR FLIGHTS")[0]
            logger.info("FAQ: Removed 'MORE POPULAR FLIGHTS' section")

        lines = content.split('\n')

        # Patrones para identificar PREGUNTAS reales
        question_patterns = [
            r'^[A-Z][^?]{10,}\?$',  # Línea que empieza con mayúscula, termina con ?
            r'^What\s+is\s+the\s+',  # "What is the..."
            r'^Can\s+I\s+',  # "Can I..."
            r'^How\s+do\s+I\s+',  # "How do I..."
            r'^Is\s+there\s+',  # "Is there..."
            r'^Does\s+Air\s+India\s+',  # "Does Air India..."
            r'^What\s+are\s+the\s+',  # "What are the..."
            r'^Where\s+can\s+I\s+',  # "Where can I..."
            r'^When\s+should\s+I\s+',  # "When should I..."
            r'^Why\s+',  # "Why..."
            r'^Who\s+',  # "Who..."
            r'^Are\s+there\s+',  # "Are there..."
        ]

        chunks = []
        current_qa = []
        in_question = False
        question_line = ""

        for line in lines:
            line_stripped = line.strip()

            # Saltar líneas vacías o no relevantes
            if not line_stripped:
                if in_question and current_qa:
                    # Terminar chunk actual
                    chunk_text = '\n'.join(current_qa)
                    if len(chunk_text) > 50:
                        chunks.append(chunk_text)
                    current_qa = []
                    in_question = False
                continue

            # Verificar si es una PREGUNTA real
            is_question = any(re.match(pattern, line_stripped) for pattern in question_patterns)

            if is_question:
                # Guardar chunk anterior si existe
                if current_qa:
                    chunk_text = '\n'.join(current_qa)
                    if len(chunk_text) > 50:
                        chunks.append(chunk_text)

                # Empezar nueva Q/A
                current_qa = [line_stripped]
                question_line = line_stripped
                in_question = True

            elif in_question:
                # Continuar con respuesta
                current_qa.append(line_stripped)

                # Cortar si respuesta es muy larga
                if len('\n'.join(current_qa)) > 1000:
                    chunk_text = '\n'.join(current_qa)
                    if len(chunk_text) > 50:
                        chunks.append(chunk_text)
                    current_qa = [question_line]  # Restart with question
                    in_question = True

        # Último chunk
        if current_qa:
            chunk_text = '\n'.join(current_qa)
            if len(chunk_text) > 50:
                chunks.append(chunk_text)

        # Si no encontramos chunks con el método inteligente, usar método general
        if not chunks:
            logger.info("No intelligent chunks found, using general chunking")
            return self.chunk_general_text(content, chunk_size=800, overlap=100)

        return chunks

    def chunk_general_text(self, content: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
        """Standard chunking for general text."""
        # Limpiar headers scrapeados
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith("SOURCE URL:") or line.startswith("SCRAPE DATE:") or line.startswith("CONTENT LENGTH:"):
                continue
            if line:
                cleaned_lines.append(line)

        cleaned_content = '\n'.join(cleaned_lines)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        return splitter.split_text(cleaned_content)

    def create_documents(self, file_path: Path) -> List[Document]:
        """Creates documents with IMPROVED metadata."""
        filename = file_path.name

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Detectar tipo MEJORADO
            content_type = self.detect_content_type(content, filename)

            # Aplicar chunking según tipo
            if content_type == "baggage_table":
                text_chunks = self.chunk_baggage_table(content)
            elif content_type == "faq":
                text_chunks = self.chunk_faq(content)
            else:
                if len(content) > 20000:
                    text_chunks = self.chunk_general_text(content, chunk_size=1000, overlap=120)
                else:
                    text_chunks = self.chunk_general_text(content, chunk_size=1500, overlap=200)

            # Crear documentos con metadata MEJORADA
            documents = []
            for i, chunk in enumerate(text_chunks):
                # Extraer países con método MEJORADO
                countries_str = self.extract_countries_from_content(chunk, filename)

                # Metadata MEJORADA
                has_baggage_info = "baggage" in chunk.lower() or "luggage" in chunk.lower()
                question_count = chunk.count("?")
                is_question = question_count > 0

                # Calcular prioridad
                base_priority = self.CONTENT_PRIORITY_MULTIPLIER.get(content_type, 1.0)
                priority_boost = 0

                if content_type == "faq" and is_question:
                    priority_boost += 0.5
                if has_baggage_info:
                    priority_boost += 0.3
                if countries_str != "none":
                    priority_boost += 0.2

                content_priority = base_priority + priority_boost

                metadata = {
                    "filename": filename,
                    "content_type": content_type,
                    "chunk_id": i + 1,
                    "total_chunks": len(text_chunks),
                    "char_count": len(chunk),
                    "source": "air_india_scraped_real",
                    "airline": "Air India",
                    "has_baggage_info": has_baggage_info,
                    "countries_mentioned": countries_str,
                    "question_count": question_count,
                    "is_question": is_question,
                    "content_priority": round(content_priority, 2),
                    "processed_at": datetime.now().isoformat()
                }

                documents.append(Document(page_content=chunk, metadata=metadata))

            # Estadísticas
            self.stats["chunks_by_type"][content_type] = self.stats["chunks_by_type"].get(content_type, 0) + len(
                documents)

            logger.info(f"{filename}: {len(documents)} chunks ({content_type})")

            # Mostrar países detectados
            all_countries = set()
            for doc in documents:
                countries = doc.metadata.get("countries_mentioned", "")
                if countries and countries != "none":
                    for country in countries.split(", "):
                        all_countries.add(country)

            if all_countries:
                countries_list = sorted(all_countries)
                preview = ", ".join(countries_list[:5])
                if len(countries_list) > 5:
                    preview += f"... (+{len(countries_list) - 5} more)"
                logger.info(f"   Countries detected: {preview}")

            return documents

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def clean_chroma_directory(self) -> bool:
        """Cleans Chroma directory."""
        try:
            if self.chroma_dir.exists():
                import shutil
                shutil.rmtree(self.chroma_dir)

            self.chroma_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Chroma directory cleaned")
            return True
        except Exception as e:
            logger.error(f"Error cleaning directory: {e}")
            return False

    def create_vector_store(self, all_documents: List[Document]) -> Optional[Chroma]:
        """Creates Chroma vector database."""
        if not all_documents:
            logger.error("No documents to index")
            return None

        try:
            logger.info("Configuring embeddings...")
            embeddings = OllamaEmbeddings(model="nomic-embed-text")

            logger.info("Creating vector database...")
            db = Chroma.from_documents(
                documents=all_documents,
                embedding=embeddings,
                persist_directory=str(self.chroma_dir),
                collection_name="air_india_intelligent"
            )

            # Verify
            info = db.get()
            vector_count = len(info.get('ids', []))

            if vector_count == len(all_documents):
                logger.info(f"Database created: {vector_count} vectors")
                return db
            else:
                logger.error(f"Error: Expected {len(all_documents)} vectors, created {vector_count}")
                return None

        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_retrieval(self, db: Chroma):
        """Tests retrieval with improved queries."""
        test_queries = [
            "Can I send my baggage as cargo?",
            "bicycle as checked baggage policy",
            "baggage allowance for international flights",
            "how to check flight status",
            "economy class baggage limits"
        ]

        logger.info("\nTesting retrieval...")
        logger.info("-" * 50)

        for query in test_queries:
            try:
                results = db.similarity_search(query, k=2)
                if results:
                    first_result = results[0]
                    filename = first_result.metadata.get('filename', 'N/A')
                    content_type = first_result.metadata.get('content_type', 'N/A')
                    countries = first_result.metadata.get('countries_mentioned', 'N/A')
                    priority = first_result.metadata.get('content_priority', 'N/A')

                    logger.info(f"'{query}' -> {filename} ({content_type})")
                    logger.info(f"   Priority: {priority}, Countries: {countries}")
                    logger.info(f"   {first_result.page_content[:150]}...")
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