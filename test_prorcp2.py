"""
Deep search in the /prorcp/ page for the actual video source
"""
import asyncio
import httpx
import re
import base64

async def search_prorcp():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Get the /prorcp/ URL
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        rcp_url = None
        for match in resp.text.split("\n"):
            if "cloudorchestranova.com/rcp/" in match:
                m = re.search(r'https?://cloudorchestranova\.com/rcp/[A-Za-z0-9+/=]+', match)
                if m:
                    rcp_url = m.group()
                    break
        
        if not rcp_url:
            # Try from iframe
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            iframe = soup.find("iframe")
            if iframe:
                rcp_url = iframe.get("src", "")
                if rcp_url.startswith("//"):
                    rcp_url = f"https:{rcp_url}"
        
        print(f"RCP URL: {rcp_url[:80]}...")
        
        # Get RCP page to find /prorcp/ path
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        if prorcp_match:
            prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
            print(f"PRO-RCP URL: {prorcp_full[:80]}...")
        else:
            print("No /prorcp/ found")
            return
        
        # Fetch the /prorcp/ page
        prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
        
        # Search for ALL URLs in the page
        print(f"\n--- SEARCHING FOR URLS IN /prorcp/ PAGE ---")
        urls = re.findall(r'https?://[^\s"\'>\)]+', prorcp_resp.text)
        unique_urls = sorted(set(urls))
        print(f"Total unique URLs: {len(unique_urls)}")
        for u in unique_urls[:30]:
            if any(x in u for x in ['m3u8', 'vidsrc', 'stream', 'player', 'embed', 'cdn', 'cloud', 'file']):
                print(f"  {u[:100]}")
        
        # Search for encoded patterns (hex, base64)
        print(f"\n--- SEARCHING FOR ENCODED PATTERNS ---")
        
        # Look for hex-encoded URLs
        hex_matches = re.findall(r'[0-9a-fA-F]{20,}', prorcp_resp.text)
        print(f"Hex strings found: {len(hex_matches)}")
        for h in hex_matches[:5]:
            if len(h) > 20:
                try:
                    decoded = bytes.fromhex(h).decode('utf-8')
                    if 'http' in decoded or 'm3u8' in decoded:
                        print(f"  Hex decoded: {decoded[:80]}")
                except:
                    pass
        
        # Look for base64 patterns
        b64_matches = re.findall(r'[A-Za-z0-9+/]{40,}={0,2}', prorcp_resp.text)
        print(f"\nBase64 strings found: {len(b64_matches)}")
        for b in b64_matches[:5]:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                if 'http' in decoded or 'm3u8' in decoded:
                    print(f"  Base64 decoded: {decoded[:80]}")
            except:
                pass
        
        # Look for the player initialization
        print(f"\n--- PLAYER INITIALIZATION ---")
        for match in re.finditer(r'player[^a-z]*[=:]["\']?([^"\'>\n]+)', prorcp_resp.text, re.IGNORECASE):
            val = match.group(1)[:100]
            if val and len(val) > 5:
                print(f"  player value: {val}")
        
        # Look for file: or src: patterns
        print(f"\n--- FILE/SRC PATTERNS ---")
        for match in re.finditer(r'(?:file|src|source)[\s:=]+["\']([^"\']+)["\']', prorcp_resp.text, re.IGNORECASE):
            val = match.group(1)
            if 'http' in val or 'm3u8' in val or len(val) > 20:
                print(f"  {match.group(0)[:120]}")
        
        # Look for the XOR data-h pattern in scripts
        print(f"\n--- DATA-H/DATA-I IN SCRIPTS ---")
        data_h_match = re.search(r'data-h=["\']([^"\']+)["\']', prorcp_resp.text)
        if data_h_match:
            print(f"  data-h found: {data_h_match.group(1)[:50]}...")
        else:
            print("  No data-h in HTML")
        
        # Look for JavaScript that might contain the encoded URL
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', prorcp_resp.text, re.DOTALL)
        print(f"\nScripts: {len(scripts)}")
        for i, script in enumerate(scripts):
            if script and len(script) > 50:
                # Look for any URL-like patterns
                script_urls = re.findall(r'https?://[^\s"\'>\)]+', script)
                if script_urls:
                    print(f"  Script {i} URLs: {len(script_urls)}")
                    for u in script_urls[:5]:
                        print(f"    {u[:80]}")
                
                # Look for encoded data
                if 'rc4' in script.lower() or 'xor' in script.lower() or 'decode' in script.lower():
                    print(f"  Script {i} has crypto: {script[:200]}")


