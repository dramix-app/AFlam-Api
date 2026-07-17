"""
Test: Extract M3u8 from cloudorchestranova.com RCP iframe
This is the key pattern for VidSrc.me in 2025-2026.
The iframe src is found in the vidsrcme.ru page, then we use the RCP XOR decode pattern.
"""
import asyncio
import httpx
import re
import base64
from bs4 import BeautifulSoup
from urllib.parse import unquote

VIDSRC_KEY = "WXrUARXb1aDLaZjI"

async def rc4_decrypt(encrypted: str, key: str) -> str:
    standardized = encrypted.replace('_', '/').replace('-', '+')
    binary_data = base64.b64decode(standardized)
    encoded = bytearray(binary_data)
    key_bytes = bytes(key, 'utf-8')
    j = 0
    s = bytearray(range(256))
    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
        s[i], s[j] = s[j], s[i]
    decoded = bytearray(len(encoded))
    i = 0
    k = 0
    for index in range(len(encoded)):
        i = (i + 1) & 0xff
        k = (k + s[i]) & 0xff
        s[i], s[k] = s[k], s[i]
        t = (s[i] + s[k]) & 0xff
        decoded[index] = encoded[index] ^ s[t]
    return unquote(decoded.decode('utf-8'))


async def xor_decrypt(encoded_hex: str, seed: str) -> str:
    encoded_buffer = bytes.fromhex(encoded_hex)
    decoded = ""
    for i in range(len(encoded_buffer)):
        decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
    if decoded.startswith("//"):
        decoded = f"https:{decoded}"
    return decoded


