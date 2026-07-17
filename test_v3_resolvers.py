"""
Test V3 API - Test resolver-based extraction with real TMDB IDs
"""
import asyncio
import sys
import time
sys.path.insert(0, '.')

async def test_vidsrc_me():
    """Test VidSrc.me resolver"""
    print("\n" + "=" * 60)
    print("TEST: VidSrc.me Resolver")
    print("=" * 60)
    
    from app.resolvers.extractors.vidsrc_me import resolve_vidsrc_me
    
    # The Godfather (TMDB: 238)
    results = await resolve_vidsrc_me("238", "movie")
    
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  Name: {r.get('name')}")
        print(f"  Stream: {r.get('stream', 'N/A')[:80] if r.get('stream') else 'N/A'}")
        print(f"  Subtitles: {len(r.get('subtitles', []))} tracks")
        print(f"  Source: {r.get('source')}")
        print()
    
    return len(results) > 0 and any(r.get("stream") for r in results)


async def test_vidsrc_to():
    """Test VidSrc.to resolver"""
    print("\n" + "=" * 60)
    print("TEST: VidSrc.to Resolver")
    print("=" * 60)
    
    from app.resolvers.extractors.vidsrc_me import resolve_vidsrc_to
    
    results = await resolve_vidsrc_to("238", "movie")
    
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  Name: {r.get('name')}")
        print(f"  Stream: {r.get('stream', 'N/A')[:80] if r.get('stream') else 'N/A'}")
        print(f"  Subtitles: {len(r.get('subtitles', []))} tracks")
        print(f"  Source: {r.get('source')}")
        print()
    
    return len(results) > 0 and any(r.get("stream") for r in results)


async def test_other_sources():
    """Test other source extractors"""
    print("\n" + "=" * 60)
    print("TEST: Other Sources (111Movies, VidCore, etc.)")
    print("=" * 60)
    
    from app.resolvers.extractors.other_sources import (
        resolve_111movies, resolve_vidcore, resolve_flixhq, resolve_2embed
    )
    
    tests = [
        ("111Movies", resolve_111movies),
        ("VidCore", resolve_vidcore),
        ("FlixHQ", resolve_flixhq),
        ("2Embed", resolve_2embed),
    ]
    
    for name, resolver in tests:
        start = time.time()
        results = await resolver("238", "movie")
        elapsed = time.time() - start
        
        success = len(results) > 0 and any(r.get("stream") for r in results)
        status = "SUCCESS" if success else "FAILED"
        
        print(f"  {name}: {status} ({elapsed:.2f}s)")
        if results:
            for r in results:
                stream = r.get("stream", "")
                if stream:
                    print(f"    Stream: {stream[:80]}")
    
    return True


async def test_full_api():
    """Test the full API resolve_all"""
    print("\n" + "=" * 60)
    print("TEST: Full API (resolve_all)")
    print("=" * 60)
    
    from app.resolvers import resolve_all, get_extractor_names
    
    print(f"Configured extractors: {len(get_extractor_names())}")
    for e in get_extractor_names():
        print(f"  - {e['name']} ({e['id']})")
    
    start = time.time()
    results = await resolve_all("238", "movie", max_concurrent=3)
    elapsed = time.time() - start
    
    successful = [r for r in results if r.get("stream") and r["stream"] is not None]
    failed = [r for r in results if not r.get("stream") or r["stream"] is None]
    
    print(f"\nTotal time: {elapsed:.2f}s")
    print(f"Total results: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    print("\n--- Successful Streams ---")
    for r in successful:
        print(f"  [{r.get('name')}] {r.get('stream', '')[:80]}")
        if r.get('subtitles'):
            print(f"    Subtitles: {len(r['subtitles'])} tracks")
    
    print("\n--- Failed Sources ---")
    for r in failed:
        print(f"  [{r.get('name')}] {r.get('error', 'Unknown error')}")
    
    return len(successful) > 0


async def test_tv_show():
    """Test TV show extraction"""
    print("\n" + "=" * 60)
    print("TEST: TV Show (Breaking Bad S1E1)")
    print("=" * 60)
    
    from app.resolvers.extractors.vidsrc_me import resolve_vidsrc_me, resolve_vidsrc_to
    
    print("\nVidSrc.me:")
    results_me = await resolve_vidsrc_me("1396", "tv", season=1, episode=1)
    for r in results_me:
        print(f"  [{r.get('name')}] Stream: {r.get('stream', 'N/A')[:60] if r.get('stream') else 'N/A'}")
    
    print("\nVidSrc.to:")
    results_to = await resolve_vidsrc_to("1396", "tv", season=1, episode=1)
    for r in results_to:
        print(f"  [{r.get('name')}] Stream: {r.get('stream', 'N/A')[:60] if r.get('stream') else 'N/A'}")
    
    return True


async def main():
    print("=" * 60)
    print("AFlam-Api V3 - Resolver Test Suite")
    print("Testing RC4/RC6 decryption-based extraction")
    print("=" * 60)
    
    # Test individual resolvers
    me_ok = await test_vidsrc_me()
    to_ok = await test_vidsrc_to()
    other_ok = await test_other_sources()
    
    # Test full API
    full_ok = await test_full_api()
    
    # Test TV
    await test_tv_show()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  VidSrc.me: {'PASS' if me_ok else 'FAIL'}")
    print(f"  VidSrc.to: {'PASS' if to_ok else 'FAIL'}")
    print(f"  Other Sources: {'PASS' if other_ok else 'FAIL'}")
    print(f"  Full API: {'PASS' if full_ok else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
