import os
from langchain_ollama import OllamaEmbeddings

# 1. Verificar chunks reales
print("🔍 VERIFICANDO CHUNKS REALES...")
data_dir = "data/raw"
all_text = ""

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(".txt"):
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            content = f.read()
            all_text += content + "\n\n"
            print(f"📄 {filename}: {len(content)} chars")

# 2. Crear chunks manualmente
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
chunks = splitter.split_text(all_text)

print(f"\n📦 CHUNKS CREADOS: {len(chunks)}")

# 3. Verificar primer chunk COMPLETO
print("\n📄 PRIMER CHUNK COMPLETO (50 primeros chars de cada línea):")
first_chunk = chunks[0] if chunks else ""
for i, line in enumerate(first_chunk.split('\n')[:10]):
    print(f"   Línea {i}: {line[:50]}...")

# 4. Probar embeddings directamente
print("\n🧠 PROBANDO EMBEDDINGS...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    test_embed = embeddings.embed_query("baggage allowance 23 kg")
    print(f"   ✅ Embeddings funcionando: {len(test_embed)} dimensiones")

    # Probar con un chunk real
    if chunks:
        chunk_embed = embeddings.embed_query(chunks[0][:100])
        print(f"   ✅ Chunk embedding funciona: {len(chunk_embed)} dimensiones")
except Exception as e:
    print(f"   ❌ Error embeddings: {e}")

# 5. Verificar si hay contenido real
print("\n🎯 CONTENIDO REAL EN CHUNKS:")
keywords = ["23 kg", "Economy", "check-in", "United States", "baggage"]
for keyword in keywords:
    count = sum(1 for chunk in chunks if keyword in chunk)
    print(f"   '{keyword}': en {count} chunks")

# 6. Mostrar chunks problemáticos
print("\n⚠️  CHUNKS PEQUEÑOS O VACÍOS:")
for i, chunk in enumerate(chunks[:20]):
    if len(chunk.strip()) < 50:
        print(f"   Chunk {i}: SOLO {len(chunk)} chars -> '{chunk[:50]}'")