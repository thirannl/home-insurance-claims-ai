# Home Insurance Claims AI - Backend

## Project Overview
Automated insurance claim assessment using RAG.

## Tech Stack
- **Framework:** FastAPI
- **Database:** Supabase PostgreSQL
- **Vector Search:** FAISS (Separate local index files per policy)
- **LLM:** Groq API (Llama 3)
- **Embeddings:** `sentence-transformers`
- **PDF Processing:** `pdfplumber`

## Status: Step-by-Step Implementation
Current Phase: Phase 4 (Vector Storage with FAISS)

## Setup & Installation
1. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
2. Activate the virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Running the Server
You can start the FastAPI server using the provided PowerShell script (which automatically activates the virtual environment):
```powershell
.\run.ps1
```

Alternatively, you can run it manually with Uvicorn (make sure your virtual environment is active):
```powershell
uvicorn main:app --reload
```

## Testing the API
You can test the API using the Swagger UI at: `http://127.0.0.1:8000/docs`

Alternatively, use these PowerShell commands:
- **Login Test**:
  ```powershell
  Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login -ContentType "application/json" -Body '{"accessor_id": "1", "password": "kris123"}'
  ```
- **Check Status**:
  ```powershell
  Invoke-RestMethod -Uri http://127.0.0.1:8000/
  ```
