"""
Test: Extract from RCP page - now we know the pattern:
- div#hidden has data-h attribute
- body has data-i attribute (seed)
- XOR decrypt data-h with data-i to get the source URL
"""
import asyncio
import httpx
import re
import base64
from bs4 import BeautifulSoup
from urllib.parse import unquote

VIDSRC_KEY = "WXrUARXb1aDLaZjI"

async def xor_decrypt(encoded_hex: str, seed: str) -> str:
    encoded_buffer = bytes.fromhex(encoded_hex)
    decoded = ""
    for i in range(len(encoded_buffer)):
        decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
    if decoded.startswith("//"):
        decoded = f"https:{decoded}"
    return decoded


async def test_vidsrcme_full():
    """
    Full VidSrc.me extraction:
    1. Fetch embed -> get iframe (cloudorchestranova.com/rcp/...)
    2. Fetch RCP -> get data-h (from div#hidden) and data-i (from body)
    3. XOR decrypt data-h with data-i -> source URL
    4. Follow redirect -> decode -> M3u8
    """
    print("=" * 60)
    print("VidSrc.me Full Extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get embed page
        print("\n1. Fetching embed page...")
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        print(f"   RCP URL: {rcp_url[:80]}...")
        
        # Step 2: Fetch RCP page
        print("\n2. Fetching RCP page...")
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        rcp_soup = BeautifulSoup(rcp_resp.text, "html.parser")
        
        hidden = rcp_soup.find("div", {"id": "hidden"})
        body = rcp_soup.find("body")
        
        data_h = hidden.get("data-h") if hidden else None
        data_i = body.get("data-i") if body else None
        
        print(f"   data-h: {str(data_h)[:50]}...")
        print(f"   data-i: {data_i}")
        
        if not data_h or not data_i:
            print("   FAIL: Missing data-h or data-i")
            return False
        
        # Step 3: XOR decrypt
        print("\n3. XOR decrypting...")
        decoded_url = await xor_decrypt(data_h, data_i)
        print(f"   Decoded URL: {decoded_url}")
        
        # Step 4: Follow redirect
        print("\n4. Following redirect...")
        source_resp = await client.get(
            decoded_url,
            headers={**headers, "Referer": rcp_url},
            follow_redirects=True
        )
        
        print(f"   Final URL: {source_resp.url}")
        print(f"   Body length: {len(source_resp.text)}")
        
        # Step 5: Look for M3u8 or decode further
        if "vidsrc.stream" in str(source_resp.url):
            # VidSrc PRO pattern - find and decode the encrypted file
            print("\n5. VidSrc PRO pattern detected")
            for attempt in range(20):
                match = re.search(r'file:"([^"]*)"', source_resp.text)
                if not match:
                    break
                hls_url = match.group(1)
                print(f"   Attempt {attempt+1}: raw file={hls_url[:80]}")
                
                # Clean up the encrypted URL
                hls_url = re.sub(r'\/\/\S+?=', '', hls_url)[2:]
                hls_url = re.sub(r"/@#@/[^=\/]+==", "", hls_url)
                hls_url = hls_url.replace('_', '/').replace('-', '+')
                
                try:
                    decoded_m3u8 = bytearray(base64.b64decode(hls_url))
                    decoded_m3u8 = decoded_m3u8.decode('utf-8')
                except Exception as e:
                    print(f"   Decode error: {e}")
                    break
                
                print(f"   Attempt {attempt+1}: decoded={decoded_m3u8[:80]}")
                
                if decoded_m3u8.endswith('.m3u8'):
                    print(f"\n6. SUCCESS! M3u8: {decoded_m3u8}")
                    # Verify it works
                    test_resp = await client.head(decoded_m3u8, headers=headers)
                    print(f"   Accessible: {test_resp.status_code}")
                    return True
        
        # Check for direct M3u8
        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', source_resp.text)
        if m3u8_urls:
            print(f"\n5. Found M3u8 URLs: {m3u8_urls[:3]}")
            return True
        
        # Check for iframe or embed
        embed_soup = BeautifulSoup(source_resp.text, "html.parser")
        embed_iframes = embed_soup.find_all("iframe")
        if embed_iframes:
            print(f"\n5. Found iframes: {len(embed_iframes)}")
            for iframe in embed_iframes[:3]:
                print(f"   - {iframe.get('src', '')[:80]}")
            return True
        
        # Print response body for debugging
        print(f"\n5. Response body:\n{source_resp.text[:1000]}")
        return False


async def test_vidsrcto_full():
    """
    VidSrc.to -> just proxies to vsembed.ru
    1. Fetch embed -> extract iframe src
    2. Fetch iframe -> look for stream
    """
    print("\n" + "=" * 60)
    print("VidSrc.to Full Extraction")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get embed page
        print("\n1. Fetching embed page...")
        resp = await client.get("https://vidsrc.to/embed/movie/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        
        if not iframe:
            print("   FAIL: No iframe found")
            return False
        
        embed_src = iframe.get("src", "")
        print(f"   Iframe: {embed_src}")
        
        # Step 2: Fetch embed source
        print("\n2. Fetching embed source...")
        embed_resp = await client.get(embed_src, headers={**headers, "Referer": "https://vidsrc.to/"})
        print(f"   Status: {embed_resp.status_code}")
        print(f"   Final URL: {embed_resp.url}")
        print(f"   Body length: {len(embed_resp.text)}")
        
        # Look for iframes in the embed
        embed_soup = BeautifulSoup(embed_resp.text, "html.parser")
        
        # Check for vsembed pattern
        if "vsembed" in str(embed_resp.url):
            print("\n3. vsembed pattern detected")
            # vsembed uses the same RCP pattern
            vsembed_iframe = embed_soup.find("iframe")
            if vsembed_iframe:
                vsembed_src = vsembed_iframe.get("src", "")
                if vsembed_src.startswith("//"):
                    vsembed_src = f"https:{vsembed_src}"
                print(f"   vsembed iframe: {vsembed_src[:80]}...")
                
                # Fetch the vsembed RCP page
                print("\n4. Fetching vsembed RCP...")
                rcp_resp = await client.get(vsembed_src, headers={**headers, "Referer": "https://vsembed.ru/"})
                rcp_soup = BeautifulSoup(rcp_resp.text, "html.parser")
                
                hidden = rcp_soup.find("div", {"id": "hidden"})
                body = rcp_soup.find("body")
                
                if hidden and body:
                    data_h = hidden.get("data-h")
                    data_i = body.get("data-i")
                    print(f"   data-h: {str(data_h)[:50]}...")
                    print(f"   data-i: {data_i}")
                    
                    if data_h and data_i:
                        print("\n5. XOR decrypting...")
                        decoded_url = await xor_decrypt(data_h, data_i)
                        print(f"   Decoded: {decoded_url}")
                        
                        # Follow redirect
                        print("\n6. Following redirect...")
                        source_resp = await client.get(
                            decoded_url,
                            headers={**headers, "Referer": vsembed_src},
                            follow_redirects=True
                        )
                        print(f"   Final URL: {source_resp.url}")
                        
                        # Look for M3u8
                        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', source_resp.text)
                        if m3u8_urls:
                            print(f"\n7. SUCCESS! M3u8: {m3u8_urls[0][:80]}")
                            return True
                        
                        # Try iframe chain
                        src_soup = BeautifulSoup(source_resp.text, "html.parser")
                        src_iframes = src_soup.find_all("iframe")
                        if src_iframes:
                            print(f"\n7. Found {len(src_iframes)} iframes, following first...")
                            for iframe in src_iframes[:3]:
                                src = iframe.get("src", "")
                                if src.startswith("//"):
                                    src = f"https:{src}"
                                print(f"   Following: {src[:80]}...")
                                src_resp = await client.get(src, headers={**headers, "Referer": str(source_resp.url)})
                                src_m3u8 = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', src_resp.text)
                                if src_m3u8:
                                    print(f"\n8. SUCCESS! M3u8: {src_m3u8[0][:80]}")
                                    return True
            else:
                # No iframe, look for scripts with M3u8
                scripts = embed_soup.find_all("script")
                for sc in scripts[:5]:
                    text = sc.text[:200] if sc.text else ""
                    if text and ("m3u8" in text.lower() or "file" in text.lower() or "player" in text.lower()):
                        print(f"   Script: {text[:100]}")
        
        return False


async def main():
    ok1 = await test_vidsrcme_full()
    ok2 = await test_vidsrcto_full()
    
    print("\n" + "=" * 60)
    print(f"VidSrc.me: {'PASS' if ok1 else 'FAIL'}")
    print(f"VidSrc.to: {'PASS' if ok2 else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
