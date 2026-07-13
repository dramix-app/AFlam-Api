"""
AFlam-Api Configuration
All provider sources and their URL building logic
"""
import os
from typing import Dict, List, Any

PORT = int(os.getenv("PORT", 8000))
TIMEOUT = int(os.getenv("TIMEOUT", 30000))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", 8))
SCREENSHOT_ENABLED = os.getenv("SCREENSHOT_ENABLED", "false").lower() == "true"


class Provider:
    """Represents a single video source provider."""
    def __init__(self, provider_id: str, label: str, domain: str,
                 url_pattern: Dict[str, str],
                 extract_strategy: str = "playwright"):
        self.id = provider_id
        self.label = label
        self.domain = domain
        self.url_pattern = url_pattern  # {"movie": "...", "tv": "..."}
        self.extract_strategy = extract_strategy

    def build_url(self, tmdb_id: str, media_type: str,
                  season: int = None, episode: int = None) -> str:
        if media_type == "movie":
            url = self.url_pattern.get("movie", "")
            if "{id}" in url:
                return url.format(id=tmdb_id)
            return url + tmdb_id
        elif media_type == "tv":
            url = self.url_pattern.get("tv", "")
            if "{id}" in url:
                return url.format(id=tmdb_id, season=season, episode=episode)
            return url + f"{tmdb_id}/{season}/{episode}"
        return ""


