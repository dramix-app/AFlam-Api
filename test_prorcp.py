"""
Test the NEW /prorcp/ endpoint pattern from cloudorchestranova.com
The inline script shows: src: '/prorcp/OWNkN2U4ZDY4NjQ5ODc2MTVkMTQ1YmM5NjQ2YTdlZmM6TV...'
This is the new RCP endpoint that should have the data-h/data-i XOR pattern.
"""
import asyncio
import httpx
import re
import base64
from bs4 import BeautifulSoup

VIDSRC_KEY = "WXrUARXb1aDLaZjI"

async def xor_decrypt(encoded_hex: str, seed: str) -> str:
    encoded_buffer = bytes.fromhex(encoded_hex)
    decoded = ""
    for i in range(len(encoded_buffer)):
        decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
    if decoded.startswith("//"):
        decoded = f"https:{decoded}"
    return decoded


async def test_prorcp():
    print("=" * 60)
    print("Test: /prorcp/ endpoint (NEW RCP pattern)")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get the embed page
        print("\n1. Fetching embed page...")
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        # Extract the prorcp URL from the inline script
        print(f"   RCP URL: {rcp_url[:80]}...")
        
        # Find the prorcp URL in the inline script
        prorcp_match = re.search(r"src:\s*['\"](/prorcp/[A-Za-z0-9+/=]+)['\"]", resp.text)
        if not prorcp_match:
            # Try the RCP page itself
            rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
            prorcp_match = re.search(r"src:\s*['\"](/prorcp/[A-Za-z0-9+/=]+)['\"]", rcp_resp.text)
            print(f"   Looking in RCP page...")
        
        if prorcp_match:
            prorcp_path = prorcp_match.group(1)
            prorcp_full = f"https://cloudorchestranova.com{prorcp_path}"
            print(f"\n2. Found /prorcp/ path: {prorcp_path[:80]}...")
        else:
            print("   No /prorcp/ found in inline script")
            # Try to find it from the RCP page
            print("   Let's look at the RCP page more carefully...")
            rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
            
            # Search for prorcp in the entire RCP page
            prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
            if prorcp_match:
                prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
                print(f"   Found in RCP: {prorcp_full[:80]}...")
            else:
                print("   No /prorcp/ found at all")
                # Print the inline script
                scripts = soup.find_all("script")
                for sc in scripts:
                    if sc.text and "prorcp" in sc.text:
                        print(f"\n   Script with prorcp ({len(sc.text)} chars):")
                        idx = sc.text.index("prorcp")
                        print(f"   {sc.text[max(0,idx-50):idx+200]}")
                return False
        
        # Step 2: Fetch the /prorcp/ endpoint
        print(f"\n3. Fetching /prorcp/ endpoint...")
        prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
        print(f"   Status: {prorcp_resp.status_code}")
        print(f"   Body length: {len(prorcp_resp.text)}")
        
        prorcp_soup = BeautifulSoup(prorcp_resp.text, "html.parser")
        
        # Look for hidden div and data-h
        hidden = prorcp_soup.find("div", {"id": "hidden"})
        body = prorcp_soup.find("body")
        
        print(f"\n4. Checking /prorcp/ response:")
        print(f"   hidden div: {hidden is not None}")
        if hidden:
            print(f"   hidden attrs: {hidden.attrs}")
        print(f"   body: {body is not None}")
        if body:
            print(f"   body data-i: {body.get('data-i', 'NONE')}")
        
        if hidden and body:
            data_h = hidden.get("data-h")
            data_i = body.get("data-i")
            print(f"   data-h: {str(data_h)[:50]}...")
            print(f"   data-i: {data_i}")
            
            if data_h and data_i:
                # XOR decrypt
                print("\n5. XOR decrypting...")
                decoded_url = await xor_decrypt(data_h, data_i)
                print(f"   Decoded URL: {decoded_url}")
                
                # Follow redirect
                print("\n6. Following redirect...")
                source_resp = await client.get(
                    decoded_url,
                    headers={**headers, "Referer": prorcp_full},
                    follow_redirects=True
                )
                print(f"   Final URL: {source_resp.url}")
                
                # Look for M3u8
                m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', source_resp.text)
                if m3u8_urls:
                    print(f"\n7. SUCCESS! M3u8: {m3u8_urls[0][:100]}")
                    return True
                
                # Try the vidsrc.stream pattern
                if "vidsrc.stream" in str(source_resp.url):
                    for attempt in range(20):
                        match = re.search(r'file:"([^"]*)"', source_resp.text)
                        if not match:
                            break
                        hls_url = match.group(1)
                        hls_url = re.sub(r'\/\/\S+?=', '', hls_url)[2:]
                        hls_url = re.sub(r"/@#@/[^=\/]+==", "", hls_url)
                        hls_url = hls_url.replace('_', '/').replace('-', '+')
                        try:
                            decoded = bytearray(base64.b64decode(hls_url)).decode('utf-8')
                        except:
                            break
                        if decoded.endswith('.m3u8'):
                            print(f"\n7. SUCCESS! M3u8: {decoded}")
                            return True
                        print(f"   Attempt {attempt+1}: {decoded[:60]}")
                
                # Print body for debugging
                print(f"\n   Body preview: {source_resp.text[:1000]}")
                return False
        
        # Print the /prorcp/ page body for debugging
        print(f"\n   /prorcp/ page body:\n{prorcp_resp.text[:2000]}")
        return False