async def test_vidsrcme_extraction():
    """
    Full extraction from VidSrc.me:
    1. Fetch embed page
    2. Find iframe src (cloudorchestranova.com/rcp/...)
    3. Fetch RCP page -> get data-h and data-i
    4. XOR decrypt -> get source URL
    5. Follow redirect -> get M3u8
    """
    print("=" * 60)
    print("VidSrc.me Full Extraction (cloudorchestranova.com RCP)")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidsrc.me/embed/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Fetch embed page
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        print(f"   Final URL: {resp.url}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Step 2: Find iframe
        iframe = soup.find("iframe")
        if not iframe:
            print("   ERROR: No iframe found!")
            return False
        
        rcp_src = iframe.get("src", "")
        if rcp_src.startswith("//"):
            rcp_src = f"https:{rcp_src}"
        print(f"\n2. Found iframe: {rcp_src[:80]}...")
        
        # Step 3: Fetch RCP page
        print(f"\n3. Fetching RCP page...")
        rcp_resp = await client.get(rcp_src, headers={**headers, "Referer": str(resp.url)})
        print(f"   Status: {rcp_resp.status_code}")
        print(f"   Body length: {len(rcp_resp.text)}")
        
        rcp_soup = BeautifulSoup(rcp_resp.text, "html.parser")
        
        # Get data-h and data-i
        hidden = rcp_soup.find("div", {"id": "hidden"})
        body = rcp_soup.find("body")
        
        if not hidden or not body:
            print("   ERROR: No hidden div or body with data-i")
            print(f"   Page HTML: {rcp_resp.text[:1000]}")
            return False
        
        data_h = hidden.get("data-h")
        data_i = body.get("data-i")
        
        print(f"\n4. Data-h: {data_h[:50]}...")
        print(f"   Data-i (seed): {data_i[:30]}...")
        
        if not data_h or not data_i:
            print("   ERROR: Missing data-h or data-i")
            return False
        
        # Step 4: XOR decrypt
        print(f"\n5. XOR decrypting...")
        decoded_url = await xor_decrypt(data_h, data_i)
        print(f"   Decoded URL: {decoded_url}")
        
        # Step 5: Follow redirect
        print(f"\n6. Following source URL...")
        source_resp = await client.get(
            decoded_url,
            headers={**headers, "Referer": rcp_src},
            follow_redirects=False
        )
        
        location = source_resp.headers.get("location")
        print(f"   Redirect location: {location}")
        
        if not location:
            print(f"   Response body: {source_resp.text[:500]}")
            return False
        
        # Step 6: Fetch the final source
        print(f"\n7. Fetching final source...")
        final_resp = await client.get(location, headers={**headers, "Referer": location.split('/')[2]})
        print(f"   Status: {final_resp.status_code}")
        print(f"   Body length: {len(final_resp.text)}")
        
        # Look for M3u8
        if "vidsrc.stream" in location:
            # VidSrc PRO - need to extract and decode
            for attempt in range(10):
                match = re.search(r'file:"([^"]*)"', final_resp.text)
                if not match:
                    break
                hls_url = match.group(1)
                # Clean up
                hls_url = re.sub(r'\/\/\S+?=', '', hls_url)[2:]
                hls_url = re.sub(r"/@#@/[^=\/]+==", "", hls_url)
                hls_url = hls_url.replace('_', '/').replace('-', '+')
                try:
                    hls_url = bytearray(base64.b64decode(hls_url))
                    hls_url = hls_url.decode('utf-8')
                except Exception as e:
                    print(f"   Base64 decode error: {e}")
                    break
                if hls_url.endswith('.m3u8'):
                    print(f"\n8. SUCCESS! M3u8 URL: {hls_url[:100]}")
                    # Test the URL
                    test_resp = await client.head(hls_url, headers=headers)
                    print(f"   URL accessible: {test_resp.status_code}")
                    return True
                print(f"   Attempt {attempt+1}: decoded to {hls_url[:60]}")
        
        elif "multiembed.mov" in location:
            # SuperEmbed - need Hunter decode
            print(f"\n8. SuperEmbed source detected")
            match = re.search(r"eval\(function\(h,u,n,t,e,r\).*?}\((.*?)\)\)", final_resp.text)
            if match:
                print(f"   Found Hunter-coded JS")
                # Print first 200 chars
                print(f"   Content: {final_resp.text[:500]}")
            return False
        
        else:
            # Direct URL
            print(f"\n8. Direct source: {location[:100]}")
            return location.endswith('.m3u8')
    
    return False


async def test_vidsrcto_extraction():
    """
    Full extraction from VidSrc.to:
    1. Fetch embed page
    2. Extract iframe src (vsembed.ru)
    3. Fetch vsembed.ru and extract stream
    """
    print("\n" + "=" * 60)
    print("VidSrc.to Extraction (vsembed.ru proxy)")
    print("=" * 60)
    
    tmdb_id = "238"
    url = f"https://vidsrc.to/embed/movie/{tmdb_id}"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Fetch embed page
        print(f"\n1. Fetching: {url}")
        resp = await client.get(url, headers=headers)
        print(f"   Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Step 2: Find iframe
        iframe = soup.find("iframe")
        if not iframe:
            print("   ERROR: No iframe found!")
            return False
        
        embed_src = iframe.get("src", "")
        print(f"\n2. Found iframe: {embed_src}")
        
        # Step 3: Fetch the embed source
        print(f"\n3. Fetching embed source...")
        embed_resp = await client.get(embed_src, headers={**headers, "Referer": "https://vidsrc.to/"})
        print(f"   Status: {embed_resp.status_code}")
        print(f"   Body length: {len(embed_resp.text)}")
        print(f"   Final URL: {embed_resp.url}")
        
        # Look for M3u8
        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', embed_resp.text)
        print(f"\n4. Found {len(m3u8_urls)} M3u8 URLs:")
        for m in m3u8_urls[:5]:
            print(f"   - {m[:80]}")
        
        # Look for iframes
        embed_soup = BeautifulSoup(embed_resp.text, "html.parser")
        embed_iframes = embed_soup.find_all("iframe")
        print(f"\n5. Found {len(embed_iframes)} iframes in embed page:")
        for iframe in embed_iframes[:5]:
            print(f"   - {iframe.get('src', '')[:80]}")
        
        # Look for scripts with data
        scripts = embed_soup.find_all("script")
        for sc in scripts[:5]:
            text = sc.text[:200] if sc.text else ""
            if "m3u8" in text.lower() or "player" in text.lower() or "src" in text.lower():
                print(f"\n   Script: {text[:100]}")
        
        return len(m3u8_urls) > 0 or len(embed_iframes) > 0


async def main():
    print("=" * 60)
    print("AFlam-Api V3 - New Extraction Pattern Test")
    print("=" * 60)
    
    ok1 = await test_vidsrcme_extraction()
    ok2 = await test_vidsrcto_extraction()
    
    print("\n" + "=" * 60)
    print(f"VidSrc.me (RCP/XOR): {'PASS' if ok1 else 'FAIL'}")
    print(f"VidSrc.to (vsembed): {'PASS' if ok2 else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
