# test_rag_direct.py
# !/usr/bin/env python3
"""
Test directo del sistema RAG - Verifica si encuentra información REAL
"""

import sys
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Añadir proyecto al path
sys.path.append(str(Path(__file__).parent))


def test_rag_system():
    """Test directo del RAG handler."""
    print("=" * 70)
    print("🧪 RAG SYSTEM - DIRECT TEST")
    print("=" * 70)

    try:
        from rag.rag_handler import create_rag_handler

        # 1. Inicializar RAG
        print("\n1. 🔧 Initializing RAG Handler...")
        rag = create_rag_handler()

        if not rag or not rag.is_initialized:
            print("❌ RAG failed to initialize")
            return False

        print(f"✅ RAG initialized: {rag.get_stats().get('document_count', 0)} documents")

        # 2. Test de búsqueda directa (sin LLM)
        print("\n2. 🔍 Testing document search...")

        test_queries = [
            ("baggage allowance", "Should find baggage info"),
            ("checked baggage", "Should find checked baggage details"),
            ("carry on luggage", "Should find cabin baggage info"),
            ("flight status", "Should find flight status info"),
            ("economy class baggage", "Should find class-specific info"),
        ]

        search_results = []
        for query, expected in test_queries:
            print(f"\n   Query: '{query}'")
            result = rag.search(query, k=2)

            if result["success"] and result["found"]:
                docs = result["documents"]
                print(f"   ✅ Found: {len(docs)} documents")
                for doc in docs:
                    print(f"      • Source: {doc['source']}")
                    print(f"        Type: {doc['type']}")
                    if doc.get('countries') and doc['countries'] != 'none':
                        print(f"        Countries: {doc['countries']}")
                search_results.append(True)
            else:
                print(f"   ❌ Not found or error: {result.get('error', 'No results')}")
                search_results.append(False)

        # 3. Test con LLM (respuestas completas)
        print("\n3. 🤖 Testing LLM answers (this may take a minute)...")

        llm_test_queries = [
            ("What is the baggage allowance for international flights?",
             "Should give specific kg numbers"),
            ("Can I carry a bicycle as checked baggage?",
             "Should mention bicycle policy"),
            ("How to check flight status?",
             "Should explain flight status check"),
            ("What is the cabin baggage limit?",
             "Should mention 7kg or 8kg"),
        ]

        llm_results = []
        for query, expected in llm_test_queries[:2]:  # Solo 2 para no saturar
            print(f"\n   Query: '{query}'")
            print(f"   Expected: {expected}")

            answer = rag.get_answer(query)

            # Analizar respuesta
            if len(answer) < 50:
                print(f"   ❌ Answer too short ({len(answer)} chars)")
                print(f"      Answer: {answer[:100]}...")
                llm_results.append(False)
            elif "didn't find" in answer.lower() or "not in the context" in answer.lower():
                print(f"   ⚠️  Answer: 'Information not found'")
                print(f"      Full: {answer[:150]}...")
                llm_results.append(False)
            else:
                print(f"   ✅ Answer length: {len(answer)} chars")
                print(f"      Preview: {answer[:150]}...")
                llm_results.append(True)

        # 4. Resumen
        print("\n" + "=" * 70)
        print("📊 RAG TEST RESULTS SUMMARY")
        print("=" * 70)

        search_success = sum(search_results)
        llm_success = sum(llm_results)

        print(f"🔍 Document Search: {search_success}/{len(search_results)}")
        print(f"🤖 LLM Answers: {llm_success}/{len(llm_results)}")

        if search_success >= 3 and llm_success >= 1:
            print("\n🎉 RAG SYSTEM IS WORKING REASONABLY WELL!")
            return True
        else:
            print("\n⚠️  RAG SYSTEM NEEDS IMPROVEMENT")
            if search_success < 3:
                print("   • Document search is not finding enough information")
            if llm_success < 1:
                print("   • LLM is not generating good answers from context")
            return False

    except Exception as e:
        print(f"\n❌ ERROR in RAG test: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_rag_data():
    """Verifica los datos que tiene el RAG."""
    print("\n" + "=" * 70)
    print("📁 CHECKING RAG DATA SOURCES")
    print("=" * 70)

    data_dir = Path("rag/data/raw")
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return

    files = list(data_dir.glob("*.txt"))
    print(f"Found {len(files)} text files:")

    for file in files:
        size = file.stat().st_size
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = []
            for _ in range(3):
                line = f.readline().strip()
                if line:
                    first_lines.append(line[:100])

        print(f"\n📄 {file.name} ({size:,} bytes)")
        for i, line in enumerate(first_lines, 1):
            print(f"   {i}. {line}")


def main():
    """Ejecuta todas las verificaciones RAG."""
    print("🚀 AIR INDIA RAG SYSTEM - COMPREHENSIVE TEST")

    # 1. Verificar datos
    check_rag_data()

    # 2. Testear sistema RAG
    rag_ok = test_rag_system()

    # 3. Recomendaciones
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS FOR IMPROVEMENT")
    print("=" * 70)

    if rag_ok:
        print("""
        ✅ RAG is working. Suggestions:
        1. Add more specific test queries for edge cases
        2. Consider improving prompts for better answers
        3. Add more documents if certain topics are missing
        """)
    else:
        print("""
        ❌ RAG needs improvement. Suggestions:

        A. IF DOCUMENTS NOT FOUND:
        1. Check if rag/indexer.py was run: python -m rag.indexer
        2. Verify scraped data in rag/data/raw/ has baggage info
        3. Check file sizes: should be >10KB each

        B. IF ANSWERS ARE GENERIC:
        1. Improve prompts in rag_handler.py
        2. Add more specific context in get_context()
        3. Ensure Ollama model is good (phi3:mini works)

        C. QUICK FIXES:
        1. Add fallback information for common queries
        2. Improve country detection patterns
        3. Add more keywords to search
        """)

    return rag_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)