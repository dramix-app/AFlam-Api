"""
Playwright v3 - Fixed API usage with page.locator()
"""
import asyncio
import re
from playwright.async_api import async_playwright

async def test_full_chain():
    print("=" * 60)
    print("Playwright: Full chain extraction")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        m3u8_urls = []
        
        page.on("response", lambda resp: (m3u8_urls.append(resp.url), print(f"  M3u8: {resp.url[:100]}")) if '.m3u8' in resp.url else None)
        
        # Load the embed page
        print("\n1. Loading VidSrc.me embed...")
        await page.goto("https://vidsrc.me/embed/238", wait_until="load", timeout=30000)
        await page.wait_for_timeout(8000)
        
        # Check for iframe using locator
        iframe_locator = page.locator("iframe")
        iframe_count = await iframe_locator.count()
        print(f"   Iframes: {iframe_count}")
        
        if iframe_count > 0:
            first_frame = page.frame("iframe")
            if first_frame:
                print(f"   Frame URL: {first_frame.url[:80]}")
                
                # Wait for the RCP page to load
                await page.wait_for_timeout(3000)
                
                # Look for sub-iframe in the RCP frame
                sub_iframe = first_frame.locator("iframe")
                sub_count = await sub_iframe.count()
                print(f"   Sub-iframes in RCP: {sub_count}")
                
                if sub_count > 0:
                    sub_frame = first_frame.frame("iframe")
                    if sub_frame:
                        print(f"   Sub-frame URL: {sub_frame.url[:80]}")
                        
                        # Check for video
                        videos = await sub_frame.query_selector_all("video")
                        print(f"   Videos: {len(videos)}")
                        
                        # Get all video sources
                        for v in videos:
                            src = await v.get_attribute("src")
                            current_src = await v.get_attribute("currentSrc")
                            print(f"     src={src[:60]}, currentSrc={current_src[:60]}")
                        
                        # Check for player config
                        try:
                            player_config = await sub_frame.evaluate("""
                                () => {
                                    let info = {};
                                    // Check for HLS.js
                                    if (window.hls) {
                                        info.hls = window.hls.currentLevel || 0;
                                    }
                                    // Check for PlayerJS
                                    if (window.player) {
                                        try { info.player = JSON.stringify(window.player).substring(0, 200); } catch(e) {}
                                    }
                                    return info;
                                }
                            """)
                            if player_config:
                                print(f"   Player config: {player_config}")
                        except Exception as e:
                            print(f"   Player eval error: {e}")
            else:
                print("   Frame not accessible (cross-origin)")
        else:
            print("   No iframe found")
        
        # Wait for any video to load
        await page.wait_for_timeout(10000)
        
        # Check all frames for video
        print(f"\n2. All frames: {len(page.frames)}")
        for frame in page.frames:
            print(f"   - {frame.url[:70]}")
            try:
                videos = await frame.evaluate("""
                    () => {
                        let srcs = [];
                        document.querySelectorAll('video').forEach(v => {
                            srcs.push({src: v.src || '', currentSrc: v.currentSrc || ''});
                        });
                        return srcs;
                    }
                """)
                if videos:
                    print(f"     Videos: {videos}")
            except:
                pass
        
        await browser.close()
    
    print(f"\n{'=' * 60}")
    print(f"M3u8 found: {len(m3u8_urls)}")
    for u in m3u8_urls:
        print(f"  {u[:100]}")
    return len(m3u8_urls) > 0


async def test_vsembed_direct():
    print("\n" + "=" * 60)
    print("Playwright: vsembed.ru direct")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        m3u8_urls = []
        
        page.on("response", lambda resp: (m3u8_urls.append(resp.url), print(f"  M3u8: {resp.url[:100]}")) if '.m3u8' in resp.url else None)
        
        print("Loading: https://vsembed.ru/embed/movie/238/")
        await page.goto("https://vsembed.ru/embed/movie/238/", wait_until="load", timeout=30000)
        await page.wait_for_timeout(5000)
        
        # Check frames
        for frame in page.frames:
            print(f"   Frame: {frame.url[:70]}")
            try:
                videos = await frame.evaluate("""
                    () => {
                        let srcs = [];
                        document.querySelectorAll('video').forEach(v => {
                            srcs.push({src: v.src || '', currentSrc: v.currentSrc || ''});
                        });
                        return srcs;
                    }
                """)
                if videos:
                    print(f"     Videos: {videos}")
            except:
                pass
        
        await browser.close()
    
    print(f"M3u8 found: {len(m3u8_urls)}")
    return len(m3u8_urls) > 0


async def test_vidsrcme_sources_js():
    """
    The vidsrcme.ru page loads sources.js which contains the source URLs.
    Let's fetch and parse it.
    """
    print("\n" + "=" * 60)
    print("Fetch and parse sources.js from vidsrcme.ru")
    print("=" * 60)
    
    import httpx
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
        
        # Fetch sources.js
        print("Fetching sources.js...")
        resp = await client.get("https://vidsrcme.ru/sources.js?t=1745104089", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Content:\n{resp.text[:3000]}")


async def main():
    ok1 = await test_full_chain()
    ok2 = await test_vsembed_direct()
    await test_vidsrcme_sources_js()
    
    print(f"\n{'=' * 60}")
    print(f"Full chain: {'PASS' if ok1 else 'FAIL'}")
    print(f"Vsembed direct: {'PASS' if ok2 else 'FAIL'}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    asyncio.run(main())
