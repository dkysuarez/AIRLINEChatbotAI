from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

print("🧠 Probando el RAG - Búsqueda de contexto relevante\n")
print("=" * 80)

queries = [
    "equipaje Estados Unidos",
    "baggage allowance domestic flex",
    "check-in online",
    "additional allowance Maharaja Club"
]

for query in queries:
    print(f"\n🔍 PREGUNTA: {query.upper()}")
    print("-" * 60)
    results = db.similarity_search(query, k=3)
    if results:
        for i, doc in enumerate(results):
            print(f"RESULTADO {i+1}:")
            print(doc.page_content[:600])  # Más caracteres para ver la tabla
            print("\n" + "-" * 40)
    else:
        print("   No se encontraron resultados")
    print("\n" + "=" * 80)

print("\n🎉 ¡Prueba completada! Si ves tablas con kg/lb y países, el RAG funciona perfecto.")