from langchain_huggingface import HuggingFaceEmbeddings
import os

class EmbeddingService:
    def __init__(self):
        # Using the same model as before, but through LangChain's HuggingFace wrapper
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

    def get_embeddings_model(self):
        return self.embeddings

# Singleton instance
embedding_service = EmbeddingService()
