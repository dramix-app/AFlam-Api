"""
Debug - focus on what we found:
1. VidSrc.me -> redirects to vidsrcme.ru -> iframe to cloudorchestranova.com/rcp/...
2. 111Movies -> redirects to player.vidlove.cc/embed/movie/238
3. VidCore -> returns a page with scripts but no iframes
"""
import asyncio
import httpx
import re
from bs4 import BeautifulSoup
import base64

async def debug_vidsrcme_rcp():
    """Debug the RCP iframe from cloudorchestranova.com"""
    print("=" * 60)
    print("DEBUG: cloudorchestranova.com/rcp/...")
    print("=" * 60)
    
    rcp_url = "https://cloudorchestranova.com/rcp/YzE2YjM3MmQ0YzFhY2MxODk2NzhhNTMxYzJjMGZiMWU6Tm1oRFNtUmFZMVZpZEN0NWRFd3ZUM1p1TkZodlExbE5SRXBDSzFwaE0wUnNjVGhzU0VrNU5IVk1TMFo1TTNGTlJrNTRNM2RVTUhoUmIwVTFOVGxMTmpoU1EzTlRlVXBhV2tSd1lVUjFWaXQyWVVWUFYwNDFTM0JaWkhoUmVVbDNkRXAxT1c1c00zcGlaR1ZNWjNoYVowTmtZMGhHYlM4d1ZWaEpiVUZMYkZOcVRucENVWFJ5VjI1MmVTdDNhRU5pYUZoRmVFNXdXRkJyZDB0aE4weFhWalk0VDBvMU1VeG5NREYxZVRBd1MycDFSRkJ6VFc5MmQxVjBRa2xyU0VGdWJXSm5TVXg2ZFhSSGFXUnpaMU5KYlZCa09HaFdSMVZpYUVadFEybENSRVowZVdWdlpEYzBURzQ0Tmtsd1NFVXlURmhaYzJaMmRVNHhNalZCY0M4NVJrSjNiMEZ5Vmt0U05sRnJkMVJQWkdkd1RGbE5abWRYUjJob1J6WmtZalJ2WTNaeFRITTROWEZCWlc5QloyUjRZVGROVHpOd1IzUnFiV0Y2YVRaUFJYQnNWMWRNYUROMWVuVkRZWFpQWWpGa1FYTXJaV3ROTmpoeWRXazBUa2c1Y1ZoaU5WUkRaMDVUUm5JemNYUnVURU0xVVVSc1QyaDFNR2xLVmpkdVR5dGFVak15YUdvdmRTdElkbGxNTDI1dWRGWkZja1UxYlRGeFQwNXlMMGxpY0djMlkwRkhOR2xwV0U5c09XRlJNbFV6UlcxclVGTktTbVUwVlZScE4xRlljbXRrV0dwTE5WVmhOR1ZPWTJOQlNtaDJkSGxuUldoSVVVNVBlbWMyUkU5R1JuVmxUblZCT0NzNFRVZDROVEpOVUcxSVZGWnRSRVpHZFVaamFtNXdWbWtyYWs5VFdrTXdZbW8xYjNGSFp6RXJZMFpDTUhSWE1FOW9RalIwYlhrMU5HZE9iakpJZDJ0SFRVdGxXREY1VjNwbGQyZDJSbVIyT1ZaQk4xRlpaekZLUXpWV2VESkVibHBwYmpKemQyUkxRbk42WjNaRFNXa3JZWGxFVGxkbU9GUk1VMFZYVFhadVRtUXdTVFpqV25OWGMyVTRkRFpXZFhkcVdUaDRhR3RQTm01blVISktXVEp5VG10cFpDdENabGQ1TUVwT2J5czRWV2xWVFU4clVXNXNabkZQTkdOc1lXMHpTRTV6Y1hSVFpraFFiRVl2Y21reVRHOVdRMk0xUzJZeVlWWjBXVTV4VFVSdmVEVllURVV6UlhGU2REbFFTbkJ1VFZWeVYwZHZhVU5MVFM5MFYyRjFaMHh6YTFkaU5tZGtRVGxsVUVWalRqaHBLMU5YYlVkaVlVRXlaV2N2TldOSVVucHRVbFV4YzJsRFJqVklNVlZFWTBzNWQzbHRiVlZOU2k4ekwyMXFlQ3RrUW10Mk1rbFVTa3h5V0hSb05ESmpla1JUVDBWNFRrMHlaMkp5U21RNGVFRkViWGc0WVhocFoyVm9SRFYyVERKd2REaE1WVFpVU1ZSTVNWQnpaelJ4Y1dZNU5qWXdTV2RrTVdwM2JIY3ZjbU5OVm1vd1dreGtibFZhYkhOdVpHZGpkMHN2TmpGSlIyMDNVMHgyWW1KRmVFNTZla3RTVTJ3M1FrRmxOVWx6U2pCMUsyMXNlak1yVkhodUwzWTBaM0ZYVHpWcFFVVlVSVGhVVnpsTVVFTm9SRm92TVRjMWFubFNRa041YmxCNVFtRkVNRk5NWW1OVVRUQjVaRTFQTUd0cVVtdHdTVGxWUTI1dlVVNHJhVlpuTW5KV1RFMWhSVkJOWmk5WlJFOTNUaTlGT0c5cWRqWTFiREZwYmxGM01EQk1ZamxsVFZaVlJub3dlR3hVU25KWVJqZG5aMk5wTWpkcU5uWnBZMng0SzIxMGRHdENSVkoyYzNobmJ6WlVVVEpzYm5NMWRtZE9NM05XVldSSVRuUkNkMVZQVW14Q2QybERhbFZKYUUxNlZtazRObUZTY2xFdllrczFWbXhoVVZReVJWVnJVSE5s"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.me/",
        }
        
        resp = await client.get(rcp_url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body length: {len(resp.text)}")
        print(f"Final URL: {resp.url}")
        print(f"\nBody preview:\n{resp.text[:2000]}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        hidden = soup.find("div", {"id": "hidden"})
        body = soup.find("body")
        
        print(f"\nHidden div: {hidden is not None}")
        if hidden:
            data_h = hidden.get("data-h", "NONE")
            print(f"  data-h: {data_h[:50]}...")
        
        print(f"Body: {body is not None}")
        if body:
            data_i = body.get("data-i", "NONE")
            print(f"  data-i: {data_i[:30]}...")
        
        # Look for iframes
        iframes = soup.find_all("iframe")
        print(f"\nIframes: {len(iframes)}")
        for iframe in iframes:
            print(f"  src: {iframe.get('src', '')[:100]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        print(f"\nScripts: {len(scripts)}")
        for sc in scripts:
            src = sc.get("src", "")
            text = sc.text[:200] if sc.text else ""
            if src:
                print(f"  External: {src[:80]}")
            elif text:
                print(f"  Inline: {text[:100]}")


async def debug_111movies_vidlove():
    """Debug player.vidlove.cc which is what 111Movies redirects to"""
    print("\n" + "=" * 60)
    print("DEBUG: player.vidlove.cc (111Movies redirect target)")
    print("=" * 60)
    
    url = "https://player.vidlove.cc/embed/movie/238"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body length: {len(resp.text)}")
        print(f"\nBody preview:\n{resp.text[:3000]}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for iframes
        iframes = soup.find_all("iframe")
        print(f"\nIframes: {len(iframes)}")
        for iframe in iframes:
            print(f"  src: {iframe.get('src', '')[:100]}")
        
        # Look for scripts
        scripts = soup.find_all("script")
        print(f"\nScripts: {len(scripts)}")
        for sc in scripts:
            src = sc.get("src", "")
            text = sc.text[:200] if sc.text else ""
            if src:
                print(f"  External: {src[:80]}")
            elif text and len(text) > 10:
                print(f"  Inline ({len(text)} chars): {text[:100]}")


async def debug_vidcore_scripts():
    """Debug VidCore scripts to find the player pattern"""
    print("\n" + "=" * 60)
    print("DEBUG: VidCore scripts analysis")
    print("=" * 60)
    
    url = "https://vidcore.org/embed/movie/238"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Print ALL scripts
        scripts = soup.find_all("script")
        print(f"Total scripts: {len(scripts)}")
        for i, sc in enumerate(scripts):
            src = sc.get("src", "")
            text = sc.text
            if src:
                print(f"\n  [{i}] External: {src[:100]}")
            elif len(text) > 10:
                print(f"\n  [{i}] Inline ({len(text)} chars):")
                # Print first 300 chars
                print(f"    {text[:300]}")


async def debug_vidsrc_to_page():
    """Debug VidSrc.to - find the data-id or alternative pattern"""
    print("\n" + "=" * 60)
    print("DEBUG: VidSrc.to full page analysis")
    print("=" * 60)
    
    url = "https://vidsrc.to/embed/movie/238"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        print(f"Body length: {len(resp.text)}")
        print(f"\nFull page HTML:\n{resp.text}")


async def main():
    await debug_vidsrcme_rcp()
    await debug_111movies_vidlove()
    await debug_vidcore_scripts()
    await debug_vidsrc_to_page()

if __name__ == "__main__":
    asyncio.run(main())
