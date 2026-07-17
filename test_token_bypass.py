"""
Test M3u8 URLs with correct Referer and Origin headers.
The 401 error is likely due to missing Referer or Origin headers.
The player on cloudorchestranova.com uses these headers to authorize the stream.
"""
import asyncio
import httpx
import re
from bs4 import BeautifulSoup

async def test_headers_bypass():
    print("=" * 60)
    print("Test: M3u8 Header Bypass (Referer/Origin)")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get the /prorcp/ page to get the URLs and the current context
        print("1. Fetching /prorcp/ page...")
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
        
        # Extract M3u8 URLs
        all_m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.(?:m3u8|m3u)[^\s"\'\)\]>\n]*', prorcp_resp.text)
        if not all_m3u8:
            print("   No M3u8 found")
            return
        
        target_url = all_m3u8[0].replace('?token=__TOKEN__', '').replace('?token=__TOKENPG__', '')
        print(f"\n2. Testing Target: {target_url[:80]}...")
        
        # Try different header combinations
        test_cases = [
            {"label": "No Referer", "headers": {}},
            {"label": "Referer: vidsrc.me", "headers": {"Referer": "https://vidsrc.me/"}},
            {"label": "Referer: cloudorchestranova.com", "headers": {"Referer": "https://cloudorchestranova.com/"}},
            {"label": "Referer: prorcp page", "headers": {"Referer": prorcp_full}},
            {"label": "Origin: cloudorchestranova.com", "headers": {"Origin": "https://cloudorchestranova.com"}},
            {"label": "Full Headers (Origin + Referer)", "headers": {
                "Origin": "https://cloudorchestranova.com",
                "Referer": "https://cloudorchestranova.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site"
            }},
        ]
        
        for case in test_cases:
            print(f"\n   Case: {case['label']}")
            try:
                # Use a new client for each case to avoid cookie interference
                async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as c:
                    h = {**headers, **case['headers']}
                    resp = await c.get(target_url, headers=h)
                    print(f"     Status: {resp.status_code}")
                    if resp.status_code == 200:
                        print(f"     SUCCESS! Content length: {len(resp.text)}")
                        print(f"     Preview: {resp.text[:100]}")
                        return True
            except Exception as e:
                print(f"     Error: {e}")
        
        # Step 3: Look for the token generation in the page
        print("\n3. Searching for token generation logic...")
        # Search for 'token' in scripts
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', prorcp_resp.text, re.DOTALL)
        for i, script in enumerate(scripts):
            if 'token' in script.lower():
                print(f"   Script {i} contains 'token'")
                # Look for assignment
                token_match = re.search(r'token\s*=\s*["\']([^"\']+)["\']', script)
                if token_match:
                    print(f"     Found token assignment: {token_match.group(1)}")
                
                # Look for dynamic generation
                if 'fetch' in script or 'XMLHttpRequest' in script:
                    print(f"     Script {i} has network requests for token")
        
        # Look for the 'reporting.js' which often handles tokens
        print("\n4. Checking reporting.js for token logic...")
        rep_match = re.search(r'src=["\'](/reporting\.js\?t=[^"\']+)["\']', prorcp_resp.text)
        if rep_match:
            rep_url = f"https://cloudorchestranova.com{rep_match.group(1)}"
            rep_resp = await client.get(rep_url, headers={**headers, "Referer": prorcp_full})
            if 'token' in rep_resp.text.lower():
                print("   reporting.js contains 'token' logic")
                # Look for token generation patterns
                # Often it's an AJAX call to /pass_md5.php or similar
        
        # Check for pass_md5.php or similar endpoints
        pass_match = re.search(r'["\'](/[^"\']+\.php[^"\']*)["\']', prorcp_resp.text)
        if pass_match:
            print(f"\n5. Found PHP endpoint: {pass_match.group(1)}")

async def main():
    await test_headers_bypass()

if __name__ == "__main__":
    asyncio.run(main())
