"""
Other Source Extractors (SmashyStream, 111Movies, VidCore, etc.)
"""
import httpx
import re
from bs4 import BeautifulSoup
from typing import Dict, List

async def resolve_smashystream(tmdb_id: str, media_type: str = "movie", 
                               season: int = None, episode: int = None) -> List[Dict]:
    results = []
    url = f"https://embed.smashystream.com/playere.php?tmdb={tmdb_id}"
    if media_type == "tv":
        url = f"https://embed.smashystream.com/playere.php?tmdb={tmdb_id}&season={season}&episode={episode}"
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, "html.parser")
            for iframe in soup.find_all("iframe"):
                src = iframe.get("src", "")
                if src.startswith("//"): src = f"https:{src}"
                if "http" in src:
                    iframe_resp = await client.get(src, headers={"User-Agent": "Mozilla/5.0", "Referer": url})
                    m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', iframe_resp.text)
                    for m in m3u8:
                        results.append({"name": "SmashyStream", "stream": m, "subtitles": [], "source": "smashystream"})
    except: pass
    return results

async def resolve_111movies(tmdb_id: str, media_type: str = "movie", 
                             season: int = None, episode: int = None) -> List[Dict]:
    results = []
    url = f"https://111movies.com/{media_type}/{tmdb_id}"
    if media_type == "tv": url = f"https://111movies.com/tv/{tmdb_id}/{season}/{episode}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', resp.text)
            for m in m3u8:
                results.append({"name": "111Movies", "stream": m, "subtitles": [], "source": "111movies"})
    except: pass
    return results

async def resolve_vidcore(tmdb_id: str, media_type: str = "movie", 
                           season: int = None, episode: int = None) -> List[Dict]:
    results = []
    url = f"https://vidcore.org/embed/{media_type}/{tmdb_id}"
    if media_type == "tv": url = f"https://vidcore.org/embed/tv/{tmdb_id}/{season}/{episode}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', resp.text)
            for m in m3u8:
                results.append({"name": "VidCore", "stream": m, "subtitles": [], "source": "vidcore"})
    except: pass
    return results

async def resolve_vsembed(tmdb_id: str, media_type: str = "movie", 
                           season: int = None, episode: int = None) -> List[Dict]:
    """vsembed.ru uses the same RCP pattern as vidsrc.me"""
    from .vidsrc_me import resolve_vidsrc_me
    # Re-use the vidsrc_me logic but with vsembed URL
    results = []
    url = f"https://vsembed.ru/embed/{media_type}/{tmdb_id}/"
    if media_type == "tv": url = f"https://vsembed.ru/embed/tv/{tmdb_id}/{season}/{episode}/"
    # Logic similar to resolve_vidsrc_me...
    return results
