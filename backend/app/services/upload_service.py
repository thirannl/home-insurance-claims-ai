import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.file_service import FileService
from app.services.vector_service import vector_service
from langchain_text_splitters import RecursiveCharacterTextSplitter

UPLOAD_DIR = "./app/uploads"

class UploadService:
    @staticmethod
    async def process_policy(db: Session, file_path: str, policy_id: str):
        """
        Extracts text from policy, chunks it with LangChain, and creates FAISS index.
        """
        # 1. Extract Text
        print("    -> Extracting text from policy file...")
        text_content = await FileService.get_document_text(file_path)
        print(f"    -> Extracted {len(text_content)} characters.")
        
        # 2. Chunk Text using LangChain's RecursiveCharacterTextSplitter
        print("    -> Chunking text...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        chunks = text_splitter.split_text(text_content)
        print(f"    -> Created {len(chunks)} chunks.")
        
        # 3. Create and Save FAISS Index (LangChain handles embeddings internally now)
        print("    -> Generating embeddings and saving FAISS index...")
        vector_service.create_and_save_index(chunks, policy_id)
        print("    -> FAISS index saved.")
        
        return len(chunks)

    @staticmethod
    async def process_tc(db: Session, file_path: str):
        """
        Processes global Terms & Conditions with LangChain.
        """
        text_content = await FileService.get_document_text(file_path)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_text(text_content)
        
        # Save as a special 'global' index
        vector_service.create_and_save_index(chunks, "global_tc")
        
        # 5. Insert new T&C location into DB (keeping history of previous records)
        try:
            query = text("INSERT INTO terms_and_conditions (location) VALUES (:loc)")
            db.execute(query, {"loc": file_path})
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error updating T&C in database: {e}")
            raise e
        
        return len(chunks)

    @staticmethod
    async def save_upload(file, sub_dir: str) -> str:
        """
        Saves an uploaded file to the local disk.
        """
        os.makedirs(os.path.join(UPLOAD_DIR, sub_dir), exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, sub_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        return file_path
