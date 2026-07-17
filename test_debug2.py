"""
Deep debug - find the actual video player patterns in each source
"""
import asyncio
import httpx
import re
from bs4 import BeautifulSoup

async def debug_vidsrcme_detail():
    """VidSrc.me now uses rcp pattern via iframe to cloudorchestranova.com"""
    print("=" * 60)
    print("DEBUG: VidSrc.me - Detailed iframe analysis")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidsrc.me/embed/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the iframe
        iframe = soup.find("iframe")
        if iframe:
            src = iframe.get("src", "")
            if src.startswith("//"):
                src = f"https:{src}"
            print(f"\nIframe src: {src}")
            
            # Fetch the iframe content
            print(f"\nFetching iframe content...")
            iframe_resp = await client.get(src, headers={**headers, "Referer": "https://vidsrc.me/"})
            print(f"Status: {iframe_resp.status_code}")
            print(f"Body length: {len(iframe_resp.text)}")
            
            # Look for any URLs
            urls = re.findall(r'https?://[^\s"\']*', iframe_resp.text)
            print(f"\nFound {len(urls)} URLs in iframe page:")
            for u in set(urls)[:20]:
                if 'cloudorchestra' in u or 'rcp' in u or 'm3u8' in u or 'player' in u:
                    print(f"  - {u[:80]}")
            
            # Look for scripts with data
            scripts = soup.find_all("script")
            for sc in scripts:
                text = sc.text
                if len(text) > 50:
                    # Look for rcp, m3u8, player, embed
                    for keyword in ['rcp', 'm3u8', 'player', 'embed', 'source', 'video']:
                        if keyword in text.lower():
                            print(f"\nScript contains '{keyword}':")
                            idx = text.lower().index(keyword)
                            print(f"  Context: {text[max(0,idx-50):idx+100]}")
                            break


async def debug_111movies_detail():
    """111Movies redirects to player.vidlove.cc"""
    print("\n" + "=" * 60)
    print("DEBUG: 111Movies - player.vidlove.cc analysis")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://111movies.net/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        print(f"Final URL: {resp.url}")
        print(f"Body length: {len(resp.text)}")
        
        # Print all scripts
        scripts = soup.find_all("script")
        print(f"\nScripts ({len(scripts)}):")
        for i, sc in enumerate(scripts):
            src = sc.get("src", "")
            text = sc.text[:300] if sc.text else ""
            print(f"  Script {i}: src={src[:50]} | len={len(sc.text)}")
            if src or text:
                print(f"    Content preview: {(src or text)[:100]}")
        
        # Look for any JS with URLs
        for sc in scripts:
            if sc.text:
                # Find any URLs in the script
                urls_in_script = re.findall(r'https?://[^\s"\']+', sc.text)
                for u in urls_in_script[:5]:
                    print(f"  URL in script: {u[:80]}")


async def debug_vidcore_detail():
    """VidCore - find the player pattern"""
    print("\n" + "=" * 60)
    print("DEBUG: VidCore - Detailed analysis")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidcore.org/embed/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for all URLs in the page
        urls = re.findall(r'https?://[^\s"\']+', resp.text)
        print(f"\nFound {len(urls)} URLs in page:")
        for u in set(urls)[:20]:
            if any(x in u for x in ['player', 'embed', 'm3u8', 'video', 'stream', 'cloud']):
                print(f"  - {u[:80]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        print(f"\nScripts ({len(scripts)}):")
        for sc in scripts[:5]:
            src = sc.get("src", "")
            text = sc.text[:300] if sc.text else ""
            content = src or text
            if content and any(x in content.lower() for x in ['player', 'embed', 'm3u8', 'video']):
                print(f"  Script with video content: {content[:150]}")


async def debug_vidsrcme_rcp():
    """Debug the RCP iframe from VidSrc.me"""
    print("\n" + "=" * 60)
    print("DEBUG: VidSrc.me RCP iframe direct analysis")
    print("=" * 60)
    
    # The iframe from the page: https://cloudorchestranova.com/rcp/...
    rcp_url = "https://cloudorchestranova.com/rcp/MWQ0Y2IzZmMwMzUwNWVlYjEzYmMzZjc2ZDI0YTc0OWM6Yml0UmJmZGFkYjE0MWUxMzQ3NTIyY2IxMDM0Y2M0NjE3Ng=="
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.me/",
        }
        
        print(f"Fetching: {rcp_url[:60]}...")
        resp = await client.get(rcp_url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body length: {len(resp.text)}")
        print(f"Final URL: {resp.url}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for hidden div and body data attributes
        hidden = soup.find("div", {"id": "hidden"})
        body = soup.find("body")
        
        if hidden:
            print(f"\nHidden div data-h: {hidden.get('data-h', 'NONE')[:50]}")
        else:
            print("\nNo hidden div found")
        
        if body:
            print(f"Body data-i: {body.get('data-i', 'NONE')[:30]}")
        
        # Look for iframes
        iframes = soup.find_all("iframe")
        print(f"\nIframes: {len(iframes)}")
        for iframe in iframes:
            src = iframe.get("src", "")
            print(f"  - {src[:100]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        print(f"\nScripts: {len(scripts)}")
        for sc in scripts[:5]:
            text = sc.text[:200] if sc.text else ""
            if text:
                print(f"  Content: {text[:100]}")


async def main():
    await debug_vidsrcme_detail()
    await debug_111movies_detail()
    await debug_vidcore_detail()
    await debug_vidsrcme_rcp()

if __name__ == "__main__":
    asyncio.run(main())
