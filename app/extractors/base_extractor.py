"""
Base extractor engine using Playwright headless browser
Extracts M3u8 streams, subtitles, and quality info from embedded players
"""
import re
import asyncio
import json
import time
import os
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response

from ..config import TIMEOUT, SCREENSHOT_ENABLED


class StreamResult:
    """Result of a single source extraction."""
    def __init__(self, source_id: str, label: str):
        self.source_id = source_id
        self.label = label
        self.hls_url: Optional[str] = None
        self.subtitles: List[Dict[str, str]] = []
        self.qualities: List[str] = []
        self.error: Optional[str] = None
        self.extract_time: float = 0.0
        self.embed_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "label": self.label,
            "hls_url": self.hls_url,
            "subtitles": self.subtitles,
            "qualities": self.qualities,
            "extract_time": round(self.extract_time, 2),
            "error": self.error,
            "embed_url": self.embed_url
        }

    @property
    def is_success(self) -> bool:
        return self.hls_url is not None and self.error is None


# Patterns to detect M3u8 streams in responses and page content
M3U8_PATTERNS = [
    r'https?://[^"\'\\>\s]+\.m3u8[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+/master\.m3u8[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+/playlist\.m3u8[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+index\.m3u8[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+m3u8[^"\'\\>\s]*',
]

SUBTITLE_PATTERNS = [
    r'https?://[^"\'\\>\s]+\.vtt[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+\.srt[^"\'\\>\s]*',
    r'https?://[^"\'\\>\s]+sub[^"\'\\>\s]*\.(?:vtt|srt|webvtt)',
    r'https?://[^"\'\\>\s]+subtitle[^"\'\\>\s]*\.(?:vtt|srt)',
]

LANG_CODES = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
    "de": "German",
    "it": "Italian",
    "tr": "Turkish",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "pl": "Polish",
    "nl": "Dutch",
    "ro": "Romanian",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
}


class PlaywrightExtractor:
    """
    Core extractor using Playwright to intercept network requests
    and extract M3u8 streams from embedded video players.
    """

    def __init__(self):
        self._m3u8_urls: List[str] = []
        self._subtitle_urls: List[str] = []
        self._response_urls: List[str] = []

    def _reset(self):
        """Reset collected data for a new extraction."""
        self._m3u8_urls = []
        self._subtitle_urls = []
        self._response_urls = []

    def _collect_network_responses(self, response: Response):
        """Intercept and collect all network responses."""
        url = response.url
        self._response_urls.append(url)

        # Detect M3u8 streams
        if '.m3u8' in url or 'playlist' in url or 'm3u8' in url.lower():
            if url not in self._m3u8_urls:
                self._m3u8_urls.append(url)

        # Detect subtitles
        if any(ext in url.lower() for ext in ['.vtt', '.srt', 'subtitle', 'subs']):
            if url not in self._subtitle_urls:
                self._subtitle_urls.append(url)

    async def _scan_page_content(self, page: Page):
        """Scan page content for M3u8 URLs and subtitles embedded in scripts."""
        try:
            content = await page.content()

            # Find M3u8 URLs in page source
            for pattern in M3U8_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    if m not in self._m3u8_urls:
                        self._m3u8_urls.append(m)

            # Find subtitle URLs
            for pattern in SUBTITLE_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for m in matches:
                    if m not in self._subtitle_urls:
                        self._subtitle_urls.append(m)

            # Execute JavaScript to find streams in player objects
            try:
                streams = await page.evaluate("""() => {
                    let streams = [];
                    // Check for HLS player instances
                    if (typeof Hls !== 'undefined' && Hls.instances) {
                        for (let instance of Hls.instances) {
                            if (instance.url) {
                                streams.push(instance.url);
                            }
                        }
                    }
                    // Check common player configurations
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const text = script.textContent || '';
                        const m3u8Matches = text.match(/https?:\\\\/\\\\/[^"'\\\\\\\\s]+\\.m3u8[^"'\\\\\\\\s]*/g);
                        if (m3u8Matches) {
                            streams.push(...m3u8Matches);
                        }
                    }
                    return streams;
                }""")
                if streams:
                    for s in streams:
                        if s and s not in self._m3u8_urls:
                            self._m3u8_urls.append(s)
            except Exception:
                pass
        except Exception:
            pass

    async def _parse_m3u8_qualities(self, m3u8_url: str) -> List[str]:
        """Parse M3u8 playlist to extract available quality variants."""
        qualities = []
        try:
            from playwright.async_api import async_playwright
            # Quick fetch to check quality variants
            base_url = '/'.join(m3u8_url.split('/')[:-1]) + '/'
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(m3u8_url, follow_redirects=True,
                                       headers={'User-Agent': 'Mozilla/5.0'})
                content = resp.text
                # Parse EXT-X-STREAM-INF for quality info
                for line in content.split('\n'):
                    if 'RESOLUTION' in line:
                        match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                        if match:
                            qualities.append(match.group(1))
        except Exception:
            pass
        return qualities

    async def extract(self, embed_url: str, source_id: str, label: str,
                      timeout: int = TIMEOUT) -> StreamResult:
        """
        Extract M3u8 stream from an embedded video URL.
        
        Args:
            embed_url: The embed URL of the video player
            source_id: Provider ID
            label: Provider label
            timeout: Request timeout in milliseconds
        
        Returns:
            StreamResult with extracted data
        """
        result = StreamResult(source_id, label)
        result.embed_url = embed_url
        self._reset()

        start_time = time.time()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    bypass_csp=True,
                )

                page = await context.new_page()

                # Intercept network responses
                page.on("response", self._collect_network_responses)

                # Navigate to embed URL
                await page.goto(embed_url, wait_until="domcontentloaded",
                               timeout=timeout)

                # Wait for network idle (streams usually load within a few seconds)
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                
                # Simulate a click to trigger video loading if needed
                try:
                    # Click multiple times in case of overlays
                    await page.click("body", timeout=2000)
                    await asyncio.sleep(1)
                    await page.click("body", timeout=2000)
                except Exception:
                    pass

                # Additional wait for dynamic content
                await asyncio.sleep(10)

                # Scan page content for embedded streams
                await self._scan_page_content(page)

                # Take screenshot if enabled
                if SCREENSHOT_ENABLED:
                    screenshot_path = f"screenshots/{source_id}_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)

                await context.close()
                await browser.close()

        except Exception as e:
            result.error = str(e)[:200]
            result.extract_time = time.time() - start_time
            return result

        # Process results
        if self._m3u8_urls:
            # Prefer master playlists over individual stream playlists
            master_url = None
            for url in self._m3u8_urls:
                if 'master' in url.lower() or 'playlist' in url.lower():
                    master_url = url
                    break

            result.hls_url = master_url if master_url else self._m3u8_urls[0]

            # Parse qualities if master playlist
            if master_url:
                result.qualities = await self._parse_m3u8_qualities(master_url)
        else:
            result.error = "No M3u8 stream found"

        # Process subtitles
        for sub_url in self._subtitle_urls:
            # Try to extract language from URL
            lang = "unknown"
            for code, name in LANG_CODES.items():
                if code in sub_url.lower():
                    lang = name
                    break
            result.subtitles.append({
                "lang": lang,
                "url": sub_url
            })

        result.extract_time = time.time() - start_time
        return result
