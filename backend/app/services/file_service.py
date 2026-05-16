import pdfplumber
import os
from typing import Optional

class FileService:
    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            raise e
        return text

    @staticmethod
    async def extract_text_from_txt(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            raise e

    @staticmethod
    async def extract_text_from_docx(file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error reading DOCX file: {e}")
            raise e

    @classmethod
    async def get_document_text(cls, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return await cls.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return await cls.extract_text_from_docx(file_path)
        elif ext in ['.txt', '.json']:
            return await cls.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
