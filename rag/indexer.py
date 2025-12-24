from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import shutil

print("🚀 INDEXADOR SIMPLE - Paso a paso\n")

# 1. ELIMINAR chroma_db si existe
if os.path.exists("chroma_db"):
    print("🗑️  Eliminando chroma_db anterior...")
    shutil.rmtree("chroma_db")
    print("✅ chroma_db eliminado\n")

# 2. LEER archivos
print("📂 Leyendo archivos de data/raw/...")
data_dir = "../rag/data/raw"
all_texts = []

for filename in os.listdir(data_dir):
    if filename.endswith(".txt"):
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():  # Solo si tiene contenido
                all_texts.append(content)
                print(f"   ✅ {filename} ({len(content):,} chars)")

if not all_texts:
    print("❌ ERROR: No hay archivos .txt en data/raw/")
    exit(1)

print(f"\n📊 TOTAL: {len(all_texts)} archivos cargados")

# 3. DIVIDIR en chunks
print("\n✂️  Dividiendo en chunks...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " ", ""]
)

combined_text = "\n\n".join(all_texts)
chunks = splitter.split_text(combined_text)
print(f"📦 Chunks creados: {len(chunks)}")

# Mostrar un chunk de ejemplo
if chunks:
    print(f"\n🔍 EJEMPLO Chunk 1 (primeros 200 chars):")
    print("-" * 50)
    print(chunks[0][:200] + "...")
    print("-" * 50)

# 4. CREAR embeddings
print("\n🧠 Creando embeddings con Ollama...")
try:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Probar que funcione
    test_embed = embeddings.embed_query("baggage test")
    print(f"✅ Ollama funcionando ({len(test_embed)} dimensiones)")
except Exception as e:
    print(f"❌ ERROR con Ollama: {e}")
    print("💡 Ejecuta: ollama serve")
    exit(1)

# 5. GUARDAR en Chroma (MÉTODO DIRECTO)
print("\n💾 Guardando en Chroma...")
try:
    # Usar persist_directory para guardar automáticamente
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory="chroma_db"
    )

    print("✅ Vectorstore creado con éxito")

    # Verificar
    if os.path.exists("chroma_db"):
        files = os.listdir("chroma_db")
        print(f"📁 Archivos en chroma_db/: {len(files)}")

        # Contar documentos
        doc_count = vectorstore._collection.count()
        print(f"📊 Documentos almacenados: {doc_count}")

        if doc_count == len(chunks):
            print("🎉 ¡PERFECTO! Todos los chunks guardados")
        else:
            print(f"⚠️  Solo {doc_count} de {len(chunks)} chunks guardados")

except Exception as e:
    print(f"❌ ERROR guardando en Chroma: {e}")

print("\n" + "=" * 60)
print("🏁 INDEXADOR COMPLETADO")
print("=" * 60)
print("\n📋 PARA PROBAR:")
print("   python test_rag_simple.py")