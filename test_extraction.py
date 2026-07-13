import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extractors.base_extractor import PlaywrightExtractor
from app.config import PROVIDERS

async def test_sources():
    extractor = PlaywrightExtractor()
    tmdb_id = "157336" # Interstellar
    
    # Test top 5 sources
    for i in range(5):
        provider = PROVIDERS[i]
        embed_url = provider.build_url(tmdb_id, "movie")
        
        print(f"\n[{i+1}/5] Testing: {provider.label}")
        print(f"URL: {embed_url}")
        
        result = await extractor.extract(embed_url, provider.id, provider.label, timeout=45000)
        
        print(f"Result: {'SUCCESS' if result.is_success else 'FAILED'}")
        if result.is_success:
            print(f"HLS: {result.hls_url[:60]}...")
            print(f"Subs: {len(result.subtitles)}")
        else:
            print(f"Error: {result.error}")
        print(f"Time: {result.extract_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_sources())
