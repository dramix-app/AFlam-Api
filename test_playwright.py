"""
Test: Use Playwright to extract M3u8 from the /prorcp/ player page
This is the reliable approach - load the page, click play, intercept network requests.
"""
import asyncio
import re
import sys
import time

async def test_playwright_extraction():
    """Use Playwright to load the /prorcp/ page and intercept M3u8 requests"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        from playwright.async_api import async_playwright
    
    print("=" * 60)
    print("Playwright M3u8 Extraction Test")
    print("=" * 60)
    
    # First, get the /prorcp/ URL
    import httpx
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        resp = await client.get("https://vidsrc.me/embed/238", headers=headers)
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        iframe = soup.find("iframe")
        rcp_url = iframe.get("src", "")
        if rcp_url.startswith("//"):
            rcp_url = f"https:{rcp_url}"
        
        rcp_resp = await client.get(rcp_url, headers={**headers, "Referer": "https://vidsrc.me/"})
        prorcp_match = re.search(r'/prorcp/([A-Za-z0-9+/=]+)', rcp_resp.text)
        
        if not prorcp_match:
            print("ERROR: No /prorcp/ found")
            return False
        
        prorcp_full = f"https://cloudorchestranova.com/prorcp/{prorcp_match.group(1)}"
        print(f"\n1. Target URL: {prorcp_full[:80]}...")
    
    # Now use Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        
        # Collect all M3u8 URLs
        m3u8_urls = []
        video_requests = []
        
        async def handle_request(request):
            url = request.url
            if '.m3u8' in url:
                m3u8_urls.append(url)
                print(f"  M3u8 found: {url[:100]}")
            if any(x in url for x in ['video', 'stream', 'play', 'manifest', '.ts', 'chunk']):
                video_requests.append(url)
        
        page.on("request", handle_request)
        
        # Also listen for responses
        async def handle_response(response):
            url = response.url
            if '.m3u8' in url and response.status == 200:
                print(f"  M3u8 response: {url[:100]} (status: {response.status})")
                # Read the body
                try:
                    body = await response.text()
                    print(f"  M3u8 content: {body[:200]}")
                except:
                    pass
        
        page.on("response", handle_response)
        
        print(f"\n2. Loading /prorcp/ page...")
        await page.goto(prorcp_full, wait_until="networkidle", timeout=30000)
        
        # Wait for the player to load
        print("3. Waiting for player...")
        await page.wait_for_timeout(5000)
        
        # Click the play button
        print("4. Clicking play button...")
        try:
            await page.click("#pl_but", timeout=10000)
            await page.wait_for_timeout(8000)
        except:
            try:
                await page.click("#pl_but_background", timeout=10000)
                await page.wait_for_timeout(8000)
            except:
                print("  No play button found, trying other selectors...")
                # Try clicking on the page
                try:
                    await page.click("body", timeout=5000)
                    await page.wait_for_timeout(5000)
                except:
                    pass
        
        # Wait more for the video to load
        print("5. Waiting for video to load...")
        await page.wait_for_timeout(10000)
        
        # Check for video element
        video_src = await page.evaluate("""
            () => {
                let videos = document.querySelectorAll('video');
                let srcs = [];
                videos.forEach(v => {
                    if (v.src) srcs.push(v.src);
                    if (v.currentSrc) srcs.push(v.currentSrc);
                });
                return srcs;
            }
        """)
        
        if video_src:
            print(f"\n6. Video source found: {video_src}")
            for v in video_src:
                if '.m3u8' in v:
                    m3u8_urls.append(v)
        
        # Also check iframes
        frames = page.frames
        print(f"\n7. Frames: {len(frames)}")
        for frame in frames:
            frame_videos = await frame.evaluate("""
                () => {
                    let videos = document.querySelectorAll('video');
                    let srcs = [];
                    videos.forEach(v => {
                        if (v.src) srcs.push(v.src);
                        if (v.currentSrc) srcs.push(v.currentSrc);
                    });
                    return srcs;
                }
            """)
            if frame_videos:
                print(f"  Frame {frame.url[:50]}: videos={frame_videos}")
        
        await browser.close()
    
    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  M3u8 URLs collected: {len(m3u8_urls)}")
    for u in m3u8_urls:
        print(f"  - {u[:100]}")
    print(f"  Video requests: {len(video_requests)}")
    
    return len(m3u8_urls) > 0


async def test_playwright_vidsrcme():
    """Test loading the VidSrc.me embed page directly"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed")
        return False
    
    print("\n" + "=" * 60)
    print("Playwright: Direct VidSrc.me embed")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = await context.new_page()
        
        m3u8_urls = []
        
        page.on("response", lambda resp: m3u8_urls.append(resp.url) if '.m3u8' in resp.url else None)
        
        print("Loading: https://vidsrc.me/embed/238")
        await page.goto("https://vidsrc.me/embed/238", wait_until="networkidle", timeout=30000)
        
        # Wait for the iframe to load
        await page.wait_for_timeout(5000)
        
        # Get iframe content
        frames = page.frames
        print(f"Frames: {len(frames)}")
        for frame in frames:
            print(f"  - {frame.url[:80]}")
        
        # Check if there's a video element
        video_src = await page.evaluate("""
            () => {
                let videos = document.querySelectorAll('video');
                let srcs = [];
                videos.forEach(v => {
                    if (v.src) srcs.push(v.src);
                });
                return srcs;
            }
        """)
        print(f"Videos: {video_src}")
        
        await browser.close()
    
    print(f"M3u8 found: {len(m3u8_urls)}")
    for u in m3u8_urls:
        print(f"  {u[:100]}")
    
    return len(m3u8_urls) > 0


async def main():
    # Install playwright if needed
    import subprocess
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    
    ok1 = await test_playwright_extraction()
    ok2 = await test_playwright_vidsrcme()
    
    print(f"\n{'=' * 60}")
    print(f"/prorcp/ extraction: {'PASS' if ok1 else 'FAIL'}")
    print(f"VidSrc.me embed: {'PASS' if ok2 else 'FAIL'}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    asyncio.run(main())
