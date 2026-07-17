"""
Test cloudnestra.com RCP endpoint directly
The sources.js shows: src: "//cloudnestra.com/rcp/" + $(this).data("hash")
This is the SAME pattern as cloudorchestranova.com
"""
import asyncio
import httpx
import re
import base64
from bs4 import BeautifulSoup
from urllib.parse import unquote

async def xor_decrypt(encoded_hex: str, seed: str) -> str:
    encoded_buffer = bytes.fromhex(encoded_hex)
    decoded = ""
    for i in range(len(encoded_buffer)):
        decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
    if decoded.startswith("//"):
        decoded = f"https:{decoded}"
    return decoded


async def test_nestra():
    """
    The iframe in the embed page is already the RCP URL from cloudorchestranova.com.
    Let's fetch it with proper Referer and User-Agent, then look at the /prorcp/ endpoint.
    
    The key is: the /prorcp/ page has data-i="0068646" and uses PlayerJS.
    The actual video source is loaded by PlayerJS through its driver script.
    
    Let's try to find the video source by looking at the network requests.
    """
    print("=" * 60)
    print("Test: cloudnestra.com/cloudorchestranova.com RCP chain")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get the embed page
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        print(f"1. RCP URL: {rcp_url[:80]}...")
        
        # Step 2: Fetch RCP page
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        
        # Find /prorcp/ path
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        if not prorcp_match:
            print("   No /prorcp/ found in RCP page")
            return False
        
        prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
        print(f"2. PRO-RCP: {prorcp_full[:80]}...")
        
        # Step 3: Fetch /prorcp/ page
        prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
        
        # The /prorcp/ page has PlayerJS. Let's find the driver script.
        print(f"3. PRO-RCP body length: {len(prorcp_resp.text)}")
        
        # Find the main driver script
        driver_match = re.search(r'src=["\'](/pjs/pjs_main_drv_cast\.[^"\']+)["\']', prorcp_resp.text)
        if driver_match:
            driver_url = driver_match.group(1)
            if not driver_url.startswith("http"):
                driver_url = f"https://cloudorchestranova.com{driver_url}"
            print(f"4. Driver script: {driver_url}")
            
            driver_resp = await client.get(driver_url, headers={**headers, "Referer": prorcp_full})
            print(f"   Driver body length: {len(driver_resp.text)}")
            print(f"   Driver preview:\n{driver_resp.text[:1000]}")
        
        # Look for the actual video source in the page
        # Search for patterns like source: "...", file: "...", src: "..."
        print(f"\n5. Searching for video source patterns...")
        
        # Pattern 1: Direct M3u8
        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', prorcp_resp.text)
        if m3u8_urls:
            print(f"   Direct M3u8: {m3u8_urls}")
        
        # Pattern 2: Base64 encoded data (the atob pattern)
        atob_matches = re.findall(r"atob\(['\"]([^'\"]+)['\"]\)", prorcp_resp.text)
        if atob_matches:
            print(f"\n6. Found {len(atob_matches)} atob patterns:")
            for m in atob_matches[:5]:
                try:
                    decoded = base64.b64decode(m).decode('utf-8')
                    print(f"   Decoded: {decoded[:80]}")
                except:
                    pass
        
        # Pattern 3: Look for the PlayerJS config
        player_config = re.search(r'new\s+Playerjs\(\{[^}]+\}\)', prorcp_resp.text, re.DOTALL)
        if player_config:
            print(f"\n7. PlayerJS config found:\n{player_config.group()[:500]}")
        
        # Pattern 4: Look for the video source in scripts
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', prorcp_resp.text, re.DOTALL)
        for i, script in enumerate(scripts):
            if script and len(script) > 50:
                # Look for video source patterns
                for pattern in ['file:', 'source:', 'src:', 'video:', 'm3u8', '.mp4', '.ts']:
                    if pattern in script.lower():
                        idx = script.lower().index(pattern)
                        print(f"\n8. Script {i} has '{pattern}' at position {idx}:")
                        print(f"   {script[max(0,idx-30):idx+100]}")
                        break
        
        # The /prorcp/ page uses pako to decompress gzip data
        # Let's look for gzip data patterns
        print(f"\n9. Looking for gzip/compressed data...")
        gzip_urls = re.findall(r'https?://[^\s"\']+\.gz[^\s"\']*', prorcp_resp.text)
        if gzip_urls:
            print(f"   Gzip URLs: {gzip_urls}")
        
        # Look for the pako usage
        pako_usage = re.search(r'pako\.(inflate|decompress)\([^)]+\)', prorcp_resp.text)
        if pako_usage:
            print(f"   Pako usage: {pako_usage.group()}")
        
        # Look for the actual source loading code
        # The player loads source from a script that calls pako
        source_scripts = re.findall(r'src=["\'](/sV05[^"\']+|/f59d[^"\']+)', prorcp_resp.text)
        for s in source_scripts:
            print(f"   Obfuscated script: {s[:80]}")
        
        return False


