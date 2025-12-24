from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import re

embeddings = OllamaEmbeddings(model="nomic-embed-text")

def clean_text(text):
    """Limpia el texto de ruido común en Air India"""
    # Quitar menús repetidos, copyright, app promotion, etc.
    patterns_to_remove = [
        r"MORE POPULAR FLIGHTS.*",
        r"ABOUT US.*",
        r"AIR INDIA APP.*",
        r"Copyright © 2025 Air India Ltd.*",
        r"FOLLOW US ON.*",
        r"Sitemap.*",
        r"Terms & Conditions.*",
        r"Privacy Notice.*",
        r"Cookie Policy.*",
        r"Download the app.*",
        r"Hi, I’m AI.g.*",
        r"Set your cookies.*",
        r"We use cookies!.*"
    ]
    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text, flags=re.DOTALL)

    # Quitar líneas vacías múltiples
    text = re.sub(r'\n\s*\n', '\n\n', text)

    # Quitar URLs repetidas o links
    text = re.sub(r'https?://\S+', '', text)

    return text.strip()

def create_vectorstore():
    print("🚀 Creando vectorstore MEJORADO con datos limpios...")

    documents = []
    data_dir = "data/raw"
    for filename in os.listdir(data_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()

            # Limpiar
            cleaned = clean_text(raw_content)

            # Añadir metadata para mejor búsqueda
            documents.append({
                "content": cleaned,
                "source": filename
            })
            print(f"   ✅ Cargado y limpiado {filename} ({len(cleaned)} caracteres)")

    # Extraer solo el content para chunking
    texts = [doc["content"] for doc in documents]

    # Splitter más agresivo para chunks relevantes
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,      # Más pequeño para mejor precisión
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text("\n\n".join(texts))
    print(f"   📦 {len(chunks)} chunks creados (mejor precisión)")

    # Crear vectorstore nuevo (borra el viejo si existe)
    if os.path.exists("chroma_db"):
        import shutil
        shutil.rmtree("chroma_db")
        print("   🗑️ Vectorstore viejo borrado")

    Chroma.from_texts(chunks, embeddings, persist_directory="chroma_db")
    print("🎉 Vectorstore MEJORADO creado en 'chroma_db/' - ¡Ahora sí encuentra todo!")

if __name__ == "__main__":
    create_vectorstore()