async def test_vsembed_prorcp():
    """Test vsembed.ru which also uses the same RCP pattern"""
    print("\n" + "=" * 60)
    print("Test: vsembed.ru /prorcp/ endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Fetch vsembed
        print("\n1. Fetching vsembed.ru...")
        resp = await client.get("https://vsembed.ru/embed/movie/238/", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find iframe
        iframe = soup.find("iframe")
        if iframe:
            rcp_src = iframe.get("src", "")
            if rcp_src.startswith("//"):
                rcp_src = f"https:{rcp_src}"
            print(f"   iframe: {rcp_src[:80]}...")
        else:
            # Look for prorcp in the page
            prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', resp.text)
            if prorcp_match:
                prorcp_path = prorcp_match.group(1)
                prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_path}"
                print(f"   Found /prorcp/ in page: {prorcp_path[:80]}...")
                
                # Fetch /prorcp/
                print(f"\n2. Fetching /prorcp/...")
                prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": "https://vsembed.ru/"})
                prorcp_soup = BeautifulSoup(prorcp_resp.text, "html.parser")
                
                hidden = prorcp_soup.find("div", {"id": "hidden"})
                body = prorcp_soup.find("body")
                
                if hidden and body:
                    data_h = hidden.get("data-h")
                    data_i = body.get("data-i")
                    print(f"   data-h: {str(data_h)[:50]}...")
                    print(f"   data-i: {data_i}")
                    
                    if data_h and data_i:
                        decoded_url = await xor_decrypt(data_h, data_i)
                        print(f"   Decoded: {decoded_url}")
                        
                        source_resp = await client.get(
                            decoded_url,
                            headers={**headers, "Referer": prorcp_full},
                            follow_redirects=True
                        )
                        print(f"   Final URL: {source_resp.url}")
                        
                        m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', source_resp.text)
                        if m3u8_urls:
                            print(f"\n3. SUCCESS! M3u8: {m3u8_urls[0][:80]}")
                            return True
                        print(f"   Body: {source_resp.text[:500]}")
            else:
                print("   No iframe and no /prorcp/ found")
        
        return False


async def main():
    ok1 = await test_prorcp()
    ok2 = await test_vsembed_prorcp()
    
    print("\n" + "=" * 60)
    print(f"VidSrc.me /prorcp/: {'PASS' if ok1 else 'FAIL'}")
    print(f"VidSrc (vsembed) /prorcp/: {'PASS' if ok2 else 'FAIL'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
