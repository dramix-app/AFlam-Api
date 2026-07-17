"""
AFlam-Api V3.1 - Multi-Source M3u8 Stream Extraction API
Resolver-based: HTTP extraction from proven sources with caching.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time

load_dotenv()
from app.routes import router
from app.config import PORT
from app.resolvers import get_extractor_names

app = FastAPI(
    title="AFlam-Api",
    description="Multi-Source M3u8 Stream Extraction API",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "total_sources": len(get_extractor_names()),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True, log_level="info")
