"""
AFlam-Api V3 - Resolver Module
Orchestrates all extraction sources in parallel.
"""
import asyncio
from typing import Dict, List, Optional

from .extractors.vidsrc_me import resolve_vidsrc_me, resolve_vidsrc_to
from .extractors.other_sources import (
    resolve_111movies, resolve_vidcore, resolve_smashystream
)

# List of all extractors with their names
EXTRACTORS = [
    ("vidsrc_me", resolve_vidsrc_me, "VidSrc.me"),
    ("vidsrc_to", resolve_vidsrc_to, "VidSrc.to"),
    ("111movies", resolve_111movies, "111Movies"),
    ("vidcore", resolve_vidcore, "VidCore"),
    ("smashystream", resolve_smashystream, "SmashyStream"),
]


async def resolve_all(tmdb_id: str, media_type: str = "movie",
                      season: int = None, episode: int = None,
                      specific_source: str = None,
                      max_concurrent: int = 5) -> List[Dict]:
    """
    Resolve streams from all (or specific) sources in parallel.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_resolve(resolver_func, name, label):
        async with semaphore:
            try:
                res = await resolver_func(tmdb_id, media_type, season, episode)
                # Ensure each result has source info
                for r in res:
                    r["source_id"] = name
                    r["source_label"] = label
                return res
            except Exception as e:
                return []
    
    tasks = []
    for name, resolver, label in EXTRACTORS:
        if specific_source and name != specific_source:
            continue
        tasks.append(limited_resolve(resolver, name, label))
    
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten results
    all_results = []
    for result in task_results:
        if isinstance(result, list):
            all_results.extend(result)
    
    return all_results


def get_extractor_names() -> List[Dict]:
    """Return list of all available extractors."""
    return [{"id": name, "name": label} for name, _, label in EXTRACTORS]
