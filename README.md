# html-vd-new 🎬

Automated HTML animation to vertical video (9:16) rendering & multi-platform publishing pipeline.

Optimized for **Instagram Reels**, **Facebook Reels / Pages**, **Threads**, and **TikTok**.

---

## 🌟 Architecture & Features

1. **Auto Animation Length Detection**:
   - Detects duration dynamically via runtime JavaScript variables (`window.DUR`, `window.T`, `window.EV`, `window.CAP`).
   - Analyzes DOM scene datasets (`data-d="seconds"`).
   - Automatically synchronizes recording duration with the loop period of the HTML animation.

2. **Smart Audio Looping & Matching**:
   - Loops shorter background tracks (`-stream_loop -1` in FFmpeg) if the music track is shorter than the video.
   - Smoothly trims longer music tracks to match the exact video duration.
   - Applies an automatic audio fade-out (`afade=t=out`) in the final 0.5s for clean transitions.

3. **Production Quality 9:16 Video**:
   - Viewport: `1080x1920` (standard 9:16 vertical ratio).
   - Framerate: `60 FPS` constant.
   - Video Codec: `H.264 (High Profile, YUV420p)` for universal mobile and web playback.
   - Audio Codec: `AAC Stereo 192kbps, 44.1kHz`.
   - Injects custom CSS during recording to hide interactive replay/debug buttons (`.ui, #rp, button`).

4. **Viral AI Metadata Generation (Pollinations AI)**:
   - Automatically extracts clean topics from HTML filenames.
   - Generates high-converting, tailored titles, Instagram captions (with bullet points & comment hooks), Facebook tech post descriptions, and trending hashtags.

5. **Multi-Platform Social Media Publishing**:
   - Direct integration with Instagram Graph API (Reels container upload).
   - Direct integration with Facebook Graph API (Reels & Page video publishing).
   - Direct integration with Threads API.

6. **Automated GitHub Actions CI/CD**:
   - Runs automatically on schedule (twice daily) and via manual dispatch.
   - Syncs from Google Drive, renders, generates captions, and publishes.

---

## 📁 Directory Structure

```
html-vd-new/
├── .github/workflows/
│   └── automate.yml         # GitHub Actions automated publishing workflow
├── converter.py             # Core 1080p video generation engine & CLI
├── sync_gdrive.py           # Google Drive Service Account synchronization
├── generate_metadata.py     # AI title, caption & hashtag generator (Pollinations)
├── publish.py               # Social media publishing runner
├── orchestrator.py          # End-to-end pipeline runner
├── upload/                  # Platform-specific API upload modules (FB, IG, Threads)
├── requirements.txt         # Python dependencies
├── html_sources/            # Synced HTML animation files from Google Drive
├── music/                   # Background audio tracks (.mp3)
└── output/                  # Rendered high-definition 1080p MP4 videos
```

---

## 🔐 Configured GitHub Secrets

All secrets are configured in the repository:
- `POLLINATIONS_API_KEY`: Pollinations AI access key.
- `GOOGLE_SERVICE_ACCOUNT_KEY`: Service account JSON key with Drive access.
- `GDRIVE_HTML_FOLDER_ID`: `19LQ5ofL1ScBKGiidAH7tNxM0xruG1TJ-`
- `GDRIVE_MUSIC_FOLDER_ID`: `19zTCpkmKpZwUm8j8gnvfHZqVJqfwEz9I`
- `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_ACCOUNT_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN` / `FACEBOOK_PAGE_ID`
- `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID`

---

## 🚀 Usage

### 1. Run the Complete Automated Pipeline

```bash
# Sync Drive -> Render Next Animation -> Generate AI Captions -> Publish
python orchestrator.py --publish
```

Without social publishing (local render and metadata only):
```bash
python orchestrator.py
```

### 2. Manual Individual Steps

- **Sync Google Drive Assets:**
  ```bash
  python sync_gdrive.py
  ```

- **Convert a Single HTML File to 1080p MP4:**
  ```bash
  python converter.py --html "html_sources/What Happens When You Hit Enter.html"
  ```

- **Generate AI Social Metadata:**
  ```bash
  python generate_metadata.py "What Happens When You Hit Enter.html"
  ```

- **Publish an Existing Video:**
  ```bash
  python publish.py "output/What Happens When You Hit Enter.mp4" "metadata.json"
  ```
