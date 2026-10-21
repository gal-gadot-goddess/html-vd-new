# html-vd-new 🎬

High-performance HTML animation to vertical video (9:16) rendering pipeline with automatic animation duration detection and audio looping.

Optimized for **Instagram Reels**, **YouTube Shorts**, and **TikTok**.

---

## 🌟 Key Features

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

---

## 📁 Directory Structure

```
html-vd-new/
├── converter.py             # Core video generation engine & CLI
├── sync_gdrive.py           # Google Drive Service Account synchronization
├── requirements.txt         # Python dependencies
├── html_sources/            # Synced HTML animation files from Google Drive
├── music/                   # Background audio tracks (.mp3)
└── output/                  # Rendered high-definition 1080p MP4 videos
```

---

## ☁️ Google Drive Sync

To sync HTML files and music tracks directly from your Google Drive folders using your configured Google Service Account (`GOOGLE_SERVICE_ACCOUNT_KEY` environment variable):

```bash
python sync_gdrive.py
```

This will automatically:
1. Connect via Google Drive API v3 using the service account credentials.
2. Download all HTML files from your HTML folder (`19LQ5ofL1ScBKGiidAH7tNxM0xruG1TJ-`).
3. Download all background tracks from your music folder (`19zTCpkmKpZwUm8j8gnvfHZqVJqfwEz9I`).
4. Clean up any extra local files that are not present in your Drive folder.

---

## 🚀 Quick Start

### 1. Requirements

- Python 3.10+
- FFmpeg installed and in your system PATH
- Playwright Chromium:
  ```bash
  pip install -r requirements.txt
  playwright install chromium
  ```

### 2. Convert a Single HTML File

```bash
python converter.py --html "html_sources/How ChatGPT Works_ The Next Word.html"
```

With specific audio:
```bash
python converter.py --html "html_sources/AI Visuals_ Pick One.html" --audio "music/track_1.mp3"
```

With duration override (in seconds):
```bash
python converter.py --html "html_sources/AI Visuals_ Pick One.html" --duration 12.0
```

### 3. Batch Convert All HTML Files

```bash
python converter.py --all
```

All rendered MP4 videos will be saved into the `output/` folder.
