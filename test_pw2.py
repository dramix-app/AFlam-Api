"""
Playwright v2 - Load the full VidSrc.me page with the iframe, 
then wait for the iframe to load and extract the M3u8 from within it.
"""
import asyncio
import re
from playwright.async_api import async_playwright

async def test_full_chain():
    print("=" * 60)
    print("Playwright: Full chain - embed -> iframe -> /prorcp/ -> video")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        all_m3u8 = []
        all_responses = []
        
        async def handle_response(response):
            url = response.url
            all_responses.append(url)
            if '.m3u8' in url:
                all_m3u8.append(url)
                print(f"  M3u8: {url[:120]}")
            if any(x in url for x in ['pro', 'stream', 'vidsrc', 'cloud', 'roilandrelic']):
                print(f"  Resource: {url[:100]}")
        
        page.on("response", handle_response)
        
        # Step 1: Load the embed page
        print("\n1. Loading VidSrc.me embed...")
        await page.goto("https://vidsrc.me/embed/238", wait_until="load", timeout=30000)
        print(f"   URL: {page.url}")
        
        # Wait for iframe to appear
        await page.wait_for_timeout(5000)
        
        # Check for iframe
        iframe = page.query_selector("iframe")
        if iframe:
            src = await iframe.get_attribute("src")
            print(f"   Iframe src: {src[:80]}...")
            
            # Get the iframe's frame
            frame = iframe.content_frame()
            if frame:
                print(f"   Frame URL: {frame.url}")
                
                # Wait for the /prorcp/ iframe inside the RCP frame
                await frame.wait_for_timeout(3000)
                
                # Look for the play button in the frame
                try:
                    play_btn = frame.query_selector("#pl_but")
                    if play_btn:
                        print("   Found play button, clicking...")
                        await play_btn.click()
                        await frame.wait_for_timeout(10000)
                except:
                    pass
                
                # Check for sub-iframes
                sub_iframes = frame.query_selector_all("iframe")
                print(f"   Sub-iframes in frame: {len(sub_iframes)}")
                for si in sub_iframes:
                    si_src = await si.get_attribute("src")
                    print(f"     - {si_src[:80]}...")
                    
                    # Get sub-frame
                    sub_frame = await si.content_frame()
                    if sub_frame:
                        print(f"     Sub-frame URL: {sub_frame.url[:80]}")
                        
                        # Check for video
                        videos = await sub_frame.query_selector_all("video")
                        print(f"     Videos in sub-frame: {len(videos)}")
                        for v in videos:
                            v_src = await v.get_attribute("src")
                            print(f"       src: {v_src[:80]}")
                        videos2 = await sub_frame.query_selector_all("source")
                        for v in videos2:
                            v_src = await v.get_attribute("src")
                            print(f"       source: {v_src[:80]}")
            else:
                print("   Frame not accessible")
        else:
            print("   No iframe found on embed page")
        
        # Wait more
        await page.wait_for_timeout(5000)
        
        # Check ALL frames
        print(f"\n2. All frames ({len(page.frames)}):")
        for i, frame in enumerate(page.frames):
            print(f"   Frame {i}: {frame.url[:80]}")
            
            # Look for video elements in each frame
            try:
                video_data = await frame.evaluate("""
                    () => {
                        let results = [];
                        let videos = document.querySelectorAll('video');
                        videos.forEach(v => {
                            results.push({
                                src: v.src || '',
                                currentSrc: v.currentSrc || '',
                                readyState: v.readyState || 0,
                                currentTime: v.currentTime || 0,
                                paused: v.paused
                            });
                        });
                        // Also check for HLS.js or other player configs
                        if (window.player || window.hls) {
                            let cfg = window.player || window.hls;
                            try {
                                results.push({config: JSON.stringify(cfg) || ''});
                            } catch(e) {}
                        }
                        return results;
                    }
                """)
                if video_data:
                    print(f"     Videos: {video_data}")
            except Exception as e:
                print(f"     Frame eval error: {e}")
        
        await browser.close()
    
    print(f"\n{'=' * 60}")
    print(f"M3u8 URLs found: {len(all_m3u8)}")
    for u in all_m3u8:
        print(f"  {u[:120]}")
    return len(all_m3u8) > 0


async def test_vsembed_direct():
    """Test vsembed.ru directly - it might be simpler"""
    print("\n" + "=" * 60)
    print("Playwright: Direct vsembed.ru")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()
        
        m3u8_urls = []
        
        page.on("response", lambda resp: m3u8_urls.append(resp.url) if '.m3u8' in resp.url else None)
        
        print("Loading: https://vsembed.ru/embed/movie/238/")
        await page.goto("https://vsembed.ru/embed/movie/238/", wait_until="load", timeout=30000)
        print(f"   URL: {page.url}")
        
        await page.wait_for_timeout(5000)
        
        # Check all frames
        for frame in page.frames:
            print(f"   Frame: {frame.url[:80]}")
            try:
                videos = await frame.evaluate("""
                    () => {
                        let srcs = [];
                        document.querySelectorAll('video, source, iframe').forEach(el => {
                            if (el.src) srcs.push(el.src);
                            if (el.currentSrc) srcs.push(el.currentSrc);
                        });
                        return srcs;
                    }
                """)
                if videos:
                    print(f"     Sources: {videos}")
            except:
                pass
        
        # Check for iframe with /prorcp/
        iframe = page.query_selector("iframe")
        if iframe:
            src = await iframe.get_attribute("src")
            print(f"   Iframe: {src[:80]}...")
            
            frame = iframe.content_frame()
            if frame:
                print(f"   Frame: {frame.url}")
                
                # Wait and try to click
                await frame.wait_for_timeout(3000)
                
                # Look for prorcp in sub-iframes
                sub_iframes = frame.query_selector_all("iframe")
                for si in sub_iframes:
                    si_src = await si.get_attribute("src")
                    print(f"   Sub-iframe: {si_src[:80]}...")
                    
                    sf = await si.content_frame()
                    if sf:
                        print(f"   Sub-frame: {sf.url[:80]}")
        
        await browser.close()
    
    print(f"M3u8 found: {len(m3u8_urls)}")
    for u in m3u8_urls:
        print(f"  {u[:100]}")
    return len(m3u8_urls) > 0


async def main():
    ok1 = await test_full_chain()
    ok2 = await test_vsembed_direct()
    
    print(f"\n{'=' * 60}")
    print(f"Full chain: {'PASS' if ok1 else 'FAIL'}")
    print(f"Vsembed direct: {'PASS' if ok2 else 'FAIL'}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    asyncio.run(main())
