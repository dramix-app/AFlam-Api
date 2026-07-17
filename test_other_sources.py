"""
Test other sources from the user's list (SmashyStream, 111Movies, etc.)
These might be easier to extract than VidSrc.me which has very strong protection.
"""
import asyncio
import httpx
import re
from bs4 import BeautifulSoup

async def test_smashystream():
    print("=" * 60)
    print("Test: SmashyStream Extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # SmashyStream pattern
        url = "https://embed.smashystream.com/playere.php?tmdb=238"
        print(f"1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        
        # Look for M3u8
        m3u8_urls = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', resp.text)
        if m3u8_urls:
            print(f"   Found M3u8: {m3u8_urls}")
            return True
        
        # Look for iframes
        soup = BeautifulSoup(resp.text, "html.parser")
        iframes = soup.find_all("iframe")
        print(f"   Iframes: {len(iframes)}")
        for iframe in iframes:
            src = iframe.get("src", "")
            print(f"     - {src[:80]}")
            
            # Follow iframe
            if src.startswith("//"):
                src = f"https:{src}"
            if 'http' in src:
                try:
                    iframe_resp = await client.get(src, headers={**headers, "Referer": url})
                    iframe_m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', iframe_resp.text)
                    if iframe_m3u8:
                        print(f"       Found M3u8 in iframe: {iframe_m3u8}")
                        return True
                except:
                    pass
        
        return False

async def test_111movies():
    print("\n" + "=" * 60)
    print("Test: 111Movies Extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # 111Movies pattern
        url = "https://111movies.com/movie/238"
        print(f"1. Fetching: {url}")
        try:
            resp = await client.get(url, headers=headers)
            print(f"   Status: {resp.status_code}")
            # Look for embed or video
            m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.m3u8[^\s"\'\)\]>\n]*', resp.text)
            if m3u8:
                print(f"   Found M3u8: {m3u8}")
                return True
        except:
            print("   Failed to fetch")
        
        return False

async def main():
    await test_smashystream()
    await test_111movies()

if __name__ == "__main__":
    asyncio.run(main())
