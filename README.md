# 🎬 AFlam-Api

A professional, high-performance **Multi-Source M3u8 Stream Extraction API** designed to extract HLS video streams, subtitles, and quality information from 28+ free video providers (movies, TV shows, and anime) in parallel.

---

## 🚀 Features

- **28+ Sources**: Supports all major free providers including VidSrc (pm, to, me, in, top, xyz, pro), MoviesAPI, Embed.su, SmashyStream, and more.
- **Parallel Extraction**: Uses `asyncio` and `playwright` to scrape multiple sources simultaneously for maximum speed.
- **M3u8/HLS Extraction**: Directly extracts the master playlist URL for seamless playback in any HLS player.
- **Subtitle Support**: Automatically detects and extracts subtitle tracks (VTT/SRT) in multiple languages.
- **Quality Detection**: Parses M3u8 playlists to identify available resolutions (360p, 480p, 720p, 1080p, etc.).
- **Headless Scraper**: Built on Playwright for reliable extraction even from complex, JS-heavy embedded players.
- **RESTful API**: Simple, well-documented API built with FastAPI.
- **Docker Ready**: Includes a production-ready Dockerfile for deployment on Render, Railway, or Fly.io.

---

## 🛠️ Installation

### 1. Local Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/AFlam-Api.git
cd AFlam-Api

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the server
uvicorn main:app --reload
```

### 2. Docker Setup
```bash
docker build -t aflam-api .
docker run -p 8000:8000 aflam-api
```

---

## 📖 API Usage

### 1. Health Check
`GET /health`
Returns the status of the API and total provider count.

### 2. List All Sources
`GET /sources`
Returns a list of all 28+ supported video providers.

### 3. Extract All Sources (Parallel)
`GET /extract?tmdb_id={id}&type={movie|tv}&season={s}&episode={e}`
Extracts streams from all available sources for a specific movie or episode.

**Parameters:**
- `tmdb_id`: TMDB ID (e.g., `550`) or IMDb ID (e.g., `tt1375666`).
- `type`: `movie` or `tv`.
- `season`: Season number (required for TV).
- `episode`: Episode number (required for TV).

### 4. Extract from Specific Source
`GET /extract/{source_id}?tmdb_id={id}&type={movie|tv}`

### 5. Get Best Streams Only
`GET /streams/best?tmdb_id={id}&type={movie|tv}`
Returns only successful extractions, sorted by quality and extraction speed.

---

## 🌐 Supported Sources (28+)

1.  **VidSrc.pm**
2.  **MoviesAPI**
3.  **111Movies**
4.  **VidCore**
5.  **VidSrc.to**
6.  **VidSrc.me**
7.  **VidLink.pro**
8.  **VsEmbed.ru**
9.  **VidSrc.top**
10. **VidSpark.to**
11. **AutoEmbed.co**
12. **VidSrc.in**
13. **Embed.su**
14. **SmashyStream**
15. **MovieNinja**
16. **VidSrc.net**
17. **FlixHQ**
18. **2Embed**
19. **SuperEmbed**
20. **VidSrc.xyz**
21. **VidSrc.me (Alt)**
22. **Ridoo**
23. **MovieX**
24. **AnimeSaturn**
25. **VidSrc.pro**
26. **VidSrc.icu**
27. **VidSrc.cc**
28. **GoMovies**

---

## 📝 License
This project is for educational purposes only. The developers are not responsible for how this tool is used.

---

## 👤 Developer
Built with ❤️ by Manus for AFlam-Api.