async def test_direct_vidsrc_stream():
    """Try the VidSrc PRO direct approach"""
    print("\n" + "=" * 60)
    print("Test: Direct VidSrc PRO stream extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Try the VidSrc PRO direct API
        url = "https://vidsrc.stream/rcp/YzE2YjM3MmQ0YzFhY2MxODk2NzhhNTMxYzJjMGZiMWU6Tm1oRFNtUmFZMVZpZEN0NWRFd3ZUM1p1TkZodlExbE5SRXBDSzFwaE0wUnNjVGhzU0VrNU5IVk1TMFo1TTNGTlJrNTRNM2RVTUhoUmIwVTFOVGxMTmpoU1EzTlRlVXBhV2tSd1lVUjFWaXQyWVVWUFYwNDFTM0JaWkhoUmVVbDNkRXAxT1c1c00zcGlaR1ZNWjNoYVowTmtZMGhHYlM4d1ZWaEpiVUZMYkZOcVRucENVWFJ5VjI1MmVTdDNhRU5pYUZoRmVFNXdXRkJyZDB0aE4weFhWalk0VDBvMU1VeG5NREYxZVRBd1MycDFSRkJ6VFc5MmQxVjBRa2xyU0VGdWJXSm5TVXg2ZFhSSGFXUnpaMU5KYlZCa09HaFdSMVZpYUVadFEybENSRVowZVdWdlpEYzBURzQ0Tmtsd1NFVXlURmhaYzJaMmRVNHhNalZCY0M4NVJrSjNiMEZ5Vmt0U05sRnJkMVJQWkdkd1RGbE5abWRYUjJob1J6WmtZalJ2WTNaeFRITTROWEZCWlc5QloyUjRZVGROVHpOd1IzUnFiV0Y2YVRaUFJYQnNWMWRNYUROMWVuVkRZWFpQWWpGa1FYTXJaV3ROTmpoeWRXazBUa2c1Y1ZoaU5WUkRaMDVUUm5JemNYUnVURU0xVVVSc1QyaDFNR2xLVmpkdVR5dGFVak15YUdvdmRTdElkbGxNTDI1dWRGWkZja1UxYlRGeFQwNXlMMGxpY0djMlkwRkhOR2xwV0U5c09XRlJNbFV6UlcxclVGTktTbVUwVlZScE4xRlljbXRrV0dwTE5WVmhOR1ZPWTJOQlNtaDJkSGxuUldoSVVVNVBlbWMyUkU5R1JuVmxUblZCT0NzNFRVZDROVEpOVUcxSVZGWnRSRVpHZFVaamFtNXdWbWtyYWs5VFdrTXdZbW8xYjNGSFp6RXJZMFpDTUhSWE1FOW9RalIwYlhrMU5HZE9iakpJZDJ0SFRVdGxXREY1VjNwbGQyZDJSbVIyT1ZaQk4xRlpaekZLUXpWV2VESkVibHBwYmpKemQyUkxRbk42WjNaRFNXa3JZWGxFVGxkbU9GUk1VMFZYVFhadVRtUXdTVFpqV25OWGMyVTRkRFpXZFhkcVdUaDRhR3RQTm01blVISktXVEp5VG10cFpDdENabGQ1TUVwT2J5czRWV2xWVFU4clVXNXNabkZQTkdOc1lXMHpTRTV6Y1hSVFpraFFiRVl2Y21reVRHOVdRMk0xUzJZeVlWWjBXVTV4VFVSdmVEVllURVV6UlhGU2REbFFTbkJ1VFZWeVYwZHZhVU5MVFM5MFYyRjFaMHh6YTFkaU5tZGtRVGxsVUVWalRqaHBLMU5YYlVkaVlVRXlaV2N2TldOSVVucHRVbFV4YzJsRFJqVklNVlZFWTBzNWQzbHRiVlZOU2k4ekwyMXFlQ3RrUW10Mk1rbFVTa3h5V0hSb05ESmpla1JUVDBWNFRrMHlaMkp5U21RNGVFRkViWGc0WVhocFoyVm9SRFYyVERKd2REaE1WVFpVU1ZSTVNWQnpaelJ4Y1dZNU5qWXdTV2RrTVdwM2JIY3ZjbU5OVm1vd1dreGtibFZhYkhOdVpHZGpkMHN2TmpGSlIyMDNVMHgyWW1KRmVFNTZla3RTVTJ3M1FrRmxOVWx6U2pCMUsyMXNlak1yVkhodUwzWTBaM0ZYVHpWcFFVVlVSVGhVVnpsTVVFTm9SRm92TVRjMWFubFNRa041YmxCNVFtRkVNRk5NWW1OVVRUQjVaRTFQTUd0cVVtdHdTVGxWUTI1dlVVNHJhVlpuTW5KV1RFMWhSVkJOWmk5WlJFOTNUaTlGT0c5cWRqWTFiREZwYmxGM01EQk1ZamxsVFZaVlJub3dlR3hVU25KWVJqZG5aMk5wTWpkcU5uWnBZMng0SzIxMGRHdENSVkoyYzNobmJ6WlVVVEpzYm5NMWRtZE9NM05XVldSSVRuUkNkMVZQVW14Q2QybERhbFZKYUUxNlZtazRObUZTY2xFdllrczFWbXhoVVZReVJWVnJVSE5s"
        print(f"Fetching: {url[:60]}...")
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body length: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 1000:
            # Look for the video source
            print(f"\nPage preview:\n{resp.text[:2000]}")


async def main():
    await search_prorcp()
    await test_direct_vidsrc_stream()

if __name__ == "__main__":
    asyncio.run(main())