async def test_nestra_prorcp_page():
    """Fetch the /prorcp/ page and search for the actual video source"""
    print("\n" + "=" * 60)
    print("Deep search in /prorcp/ page for video source")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
        
        prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
        
        # Save the full page for analysis
        with open("/home/ubuntu/prorcp_page.html", "w") as f:
            f.write(prorcp_resp.text)
        
        # Search for ALL potential video URLs
        # Look for base64-encoded URLs
        b64_pattern = re.findall(r'atob\([\'"]([A-Za-z0-9+/=]+)[\'"]\)', prorcp_resp.text)
        for b in b64_pattern[:10]:
            try:
                decoded = base64.b64decode(b).decode('utf-8')
                print(f"  atob decoded: {decoded[:80]}")
            except:
                pass
        
        # Look for the main player initialization
        init_match = re.search(r'new\s+Playerjs\(([^)]+)\)', prorcp_resp.text)
        if init_match:
            print(f"\nPlayerJS init: {init_match.group()[:200]}")
        
        # Look for source loading
        source_match = re.search(r'player[^a-z_]*\.set[^;]*;|player[^a-z_]*\.load[^;]*;|\.src\s*=\s*["\']', prorcp_resp.text)
        if source_match:
            print(f"Source loading: {source_match.group()[:100]}")
        
        # Look for the pjs driver script content
        driver_match = re.search(r'src=["\'](/pjs/pjs_main_drv_cast\.[^"\']+)', prorcp_resp.text)
        if driver_match:
            driver_path = driver_match.group(1)
            driver_url = f"https://cloudorchestranova.com{driver_path}"
            driver_resp = await client.get(driver_url, headers={**headers, "Referer": prorcp_full})
            with open("/home/ubuntu/driver.js", "w") as f:
                f.write(driver_resp.text)
            print(f"\nDriver script saved ({len(driver_resp.text)} bytes)")
            
            # Look for URL patterns in driver
            driver_urls = re.findall(r'https?://[^\s"\'>\)\.]+', driver_resp.text)
            for u in set(driver_urls)[:20]:
                if any(x in u for x in ['m3u8', 'stream', 'video', 'play', 'cdn', 'file']):
                    print(f"  Driver URL: {u[:80]}")
        
        # Look for the obfuscated scripts
        obfuscated = re.findall(r'src=["\'](/sV05[a-z]+/[^"\']+)', prorcp_resp.text)
        for o in obfuscated:
            print(f"  Obfuscated: {o[:60]}")
        
        # Look for the reporting.js which might have the source loading logic
        reporting_match = re.search(r'src=["\'](/reporting\.js\?t=[^"\']+)', prorcp_resp.text)
        if reporting_match:
            rep_path = reporting_match.group(1)
            rep_url = f"https://cloudorchestranova.com{rep_path}"
            rep_resp = await client.get(rep_url, headers={**headers, "Referer": prorcp_full})
            with open("/home/ubuntu/reporting.js", "w") as f:
                f.write(rep_resp.text)
            print(f"\nReporting script saved ({len(rep_resp.text)} bytes)")
            
            # Look for URL patterns
            rep_urls = re.findall(r'https?://[^\s"\'>\)\.]+', rep_resp.text)
            for u in set(rep_urls)[:20]:
                if any(x in u for x in ['m3u8', 'stream', 'video', 'play', 'cdn', 'file', 'api']):
                    print(f"  Reporting URL: {u[:80]}")

async def main():
    await test_nestra()
    await test_nestra_prorcp_page()

if __name__ == "__main__":
    asyncio.run(main())
