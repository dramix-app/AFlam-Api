# AFlam-Api V3

A professional, high-performance **Multi-Source M3u8 Stream Extraction API** designed to extract HLS video streams, subtitles, and quality information from 25 free video providers (movies, TV shows, and anime) in parallel.

---

## Features

- **25 Verified Sources** — Proven working providers with correct extraction patterns
- **Parallel Extraction** — Uses `asyncio` + `playwright` to scrape multiple sources simultaneously
- **M3u8/HLS Extraction** — Directly extracts the master playlist URL for seamless playback
- **Subtitle Support** — Automatically detects and extracts subtitle tracks (VTT/SRT) in multiple languages
- **Quality Detection** — Parses M3u8 playlists to identify available resolutions (360p to 1080p+)
- **Headless Scraper** — Built on Playwright for reliable extraction from JS-heavy embedded players
- **RESTful API** — Simple, well-documented API built with FastAPI
- **15-Minute Cache** — Avoids re-scraping the same content within 15 minutes
- **Docker Ready** — Production-ready Dockerfile for Render, Railway, or Fly.io

---

## Installation

### Local Setup

```bash
git clone https://github.com/dramix-app/AFlam-Api.git
cd AFlam-Api
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

### Docker

```bash
docker build -t aflam-api .
docker run -p 8000:8000 aflam-api
```

---

## API Usage

### 1. Health Check

`GET /health`

### 2. List All Sources

`GET /sources`

### 3. Extract All Sources (Parallel)

`GET /extract?tmdb_id={id}&type={movie|tv}&season={s}&episode={e}`

**Parameters:**

| Parameter | Description |
|---|---|
| `tmdb_id` | TMDB ID (e.g., `550`) |
| `type` | `movie` or `tv` |
| `season` | Season number (required for TV) |
| `episode` | Episode number (required for TV) |
| `source` | (Optional) Specific source ID to extract from |

### 4. Extract from Specific Source

`GET /extract/{source_id}?tmdb_id={id}&type=movie`

### 5. Get Best Streams Only

`GET /streams/best?tmdb_id={id}&type=movie`

---

## Supported Sources (25)

| # | Provider | Domain |
|---|---|---|
| 1 | VsEmbed.ru | vsembed.ru |
| 2 | VsEmbed.su | vsembed.su |
| 3 | VidSrc.me (Alt) | vidsrcme.ru |
| 4 | 111Movies | 111movies.net |
| 5 | VidCore | vidcore.org |
| 6 | VidSrc.me | vidsrc.me |
| 7 | VidSrc.in | vidsrc.in |
| 8 | VidSrc.pm | vidsrc.pm |
| 9 | VidSrc.net | vidsrc.net |
| 10 | VidSrc.to | vidsrc.to |
| 11 | VidSrc.top | vid-src.top |
| 12 | VidSrc.pro | vidsrc.pro |
| 13 | VidSrc.cc | vidsrc.cc |
| 14 | VidSrc.icu | vidsrc.icu |
| 15 | VidLink.pro | vidlink.pro |
| 16 | VidSpark.to | vidspark.to |
| 17 | AutoEmbed.co | autoembed.co |
| 18 | MoviesAPI | moviesapi.to |
| 19 | SuperEmbed | superembed.stream |
| 20 | 2Embed | 2embed.cc |
| 21 | Ridoo | ridoo.net |
| 22 | MovieX | moviex.cc |
| 23 | SmashyStream | smashystream.com |
| 24 | FlixHQ | flixhq.to |
| 25 | GoMovies | gomovies.sx |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Server port |
| `MAX_CONCURRENT` | `5` | Max parallel extractions |
| `TIMEOUT` | `45000` | Request timeout (ms) |
| `CACHE_TTL` | `900` | Cache TTL (seconds) |

---

## Render Deployment

1. Connect repo to Render as **Web Service**
2. Runtime: **Docker**
3. Add env vars: `PORT=8000`, `MAX_CONCURRENT=5`, `TIMEOUT=45000`
4. Deploy

---

## License

This project is for educational purposes only. The developers are not responsible for how this tool is used.
