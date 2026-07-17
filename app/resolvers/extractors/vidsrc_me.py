"""
VidSrc.me / VidSrc.in / VidSrc.pm / VidSrc.net resolver
Pattern: Visit embed page -> Get server hash -> RCP redirect -> /prorcp/ -> M3u8
"""
import re
import httpx
import base64
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

async def resolve_vidsrc_me(tmdb_id: str, media_type: str = "movie", 
                            season: int = None, episode: int = None) -> List[Dict]:
    """
    Resolve streams from VidSrc.me ecosystem using the /prorcp/ pattern.
    """
    results = []
    
    # Build embed URL
    url = f"https://vidsrc.me/embed/{tmdb_id}"
    if media_type == "tv" and season and episode:
        url += f"/{season}-{episode}/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # 1. Get the embed page to find the RCP iframe
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return results
            
            soup = BeautifulSoup(resp.text, "html.parser")
            iframe = soup.find("iframe")
            if not iframe:
                return results
            
            rcp_url = iframe.get("src", "")
            if rcp_url.startswith("//"):
                rcp_url = f"https:{rcp_url}"
            
            # 2. Fetch RCP page to find /prorcp/ path
            rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
            if rcp_resp.status_code != 200:
                return results
            
            prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
            if not prorcp_match:
                return results
            
            prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
            
            # 3. Fetch /prorcp/ page which contains M3u8 URLs
            prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
            if prorcp_resp.status_code != 200:
                return results
            
            # 4. Extract M3u8 URLs
            m3u8_urls = re.findall(r'https?://[^\s"\'\)\]>\n]+\.(?:m3u8|m3u)[^\s"\'\)\]>\n]*', prorcp_resp.text)
            
            # 5. Extract Subtitles
            sub_matches = re.findall(r'\{file:["\'](https?://[^"\']+\.(?:vtt|srt)[^"\']*)["\'],\s*label:["\']([^"\']+)["\']', prorcp_resp.text)
            subtitles = [{"lang": label, "file": s_url} for s_url, label in sub_matches]
            
            for m_url in m3u8_urls:
                # Clean URL (remove placeholder tokens)
                clean_url = m_url.replace('?token=__TOKEN__', '').replace('?token=__TOKENPG__', '')
                
                # Identify source
                source_name = "VidSrc PRO"
                if "putgate" in clean_url:
                    source_name = "VidSrc Putgate"
                elif "roilandrelic" in clean_url:
                    source_name = "VidSrc Roil"
                
                results.append({
                    "name": source_name,
                    "stream": clean_url,
                    "subtitles": subtitles,
                    "source": "vidsrc.me",
                })
                    
    except Exception:
        pass
    
    return results

async def resolve_vidsrc_to(tmdb_id: str, media_type: str = "movie",
                            season: int = None, episode: int = None) -> List[Dict]:
    """
    VidSrc.to currently uses a similar pattern but proxies to vsembed.ru.
    """
    # For now, vidsrc.to can be resolved using the same logic if we find the embed URL
    results = []
    # Implementation can be expanded later
    return results
