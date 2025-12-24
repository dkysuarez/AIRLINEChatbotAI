from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import ollama  # Para traducción opcional


class AirIndiaRetriever:
    def __init__(self):
        print("🔄 Inicializando retriever de Air India...")
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

        # Cargar la base de datos vectorial
        self.db = Chroma(
            persist_directory="chroma_db",
            embedding_function=self.embeddings
        )

        # Crear retriever
        self.retriever = self.db.as_retriever(
            search_kwargs={"k": 3}  # 3 documentos más relevantes
        )
        print("✅ Retriever de Air India cargado")

    def get_relevant_context(self, query):
        """
        Busca información relevante para una pregunta
        Usa invoke() en lugar de get_relevant_documents()
        """
        try:
            # Método CORRECTO para LangChain actual
            docs = self.retriever.invoke(query)

            if not docs:
                return None

            # Mantener contexto en inglés (como está en los chunks)
            context_parts = []
            for doc in docs:
                content = doc.page_content
                # Limpiar el contenido
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                cleaned = ' '.join(lines[:4])  # Primeras 4 líneas
                if cleaned:
                    context_parts.append(cleaned[:400])  # Limitar tamaño

            return "\n\n".join(context_parts) if context_parts else None

        except Exception as e:
            print(f"❌ Error en retriever: {e}")
            return None

    def search_direct(self, query, k=3):
        """
        Método alternativo: búsqueda directa en la base de datos
        """
        try:
            results = self.db.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Error en búsqueda directa: {e}")
            return []


# Crear instancia global
airindia_retriever = AirIndiaRetriever()


# Función helper para usar en app.py
def get_airindia_context(query):
    """
    Función simple para obtener contexto de Air India
    """
    try:
        return airindia_retriever.get_relevant_context(query)
    except:
        # Fallback: búsqueda directa
        docs = airindia_retriever.search_direct(query, k=2)
        if docs:
            context = "\n\n".join([doc.page_content[:300] for doc in docs])
            return context
        return None