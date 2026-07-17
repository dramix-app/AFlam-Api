"""
Debug: The div#hidden has data-h but BeautifulSoup isn't finding it.
Let's look at the raw HTML of the hidden div.
"""
import asyncio
import httpx
import re
from bs4 import BeautifulSoup

async def test_hidden_div():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Get RCP page
        rcp_url = "https://cloudorchestranova.com/rcp/MWM5OTFmNTcwZWFiZjE4MGVkMjYxMDkwMTE0NjU5Yjk6U..."
        
        # Better: get it fresh from vidsrcme
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        
        # Look at the raw HTML around "hidden"
        html = rcp_resp.text
        
        # Find the hidden div in raw HTML
        hidden_match = re.search(r'<div[^>]*id=["\']hidden["\'][^>]*>', html, re.IGNORECASE)
        if hidden_match:
            print(f"Found hidden div in raw HTML:")
            print(f"  {hidden_match.group()}")
        else:
            print("No hidden div found in raw HTML")
        
        # Try with different BeautifulSoup parser
        soup2 = BeautifulSoup(html, "html.parser")
        hidden = soup2.find("div", id="hidden")
        print(f"\nBeautifulSoup html.parser - hidden: {hidden}")
        if hidden:
            print(f"  attrs: {hidden.attrs}")
        
        # Try lxml parser if available
        soup3 = BeautifulSoup(html, "lxml")
        hidden3 = soup3.find("div", id="hidden")
        print(f"\nBeautifulSoup lxml - hidden: {hidden3}")
        if hidden3:
            print(f"  attrs: {hidden3.attrs}")
        
        # Print the entire body section
        body_start = html.find("<body")
        body_end = html.find("</body>")
        if body_start >= 0 and body_end >= 0:
            body_html = html[body_start:body_end + 7]
            print(f"\n--- BODY HTML (first 3000 chars) ---")
            print(body_html[:3000])
        
        # Search for data-h in raw HTML
        data_h_match = re.search(r'data-h=["\']([^"\']+)["\']', html)
        if data_h_match:
            print(f"\nFound data-h in raw HTML: {data_h_match.group(1)[:50]}...")
        else:
            print("\nNo data-h found in raw HTML")
        
        # Search for data-i
        data_i_match = re.search(r'data-i=["\']([^"\']+)["\']', html)
        if data_i_match:
            print(f"Found data-i in raw HTML: {data_i_match.group(1)[:30]}")


async def test_sb_pattern():
    """
    The RCP page has sbx.js - this is the script that does the XOR decode.
    Let's look at what sbx.js does and find the data-h pattern.
    """
    print("\n" + "=" * 60)
    print("Debug: sbx.js pattern")
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
        
        # Find sbx.js in the page
        sbx_match = re.search(r'src=["\'](/sbx\.js\?t=[^"\']+)["\']', rcp_resp.text)
        if sbx_match:
            sbx_url = sbx_match.group(1)
            if not sbx_url.startswith("http"):
                sbx_url = f"https://cloudorchestranova.com{sbx_url}"
            print(f"\nFetching sbx.js: {sbx_url}")
            sbx_resp = await client.get(sbx_url, headers={**headers, "Referer": rcp_url})
            print(f"Status: {sbx_resp.status_code}")
            print(f"Content:\n{sbx_resp.text[:2000]}")
        
        # Also find base64.js
        b64_match = re.search(r'src=["\'](/base64\.js\?t=[^"\']+)["\']', rcp_resp.text)
        if b64_match:
            b64_url = b64_match.group(1)
            if not b64_url.startswith("http"):
                b64_url = f"https://cloudorchestranova.com{b64_url}"
            print(f"\nFetching base64.js: {b64_url}")
            b64_resp = await client.get(b64_url, headers={**headers, "Referer": rcp_url})
            print(f"Status: {b64_resp.status_code}")
            print(f"Content:\n{b64_resp.text[:500]}")
        
        # The actual page HTML - look for the hidden div more carefully
        print("\n--- Full page HTML (looking for hidden div) ---")
        # Find div with id hidden
        for match in re.finditer(r'<div[^>]*>', rcp_resp.text):
            tag = match.group()
            if "hidden" in tag.lower():
                print(f"Found div: {tag}")


async def main():
    await test_hidden_div()
    await test_sb_pattern()

if __name__ == "__main__":
    asyncio.run(main())
