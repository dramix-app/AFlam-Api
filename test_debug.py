"""
Debug test - see what each resolver is actually getting
"""
import asyncio
import httpx
from bs4 import BeautifulSoup

async def debug_vidsrc_me():
    """Debug VidSrc.me extraction step by step"""
    print("=" * 60)
    print("DEBUG: VidSrc.me step-by-step")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidsrc.me/embed/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get embed page
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        print(f"   Final URL: {resp.url}")
        print(f"   Body length: {len(resp.text)}")
        
        # Check if it's a real page or redirect
        if "vidsrc" in resp.url.host.lower():
            print("   ✓ On VidSrc domain")
        else:
            print(f"   Redirected to: {resp.url}")
        
        # Parse the page
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for servers
        servers = soup.find_all("div", {"class": "server"})
        print(f"\n2. Found {len(servers)} server divs:")
        for s in servers:
            print(f"   - {s.text.strip()} | data-hash: {s.get('data-hash', 'NONE')[:30]}")
        
        if not servers:
            print("   No server divs found. Let's look at the page structure:")
            # Try to find any relevant content
            title = soup.find("title")
            if title:
                print(f"   Page title: {title.text}")
            
            # Look for scripts
            scripts = soup.find_all("script")
            print(f"   Scripts: {len(scripts)}")
            for sc in scripts[:3]:
                src = sc.get("src", "")
                text = sc.text[:100] if sc.text else ""
                print(f"     - src={src[:50]} | text={text[:50]}")
            
            # Look for iframes
            iframes = soup.find_all("iframe")
            print(f"   Iframes: {len(iframes)}")
            for iframe in iframes[:3]:
                print(f"     - src: {iframe.get('src', '')[:80]}")
            
            # Look for any data attributes
            for div in soup.find_all("div")[:10]:
                attrs = {k: v for k, v in div.attrs.items() if k.startswith("data")}
                if attrs:
                    print(f"   Div with data attrs: {attrs}")


async def debug_vidsrc_to():
    """Debug VidSrc.to extraction step by step"""
    print("\n" + "=" * 60)
    print("DEBUG: VidSrc.to step-by-step")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidsrc.to/embed/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        print(f"   Final URL: {resp.url}")
        print(f"   Body length: {len(resp.text)}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for data-id anchor
        data_anchor = soup.find("a", {"data-id": True})
        if data_anchor:
            sources_id = data_anchor.get("data-id")
            print(f"\n2. Found data-id: {sources_id}")
            
            # Get episode sources
            sources_url = f"https://vidsrc.to/ajax/embed/episode/{sources_id}/sources"
            print(f"   Fetching: {sources_url}")
            sources_resp = await client.get(sources_url, headers=headers)
            print(f"   Status: {sources_resp.status_code}")
            
            if sources_resp.status_code == 200:
                try:
                    sources_data = sources_resp.json()
                    print(f"   Sources: {sources_data}")
                except Exception as e:
                    print(f"   JSON parse error: {e}")
                    print(f"   Raw: {sources_resp.text[:200]}")
        else:
            print("   No data-id anchor found")
            
            # Check page content
            title = soup.find("title")
            if title:
                print(f"   Page title: {title.text}")
            
            # Check for scripts with data
            scripts = soup.find_all("script")
            for sc in scripts[:5]:
                text = sc.text[:200] if sc.text else ""
                if text and ("vidsrc" in text.lower() or "source" in text.lower() or "embed" in text.lower()):
                    print(f"   Script: {text[:100]}")


async def debug_111movies():
    """Debug 111Movies extraction"""
    print("\n" + "=" * 60)
    print("DEBUG: 111Movies step-by-step")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://111movies.net/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        print(f"   Final URL: {resp.url}")
        print(f"   Body length: {len(resp.text)}")
        
        # Look for m3u8
        import re
        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', resp.text)
        print(f"\n2. Found {len(m3u8_urls)} M3u8 URLs:")
        for m in m3u8_urls[:5]:
            print(f"   - {m[:80]}")
        
        # Look for iframes
        soup = BeautifulSoup(resp.text, "html.parser")
        iframes = soup.find_all("iframe")
        print(f"\n3. Found {len(iframes)} iframes:")
        for iframe in iframes[:5]:
            src = iframe.get("src", "")
            print(f"   - {src[:100]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        print(f"\n4. Found {len(scripts)} scripts")
        for sc in scripts[:5]:
            text = sc.text[:200] if sc.text else ""
            if "m3u8" in text.lower() or "player" in text.lower() or "embed" in text.lower():
                print(f"   Script: {text[:100]}")


async def debug_vidcore():
    """Debug VidCore extraction"""
    print("\n" + "=" * 60)
    print("DEBUG: VidCore step-by-step")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidcore.org/embed/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        print(f"   Final URL: {resp.url}")
        print(f"   Body length: {len(resp.text)}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for iframes
        iframes = soup.find_all("iframe")
        print(f"\n2. Found {len(iframes)} iframes:")
        for iframe in iframes[:5]:
            src = iframe.get("src", "")
            print(f"   - {src[:100]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        for sc in scripts[:5]:
            text = sc.text[:200] if sc.text else ""
            if "m3u8" in text.lower() or "player" in text.lower():
                print(f"   Script: {text[:100]}")


async def main():
    await debug_vidsrc_me()
    await debug_vidsrc_to()
    await debug_111movies()
    await debug_vidcore()

if __name__ == "__main__":
    asyncio.run(main())
