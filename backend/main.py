from dotenv import load_dotenv
# Load .env FIRST — before any app import that triggers the EmbeddingService
# singleton (embedding_service.py), so HF_HUB_OFFLINE & TRANSFORMERS_OFFLINE
# are already set when sentence-transformers initialises.
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, uploads
import uvicorn

app = FastAPI(
    title="Home Insurance Claims AI",
    description="Backend for automated insurance claim assessment",
    version="1.0.0"
)

# CORS — allow the Vite dev server and preview server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(uploads.router)

@app.get("/")
async def root():
    return {"message": "Home Insurance Claims AI API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

