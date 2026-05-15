from fastapi import FastAPI
from app.routes import auth, uploads
import uvicorn

app = FastAPI(
    title="Home Insurance Claims AI",
    description="Backend for automated insurance claim assessment",
    version="1.0.0"
)

# Include Routers
app.include_router(auth.router)
app.include_router(uploads.router)

@app.get("/")
async def root():
    return {"message": "Home Insurance Claims AI API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
