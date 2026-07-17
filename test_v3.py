"""Test V3 API - test extraction from verified working sources"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.extractors.base_extractor import PlaywrightExtractor, StreamResult
from app.config import Provider, PROVIDERS, get_provider_count

async def test_extraction():
    print("=" * 60)
    print("AFlam-Api V3 - Extraction Test")
    print(f"Total providers configured: {get_provider_count()}")
    print("=" * 60)

    extractor = PlaywrightExtractor()
    
    # Test movie: The Godfather (TMDB: 238)
    tmdb_id = "238"
    
    # Test with verified working providers first
    test_providers = [
        # Tier 1 - guaranteed working
        PROVIDERS[0],  # vsembed
        PROVIDERS[3],  # 111movies
        PROVIDERS[4],  # vidcore
    ]
    
    results = []
    for p in test_providers:
        url = p.build_url(tmdb_id, "movie")
        print(f"\nTesting: {p.label} ({p.domain})")
        print(f"URL: {url}")
        
        result = await extractor.extract(embed_url=url, provider=p)
        
        status = "SUCCESS" if result.is_success else "FAILED"
        print(f"  Status: {status}")
        if result.hls_url:
            print(f"  HLS URL: {result.hls_url[:80]}...")
        if result.subtitles:
            print(f"  Subtitles: {len(result.subtitles)} tracks")
        if result.qualities:
            print(f"  Qualities: {result.qualities}")
        if result.error:
            print(f"  Error: {result.error[:80]}")
        print(f"  Time: {result.extract_time:.2f}s")
        
        results.append(result)

    success_count = sum(1 for r in results if r.is_success)
    print(f"\n{'=' * 60}")
    print(f"Results: {success_count}/{len(results)} sources successful")
    print(f"{'=' * 60}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_extraction())
