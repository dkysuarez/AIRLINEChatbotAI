from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os

print("🧪 TEST RAG FINAL - Verificación Completa\n")
print("=" * 80)

# 1. Verificar que existe el vectorstore
print("1️⃣ VERIFICANDO VECTORSTORE...")
if not os.path.exists("chroma_db"):
    print("   ❌ ERROR: No existe 'chroma_db/'")
    print("   💡 Ejecuta el indexer primero")
    exit(1)

files = os.listdir("chroma_db")
print(f"   ✅ Existe 'chroma_db/' con {len(files)} archivos")
for f in files:
    size = os.path.getsize(os.path.join("chroma_db", f))
    print(f"      • {f} ({size:,} bytes)")

# 2. Cargar embeddings
print("\n2️⃣ CARGANDO EMBEDDINGS...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    print("   ✅ Embeddings cargados (nomic-embed-text)")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 3. Cargar vectorstore
print("\n3️⃣ CARGANDO VECTORSTORE...")
try:
    # Intentar diferentes nombres de colección
    collection_names = [None, "airline_docs", "langchain"]

    db = None
    for name in collection_names:
        try:
            print(f"   🔍 Intentando colección: {name if name else 'default'}")
            if name:
                db = Chroma(
                    persist_directory="chroma_db",
                    embedding_function=embeddings,
                    collection_name=name
                )
            else:
                db = Chroma(
                    persist_directory="chroma_db",
                    embedding_function=embeddings
                )

            # Probar una búsqueda rápida
            test_results = db.similarity_search("test", k=1)
            if test_results:
                print(f"   ✅ Colección cargada y funciona")
                break
            else:
                print(f"   ⚠️  Colección vacía")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    if not db:
        print("   ❌ No se pudo cargar ninguna colección")
        exit(1)

except Exception as e:
    print(f"   ❌ Error general: {e}")
    exit(1)

# 4. Verificar documentos
print("\n4️⃣ VERIFICANDO DOCUMENTOS...")
try:
    count = db._collection.count()
    print(f"   📊 Documentos en la base: {count}")

    if count == 0:
        print("   ❌ ERROR: La base está vacía")
        exit(1)
    elif count == 110:
        print("   ✅ Perfecto! Todos los 110 chunks están presentes")
    else:
        print(f"   ⚠️  Parcial: {count} de 110 chunks")

except Exception as e:
    print(f"   ⚠️  No se pudo verificar conteo: {e}")

# 5. TEST DE BÚSQUEDAS REALES
print("\n5️⃣ TEST DE BÚSQUEDAS REALES")
print("-" * 80)

# Consultas específicas del dominio de Air India
test_cases = [
    {
        "query": "What is the baggage allowance for Economy class?",
        "description": "Equipaje Economy",
        "expected_keywords": ["kg", "Economy", "allowance", "baggage"]
    },
    {
        "query": "How to do web check-in?",
        "description": "Check-in web",
        "expected_keywords": ["web", "check-in", "online", "process"]
    },
    {
        "query": "23 kg baggage limit",
        "description": "Límite 23kg",
        "expected_keywords": ["23", "kg", "limit", "baggage"]
    },
    {
        "query": "United States baggage policy",
        "description": "Política USA",
        "expected_keywords": ["United", "States", "USA", "baggage"]
    },
    {
        "query": "flight status information",
        "description": "Estado vuelo",
        "expected_keywords": ["flight", "status", "information"]
    },
    {
        "query": "Economy Value 15 kg",
        "description": "Economy Value 15kg",
        "expected_keywords": ["Economy", "Value", "15", "kg"]
    }
]

print("\n🔍 PROBANDO BÚSQUEDAS SIMPLES (similarity_search):")
print("-" * 60)

passed_tests = 0
total_tests = len(test_cases)

for i, test in enumerate(test_cases, 1):
    query = test["query"]
    desc = test["description"]

    print(f"\n🔎 Test {i}: {desc}")
    print(f"   Query: '{query}'")

    try:
        # Búsqueda simple
        results = db.similarity_search(query, k=2)

        if results:
            print(f"   ✅ ENCONTRADOS: {len(results)} resultados")

            # Verificar contenido relevante
            found_keywords = []
            for j, doc in enumerate(results[:2]):  # Solo primeros 2
                content = doc.page_content.lower()

                # Buscar keywords esperadas
                for keyword in test["expected_keywords"]:
                    if keyword.lower() in content:
                        found_keywords.append(keyword)

                # Mostrar preview
                preview = content[:150].replace('\n', ' ')
                print(f"   {j + 1}. {preview}...")

            # Verificar keywords encontradas
            if found_keywords:
                unique_keywords = list(set(found_keywords))
                print(f"   🎯 Keywords encontradas: {', '.join(unique_keywords[:3])}")
                passed_tests += 1
            else:
                print(f"   ⚠️  No se encontraron keywords esperadas")

        else:
            print(f"   ❌ SIN RESULTADOS")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

# 6. TEST CON SCORES
print("\n🔍 PROBANDO BÚSQUEDAS CON SCORE (similarity_search_with_score):")
print("-" * 60)

sample_queries = [
    "baggage allowance",
    "web check-in process",
    "23 kg limit"
]

for query in sample_queries:
    print(f"\n📝 Query: '{query}'")

    try:
        results = db.similarity_search_with_score(query, k=3)

        if results:
            print(f"   📊 Resultados con scores:")
            for i, (doc, score) in enumerate(results):
                # Scores más bajos son mejores (distancia menor)
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"   {i + 1}. Score: {score:.4f}")
                print(f"      {content_preview}...")
        else:
            print(f"   ⚠️  Sin resultados")

    except Exception as e:
        print(f"   ❌ Error: {e}")

# 7. RESULTADO FINAL
print("\n" + "=" * 80)
print("📊 RESUMEN FINAL")
print("=" * 80)

success_rate = (passed_tests / total_tests) * 100

print(f"✅ Tests pasados: {passed_tests}/{total_tests} ({success_rate:.0f}%)")

if passed_tests == total_tests:
    print("\n🎉 🎉 🎉 ¡SISTEMA RAG FUNCIONANDO PERFECTAMENTE!")
    print("   El vectorstore está listo para usar en tu chatbot.")

elif passed_tests >= total_tests * 0.7:
    print("\n✅ ✅ Sistema RAG funciona (mayoría de tests pasados)")
    print("   Puedes proceder a integrarlo con tu chatbot.")

elif passed_tests > 0:
    print(f"\n⚠️  ⚠️  Sistema parcialmente funcional")
    print(f"   {passed_tests} de {total_tests} tests pasados")
    print("   Revisa los chunks y embeddings.")

else:
    print("\n❌ ❌ ❌ PROBLEMAS GRAVES")
    print("   El vectorstore se creó pero las búsquedas no funcionan.")
    print("   Posibles problemas:")
    print("   1. Embeddings no se guardaron correctamente")
    print("   2. Problema con la colección de Chroma")
    print("   3. Ollama no genera embeddings consistentes")

print("\n📋 SIGUIENTES PASOS:")
print("   1. Integrar en app.py: from langchain_chroma import Chroma")
print("   2. Crear retriever: retriever = db.as_retriever(search_kwargs={'k': 3})")
print("   3. Usar con tu chatbot")

print("\n" + "=" * 80)
print("🏁 TEST COMPLETADO")