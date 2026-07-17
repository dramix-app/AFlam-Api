"""
Debug: What does the cloudorchestranova.com RCP page actually contain?
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

async def test_rcp():
    # Use the exact iframe URL from the actual page
    # First get the iframe URL from vidsrcme.ru
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Get the embed page
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        print(f"RCP URL: {rcp_url}")
        
        # Fetch RCP page
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        print(f"\nRCP Status: {rcp_resp.status_code}")
        print(f"RCP Body length: {len(rcp_resp.text)}")
        print(f"RCP Final URL: {rcp_resp.url}")
        
        rcp_soup = BeautifulSoup(rcp_resp.text, "html.parser")
        
        # Print ALL elements
        print(f"\n--- ALL DIVS ---")
        for div in rcp_soup.find_all("div"):
            attrs = dict(div.attrs)
            print(f"  <div {attrs}>")
        
        print(f"\n--- ALL BODY ATTRS ---")
        body = rcp_soup.find("body")
        if body:
            print(f"  Body attrs: {dict(body.attrs)}")
        
        print(f"\n--- ALL SCRIPTS ---")
        for sc in rcp_soup.find_all("script"):
            src = sc.get("src", "")
            text = sc.text[:300] if sc.text else ""
            if src:
                print(f"  External: {src[:80]}")
            elif text:
                print(f"  Inline ({len(text)} chars): {text[:150]}")
        
        print(f"\n--- ALL IFRAMES ---")
        for iframe in rcp_soup.find_all("iframe"):
            print(f"  src: {iframe.get('src', '')[:100]}")
        
        # Check if the page is a redirect
        meta = rcp_soup.find("meta", {"http-equiv": "refresh"})
        if meta:
            print(f"\nMeta refresh: {meta.get('content')}")
        
        # Check for any location header
        print(f"\n--- HEADERS ---")
        for k, v in rcp_resp.headers.items():
            if "location" in k.lower() or "refresh" in k.lower():
                print(f"  {k}: {v[:100]}")

if __name__ == "__main__":
    asyncio.run(test_rcp())
