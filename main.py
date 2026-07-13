"""
AFlam-Api - Multi-Source M3u8 Stream Extraction API
Version: 2.0.0

A professional, high-performance API that extracts HLS/M3u8 video streams
from 28+ free video sources including movies, TV shows, and anime.

Features:
- Parallel extraction from multiple sources simultaneously
- Subtitle extraction (VTT/SRT format)
- Quality detection from M3u8 playlists
- Playwright-based headless browser extraction
- FastAPI with async/await support
- Deployable on Render, Railway, Fly.io, etc.

Endpoints:
    GET /                  - API info
    GET /health            - Health check
    GET /sources           - List all providers
    GET /extract           - Extract from all sources
    GET /extract/{source}  - Extract from specific source
    GET /streams/best      - Get best streams only
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time

load_dotenv()

from app.routes import router
from app.config import PORT, get_provider_count

app = FastAPI(
    title="AFlam-Api",
    description="Multi-Source M3u8 Stream Extraction API - Extract HLS video streams from 28+ free video providers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "AFlam-Api",
        "version": "2.0.0",
        "providers": get_provider_count(),
        "status": "online"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": get_provider_count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
