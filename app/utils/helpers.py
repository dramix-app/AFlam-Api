"""
AFlam-Api V3 - Utility helpers (minimal, routes handle formatting)
"""
import time
from typing import Dict, Any, Optional

_cache: Dict[str, Dict[str, Any]] = {}


def get_cache(key: str, ttl: int = 900) -> Optional[Dict[str, Any]]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def set_cache(key: str, data: Dict[str, Any]):
    _cache[key] = {"ts": time.time(), "data": data}


def clear_cache():
    _cache.clear()
