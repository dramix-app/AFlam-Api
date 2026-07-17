"""
Extract the actual M3u8 URLs from the /prorcp/ page and test them.
The URLs are in the master_urls variable, gzip-encoded in the URL path.
"""
import asyncio
import httpx
import re
import base64
import gzip
import io
from bs4 import BeautifulSoup

async def extract_and_test():
    print("=" * 60)
    print("Extract and Test M3u8 URLs from /prorcp/")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Step 1: Get embed -> RCP -> /prorcp/
        print("1. Fetching embed page...")
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        print(f"   RCP: {rcp_url[:80]}...")
        
        print("2. Fetching RCP page...")
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
        
        print(f"   PRO-RCP: {prorcp_full[:80]}...")
        
        print("3. Fetching /prorcp/ page...")
        prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
        
        # Step 2: Find the master_urls variable
        # The page has: new Playerjs({id:"player_parent", file: master_urls, ...})
        # We need to find where master_urls is defined
        print("4. Finding master_urls variable...")
        
        # Search for master_urls definition
        master_match = re.search(r'var\s+master_urls\s*=\s*\[([^\]]+)\]', prorcp_resp.text, re.DOTALL)
        if master_match:
            print(f"   Found master_urls array!")
            urls_str = master_match.group(1)
            print(f"   Content: {urls_str[:500]}")
            
            # Extract individual URLs
            url_matches = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', urls_str)
            print(f"   URLs found: {len(url_matches)}")
            for u in url_matches:
                print(f"     {u[:100]}")
        else:
            # Try different pattern
            master_match2 = re.search(r'master_urls\s*=\s*\[([^\]]+)\]', prorcp_resp.text, re.DOTALL)
            if master_match2:
                print(f"   Found master_urls (no var): {master_match2.group(1)[:300]}")
            else:
                # Look for any array with m3u8 URLs
                all_m3u8 = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', prorcp_resp.text)
                print(f"   Direct M3u8 strings in page: {len(all_m3u8)}")
                for u in all_m3u8[:5]:
                    print(f"     {u[:100]}")
        
        # Step 3: Extract all M3u8 URLs from the page
        print("\n5. Extracting ALL M3u8 URLs...")
        all_m3u8 = re.findall(r'https?://[^\s"\'\)\]>\n]+\.(?:m3u8|m3u)[^\s"\'\)\]>\n]*', prorcp_resp.text)
        print(f"   Found {len(all_m3u8)} M3u8 URLs:")
        for u in all_m3u8:
            print(f"     {u[:120]}")
        
        # Step 4: Also look at the inline scripts for URL patterns
        print("\n6. Searching inline scripts for URL variables...")
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', prorcp_resp.text, re.DOTALL)
        for i, script in enumerate(scripts):
            if not script:
                continue
            # Look for URL patterns
            urls_in_script = re.findall(r'["\'](https?://[^\s"\']+m3u8[^\s"\']*)["\']', script)
            if urls_in_script:
                print(f"   Script {i}: {len(urls_in_script)} M3u8 URLs")
                for u in urls_in_script[:3]:
                    print(f"     {u[:100]}")
            
            # Look for array definitions
            array_match = re.search(r'(?:var\s+)?(\w+_urls|urls|sources)\s*=\s*\[([^\]]+)\]', script, re.DOTALL)
            if array_match and 'm3u8' in array_match.group(2):
                print(f"   Script {i} has URL array: {array_match.group(1)}")
                print(f"     {array_match.group(2)[:200]}")
        
        # Step 5: Try to access the M3u8 URLs (without token first)
        print("\n7. Testing M3u8 URLs...")
        for u in all_m3u8[:3]:
            # Try without token
            test_url = u.replace('?token=__TOKEN__', '').replace('?token=__TOKENPG__', '')
            print(f"   Testing: {test_url[:80]}...")
            try:
                test_resp = await client.head(test_url, headers=headers, timeout=10)
                print(f"     Status: {test_resp.status_code}")
                if test_resp.status_code == 200:
                    print(f"     SUCCESS! M3u8 is accessible!")
                    # Try to get the content
                    content_resp = await client.get(test_url, headers=headers, timeout=10)
                    print(f"     Content: {content_resp.text[:200]}")
                else:
                    # Try with the full URL (with __TOKEN__)
                    test_resp2 = await client.head(u, headers=headers, timeout=10)
                    print(f"     With token: {test_resp2.status_code}")
            except Exception as e:
                print(f"     Error: {e}")
        
        return len(all_m3u8) > 0


async def extract_vidsrc_me_pattern():
    """
    Also test the VidSrc.me embed page for the master_urls pattern
    """
    print("\n" + "=" * 60)
    print("Test: VidSrc.me embed page master_urls pattern")
    print("=" * 60)
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # The embed page has the RCP iframe which loads /prorcp/
        # But the /prorcp/ is loaded via JavaScript when you click play
        # So we need to find the /prorcp/ URL directly from the RCP page
        
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        
        # Find the /prorcp/ URL
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        if prorcp_match:
            prorcp_path = prorcp_match.group(1)
            prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_path}"
            
            # Fetch it
            prorcp_resp = await client.get(prorcp_full, headers={**headers, "Referer": rcp_url})
            
            # Extract M3u8 URLs
            m3u8_urls = re.findall(r'https?://[^\s"\'\)\]>\n]+\.(?:m3u8|m3u)[^\s"\'\)\]>\n]*', prorcp_resp.text)
            
            # Clean up the URLs
            clean_urls = []
            for u in m3u8_urls:
                # Remove token placeholder
                u = u.replace('?token=__TOKEN__', '').replace('?token=__TOKENPG__', '')
                clean_urls.append(u)
            
            print(f"   M3u8 URLs from /prorcp/: {len(clean_urls)}")
            for u in clean_urls:
                print(f"     {u[:100]}")
            
            # Test them
            for u in clean_urls[:2]:
                try:
                    resp = await client.head(u, headers=headers, timeout=10)
                    print(f"     [{resp.status_code}] {u[:80]}")
                except Exception as e:
                    print(f"     [ERROR] {u[:60]}: {e}")
        
        # Also check vidsrcme.ru (the source provider)
        print("\n   Testing vidsrcme.ru directly...")
        try:
            vme_resp = await client.get("https://vidsrcme.ru/embed/238", headers=headers, timeout=10)
            print(f"     Status: {vme_resp.status_code}")
            # Check for iframe
            vme_soup = BeautifulSoup(vme_resp.text, "html.parser")
            vme_iframe = vme_soup.find("iframe")
            if vme_iframe:
                print(f"     Iframe: {vme_iframe.get('src', '')[:80]}")
            # Check for M3u8
            vme_m3u8 = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', vme_resp.text)
            if vme_m3u8:
                print(f"     M3u8 in vidsrcme.ru: {vme_m3u8}")
        except Exception as e:
            print(f"     Error: {e}")


async def main():
    ok1 = await extract_and_test()
    await extract_vidsrc_me_pattern()

if __name__ == "__main__":
    asyncio.run(main())
