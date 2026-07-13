import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extractors.base_extractor import PlaywrightExtractor
from app.config import PROVIDERS

async def test():
    extractor = PlaywrightExtractor()
    # Test SmashyStream and VidSrc.to
    targets = ['smashy', 'vidsrc.to', 'vidsrc.me', 'embed.su']
    
    for tid in targets:
        provider = next(p for p in PROVIDERS if p.id == tid)
        url = provider.build_url("157336", "movie")
        print(f"\nTesting {provider.label}...")
        result = await extractor.extract(url, provider.id, provider.label, timeout=60000)
        print(f"Result: {'SUCCESS' if result.is_success else 'FAILED'}")
        if result.is_success:
            print(f"Stream: {result.hls_url}")
            print(f"Subs: {len(result.subtitles)}")
        else:
            print(f"Error: {result.error}")

if __name__ == "__main__":
    asyncio.run(test())
