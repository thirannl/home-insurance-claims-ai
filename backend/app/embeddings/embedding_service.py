from langchain_huggingface import HuggingFaceEmbeddings
import os

# Force offline mode so sentence-transformers uses the local cache only.
# The model (all-MiniLM-L6-v2) is already cached; this prevents the
# httpx/huggingface_hub network check that crashes at server startup.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

class EmbeddingService:
    def __init__(self):
        # Using the same model as before, but through LangChain's HuggingFace wrapper
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

    def get_embeddings_model(self):
        return self.embeddings

# Singleton instance
embedding_service = EmbeddingService()