# ============================================================
# 25+ Provider Sources for M3u8 Extraction
# ============================================================
PROVIDERS: List[Provider] = [
    # 1. VidSrc.pm
    Provider("vidsrc.pm", "VidSrc.pm", "vidsrc.pm",
             {"movie": "https://vidsrc.pm/embed/movie/{id}", "tv": "https://vidsrc.pm/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 2. MoviesAPI
    Provider("moviesapi", "MoviesAPI", "moviesapi.to",
             {"movie": "https://moviesapi.to/movie/{id}", "tv": "https://moviesapi.to/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 3. 111Movies
    Provider("111movies", "111Movies", "111movies.net",
             {"movie": "https://111movies.net/movie/{id}", "tv": "https://111movies.net/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 4. VidCore
    Provider("vidcore", "VidCore", "vidcore.org",
             {"movie": "https://vidcore.org/embed/movie/{id}", "tv": "https://vidcore.org/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 5. VidSrc.to
    Provider("vidsrc.to", "VidSrc.to", "vidsrc.to",
             {"movie": "https://vidsrc.to/embed/movie/{id}", "tv": "https://vidsrc.to/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 6. VidSrc.me
    Provider("vidsrc.me", "VidSrc.me", "vidsrc.me",
             {"movie": "https://vidsrc.me/embed/movie/{id}", "tv": "https://vidsrc.me/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 7. VidLink.pro
    Provider("vidlink", "VidLink.pro", "vidlink.pro",
             {"movie": "https://vidlink.pro/movie/{id}", "tv": "https://vidlink.pro/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 8. VsEmbed.ru
    Provider("vsembed", "VsEmbed.ru", "vsembed.ru",
             {"movie": "https://vsembed.ru/embed/movie/{id}", "tv": "https://vsembed.ru/embed/tv/{id}"},
             extract_strategy="playwright"),

    # 9. VidSrc.top
    Provider("vidsrc.top", "VidSrc.top", "vid-src.top",
             {"movie": "https://vid-src.top/embed/movie/{id}", "tv": "https://vid-src.top/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 10. VidSpark.to
    Provider("vidspark", "VidSpark.to", "vidspark.to",
             {"movie": "https://vidspark.to/movie/{id}", "tv": "https://vidspark.to/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 11. AutoEmbed.co
    Provider("autoembed", "AutoEmbed.co", "autoembed.co",
             {"movie": "https://autoembed.co/movie/tmdb/{id}", "tv": "https://autoembed.co/tv/tmdb/{id}-{season}-{episode}"},
             extract_strategy="playwright"),

    # 12. VidSrc.in
    Provider("vidsrc.in", "VidSrc.in", "vidsrc.in",
             {"movie": "https://vidsrc.in/embed/movie/{id}", "tv": "https://vidsrc.in/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 13. Embed.su
    Provider("embed.su", "Embed.su", "embed.su",
             {"movie": "https://embed.su/embed/movie/{id}", "tv": "https://embed.su/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 14. SmashyStream.com
    Provider("smashy", "SmashyStream", "smashystream.com",
             {"movie": "https://embed.smashystream.com/playere.php?tmdb={id}", "tv": "https://embed.smashystream.com/playere.php?tmdb={id}&s={season}&e={episode}"},
             extract_strategy="playwright"),

    # 15. MovieNinja
    Provider("movieninja", "MovieNinja", "movieninja.com",
             {"movie": "https://movieninja.com/player/movie/{id}", "tv": "https://movieninja.com/player/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 16. Vidsrc.net
    Provider("vidsrc.net", "VidSrc.net", "vidsrc.net",
             {"movie": "https://vidsrc.net/embed/movie/{id}", "tv": "https://vidsrc.net/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 17. FlixHQ
    Provider("flixhq", "FlixHQ", "flixhq.to",
             {"movie": "https://flixhq.to/embed/movie/{id}", "tv": "https://flixhq.to/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 18. 2Embed
    Provider("2embed", "2Embed", "2embed.cc",
             {"movie": "https://www.2embed.cc/embed/{id}", "tv": "https://www.2embed.cc/embedtv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 19. SuperEmbed.stream
    Provider("superembed", "SuperEmbed", "superembed.stream",
             {"movie": "https://superembed.stream/embed/{id}", "tv": "https://superembed.stream/embedtv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 20. VidSrc.xyz
    Provider("vidsrc.xyz", "VidSrc.xyz", "vidsrc.xyz",
             {"movie": "https://vidsrc.xyz/embed/movie/{id}", "tv": "https://vidsrc.xyz/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 21. VidSrc.me (alt)
    Provider("vidsrcme.ru", "VidSrc.me (Alt)", "vidsrcme.ru",
             {"movie": "https://vidsrcme.ru/embed/movie/{id}", "tv": "https://vidsrcme.ru/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 22. Ridoo
    Provider("ridoo", "Ridoo", "ridoo.net",
             {"movie": "https://ridoo.net/embed/movie/{id}", "tv": "https://ridoo.net/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 23. MovieX
    Provider("moviex", "MovieX", "moviex.cc",
             {"movie": "https://moviex.cc/embed/movie/{id}", "tv": "https://moviex.cc/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 24. Animesaturn (Anime support)
    Provider("animesaturn", "AnimeSaturn", "animesaturn.tv",
             {"movie": "https://www.animesaturn.tv/anime/{id}/{episode}", "tv": "https://www.animesaturn.tv/anime/{id}/{episode}"},
             extract_strategy="playwright"),

    # 25. Vidsrc.pro
    Provider("vidsrc.pro", "VidSrc.pro", "vidsrc.pro",
             {"movie": "https://vidsrc.pro/embed/movie/{id}", "tv": "https://vidsrc.pro/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 26. Vidsrc.icu
    Provider("vidsrc.icu", "VidSrc.icu", "vidsrc.icu",
             {"movie": "https://vidsrc.icu/embed/movie/{id}", "tv": "https://vidsrc.icu/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 27. Vidsrc.cc
    Provider("vidsrc.cc", "VidSrc.cc", "vidsrc.cc",
             {"movie": "https://vidsrc.cc/embed/movie/{id}", "tv": "https://vidsrc.cc/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),

    # 28. GoMovies
    Provider("gomovies", "GoMovies", "gomovies.sx",
             {"movie": "https://gomovies.sx/embed/movie/{id}", "tv": "https://gomovies.sx/embed/tv/{id}/{season}/{episode}"},
             extract_strategy="playwright"),
]


def get_provider_by_id(provider_id: str) -> Provider:
    """Get a single provider by its ID."""
    for p in PROVIDERS:
        if p.id == provider_id:
            return p
    return None


def get_all_providers() -> List[Provider]:
    """Get all available providers."""
    return PROVIDERS.copy()


def get_provider_count() -> int:
    """Get total number of providers."""
    return len(PROVIDERS)
