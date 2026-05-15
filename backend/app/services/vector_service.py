from langchain_community.vectorstores import FAISS
import os
from typing import List
from app.embeddings.embedding_service import embedding_service
from dotenv import load_dotenv

load_dotenv()

FAISS_INDEX_DIR = os.getenv("FAISS_INDEX_DIR", "./app/vector_store")

class VectorService:
    def create_and_save_index(self, chunks: List[str], policy_id: str):
        """
        Creates a FAISS index from text chunks and saves it to disk using LangChain.
        """
        if not chunks:
            return None
            
        # LangChain's FAISS handles embedding and storage in one go
        vectorstore = FAISS.from_texts(
            texts=chunks,
            embedding=embedding_service.get_embeddings_model()
        )
        
        # Save the index locally
        folder_path = os.path.join(FAISS_INDEX_DIR, f"policy_{policy_id}")
        vectorstore.save_local(folder_path)
        
        return folder_path

    def search_index(self, query: str, policy_id: str, top_k: int = 3) -> List[str]:
        """
        Loads a policy index and searches for the most relevant text chunks.
        """
        folder_path = os.path.join(FAISS_INDEX_DIR, f"policy_{policy_id}")
        
        if not os.path.exists(folder_path):
            print(f"Index for {policy_id} not found at {folder_path}")
            return []
            
        # Load the index
        vectorstore = FAISS.load_local(
            folder_path, 
            embedding_service.get_embeddings_model(),
            allow_dangerous_deserialization=True # Required for loading local FAISS files
        )
        
        # Perform similarity search
        docs = vectorstore.similarity_search(query, k=top_k)
        
        # Return the page content of the matching documents
        return [doc.page_content for doc in docs]

# Singleton instance
vector_service = VectorService()
