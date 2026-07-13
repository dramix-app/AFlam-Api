"""
Utility functions for parallel extraction and response formatting
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from ..config import MAX_CONCURRENT
from ..extractors.base_extractor import PlaywrightExtractor, StreamResult


async def extract_parallel(
    embed_urls: List[Dict[str, str]],
    max_concurrent: int = MAX_CONCURRENT
) -> List[StreamResult]:
    """
    Extract streams from multiple sources in parallel.
    
    Args:
        embed_urls: List of dicts with keys 'url', 'source_id', 'label'
        max_concurrent: Maximum number of concurrent extractions
    
    Returns:
        List of StreamResult objects
    """
    extractor = PlaywrightExtractor()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_extract(url_info: Dict[str, str]) -> StreamResult:
        async with semaphore:
            return await extractor.extract(
                embed_url=url_info["url"],
                source_id=url_info["source_id"],
                label=url_info["label"]
            )

    tasks = [limited_extract(url_info) for url_info in embed_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append(StreamResult(
                embed_urls[i]["source_id"],
                embed_urls[i]["label"]
            ))
            processed[-1].error = str(result)[:200]
        else:
            processed.append(result)

    return processed


def format_response(
    results: List[StreamResult],
    tmdb_id: str,
    media_type: str,
    season: Optional[int] = None,
    episode: Optional[int] = None
) -> Dict[str, Any]:
    """
    Format extraction results into a clean API response.
    """
    success_results = [r for r in results if r.is_success]
    error_results = [r for r in results if not r.is_success]

    total_time = max((r.extract_time for r in results), default=0)

    response = {
        "success": True,
        "status": 200,
        "data": {
            "tmdb_id": tmdb_id,
            "type": media_type,
            "season": season,
            "episode": episode,
            "total_sources": len(results),
            "successful": len(success_results),
            "failed": len(error_results),
            "total_extract_time": round(total_time, 2),
            "sources": []
        }
    }

    # Add successful sources first
    for r in sorted(success_results, key=lambda x: x.extract_time):
        source_data = {
            "source": r.source_id,
            "label": r.label,
            "status": "success",
            "stream": r.hls_url,
            "hls_url": r.hls_url,
            "embed_url": r.embed_url,
            "subtitles": r.subtitles,
            "qualities": r.qualities,
            "extract_time": r.extract_time
        }
        response["data"]["sources"].append(source_data)

    # Then add failed sources
    for r in error_results:
        source_data = {
            "source": r.source_id,
            "label": r.label,
            "status": "error",
            "error": r.error,
            "embed_url": r.embed_url,
            "extract_time": r.extract_time
        }
        response["data"]["sources"].append(source_data)

    return response


def get_best_streams(results: List[StreamResult]) -> List[Dict[str, Any]]:
    """
    Get the best available streams (sorted by quality and speed).
    """
    successful = [r for r in results if r.is_success]
    
    # Sort by: has qualities > more subtitles > faster extraction
    def sort_key(r):
        has_qualities = len(r.qualities) > 0
        sub_count = len(r.subtitles)
        return (-int(has_qualities), -sub_count, r.extract_time)
    
    return [r.to_dict() for r in sorted(successful, key=sort_key)]
