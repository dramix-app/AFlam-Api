"""
AFlam-Api V3.1 - API Routes
Uses the new resolver-based architecture.
"""
import time
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from .resolvers import resolve_all, get_extractor_names
from .config import MAX_CONCURRENT, CACHE_TTL

router = APIRouter()

_cache: dict = {}

@router.get("/")
async def root():
    return {
        "service": "AFlam-Api",
        "version": "3.1.0",
        "status": "online",
        "sources": get_extractor_names()
    }

@router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@router.get("/sources")
async def list_sources():
    return {"sources": get_extractor_names()}

@router.get("/extract")
async def extract_streams(
    tmdb_id: str = Query(..., description="TMDB movie or TV show ID"),
    type: str = Query("movie", description="Media type: movie or tv"),
    season: Optional[int] = Query(None),
    episode: Optional[int] = Query(None),
    source: Optional[str] = Query(None)
):
    start_time = time.time()
    
    if type == "tv" and (season is None or episode is None):
        raise HTTPException(status_code=400, detail="season and episode are required for TV shows")
    
    # Cache check
    cache_key = f"{type}:{tmdb_id}:{season}:{episode}:{source}"
    if cache_key in _cache:
        entry = _cache[cache_key]
        if (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["data"]
            
    results = await resolve_all(
        tmdb_id=tmdb_id,
        media_type=type,
        season=season,
        episode=episode,
        specific_source=source,
        max_concurrent=MAX_CONCURRENT
    )
    
    response = {
        "success": len(results) > 0,
        "tmdb_id": tmdb_id,
        "type": type,
        "count": len(results),
        "results": results,
        "execution_time": round(time.time() - start_time, 2)
    }
    
    _cache[cache_key] = {"ts": time.time(), "data": response}
    return response

@router.get("/streams/best")
async def get_best_stream(
    tmdb_id: str = Query(..., description="TMDB ID"),
    type: str = Query("movie", regex="^(movie|tv)$"),
    season: Optional[int] = Query(None),
    episode: Optional[int] = Query(None)
):
    results = await resolve_all(tmdb_id, type, season, episode)
    if not results:
        raise HTTPException(status_code=404, detail="No streams found")
    
    # Sort by subtitle count then name
    results.sort(key=lambda x: (-len(x.get("subtitles", [])), x.get("name", "")))
    return results[0]
