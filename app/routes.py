"""
AFlam-Api REST API Routes
FastAPI routes for stream extraction
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import time

from .config import (
    PROVIDERS, get_provider_by_id, get_all_providers, get_provider_count
)
from .utils.helpers import extract_parallel, format_response, get_best_streams

router = APIRouter()


@router.get("/")
async def root():
    """API health check and info."""
    return {
        "service": "AFlam-Api",
        "version": "2.0.0",
        "description": "Multi-Source M3u8 Stream Extraction API",
        "total_providers": get_provider_count(),
        "status": "online",
        "endpoints": {
            "health": "/health",
            "extract_all": "/extract",
            "extract_source": "/extract/{source}",
            "list_sources": "/sources",
            "extract_movies": "/extract/movies",
        }
    }


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers_count": get_provider_count(),
    }


@router.get("/sources")
async def list_sources():
    """List all available extraction sources."""
    sources = []
    for p in PROVIDERS:
        sources.append({
            "id": p.id,
            "label": p.label,
            "domain": p.domain,
        })
    return {
        "success": True,
        "total": len(sources),
        "sources": sources
    }


@router.get("/extract")
async def extract_all(
    tmdb_id: str = Query(..., description="TMDB movie or TV show ID"),
    type: str = Query("movie", description="Media type: movie or tv"),
    season: Optional[int] = Query(None, description="Season number (for TV)"),
    episode: Optional[int] = Query(None, description="Episode number (for TV)"),
    source: Optional[str] = Query(None, description="Specific source ID to extract from"),
):
    """
    Extract M3u8 streams from all sources (or a specific one).
    
    Supports both TMDB IDs and IMDb IDs (tt prefix).
    
    Examples:
        /extract?tmdb_id=550&type=movie
        /extract?tmdb_id=1399&type=tv&season=1&episode=1
        /extract?tmdb_id=tt1375666&type=movie
        /extract?tmdb_id=550&source=vidsrc.pm
    """
    if type not in ("movie", "tv"):
        raise HTTPException(status_code=400, detail="type must be 'movie' or 'tv'")

    if type == "tv" and (not season or not episode):
        raise HTTPException(
            status_code=400,
            detail="season and episode are required for TV shows"
        )

    # Build embed URLs for all providers (or specific one)
    embed_urls = []
    for provider in PROVIDERS:
        if source and provider.id != source:
            continue

        try:
            url = provider.build_url(tmdb_id, type, season, episode)
            if url:
                embed_urls.append({
                    "url": url,
                    "source_id": provider.id,
                    "label": provider.label
                })
        except Exception:
            pass

    if not embed_urls:
        raise HTTPException(status_code=400, detail="No valid URLs could be built")

    # Extract streams in parallel
    results = await extract_parallel(embed_urls)

    # Format response
    response = format_response(results, tmdb_id, type, season, episode)

    return response


@router.get("/extract/{source_id}")
async def extract_from_source(
    source_id: str,
    tmdb_id: str = Query(...),
    type: str = Query("movie"),
    season: Optional[int] = Query(None),
    episode: Optional[int] = Query(None),
):
    """Extract stream from a specific source."""
    provider = get_provider_by_id(source_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")

    try:
        url = provider.build_url(tmdb_id, type, season, episode)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    embed_urls = [{
        "url": url,
        "source_id": provider.id,
        "label": provider.label
    }]

    results = await extract_parallel(embed_urls)
    response = format_response(results, tmdb_id, type, season, episode)

    return response


@router.get("/streams/best")
async def best_streams(
    tmdb_id: str = Query(...),
    type: str = Query("movie"),
    season: Optional[int] = Query(None),
    episode: Optional[int] = Query(None),
):
    """
    Extract and return only the best available streams.
    Sorted by quality, subtitles, and extraction speed.
    """
    embed_urls = []
    for provider in PROVIDERS:
        try:
            url = provider.build_url(tmdb_id, type, season, episode)
            if url:
                embed_urls.append({
                    "url": url,
                    "source_id": provider.id,
                    "label": provider.label
                })
        except Exception:
            pass

    if not embed_urls:
        raise HTTPException(status_code=400, detail="No valid URLs could be built")

    results = await extract_parallel(embed_urls)
    best = get_best_streams(results)

    return {
        "success": True,
        "status": 200,
        "data": {
            "tmdb_id": tmdb_id,
            "type": type,
            "total_sources": len(embed_urls),
            "best_streams": best
        }
    }
