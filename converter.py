"""
HTML to Video Converter with Looping Audio & Auto Duration Detection
Engineered for 9:16 Vertical Video (Instagram Reels / YouTube Shorts / TikTok)
"""

import os
import sys
import time
import math
import glob
import random
import re
import argparse
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html_sources"
MUSIC_DIR = BASE_DIR / "music"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = OUTPUT_DIR / ".temp_recordings"

def detect_duration(page, file_content: str, default_duration: float = 15.0) -> float:
    """
    Detect the animation duration using in-page JS runtime variables and DOM analysis,
    falling back to static regex parsing.
    """
    # 1. In-page JavaScript evaluation
    try:
        js_detected = page.evaluate("""() => {
            // Check global variables
            if (typeof DUR !== 'undefined' && typeof DUR === 'number' && DUR > 0) {
                return { source: 'window.DUR', value: DUR };
            }
            if (typeof T !== 'undefined' && typeof T === 'number' && T > 0) {
                return { source: 'window.T', value: T };
            }
            
            // Check dataset.d on scenes (e.g. <section class="scene" data-d="6">)
            const sceneDurations = Array.from(document.querySelectorAll('[data-d]'))
                .map(el => parseFloat(el.getAttribute('data-d')))
                .filter(d => !isNaN(d) && d > 0);
            if (sceneDurations.length > 0) {
                const total = sceneDurations.reduce((a, b) => a + b, 0);
                return { source: 'DOM [data-d] sum', value: total };
            }
            
            // Check EV array if present
            if (typeof EV !== 'undefined' && Array.isArray(EV) && EV.length > 0) {
                const maxTs = Math.max(...EV.map(e => (Array.isArray(e) && typeof e[0] === 'number') ? e[0] : 0));
                if (maxTs > 0) {
                    return { source: 'window.EV max timestamp', value: maxTs + 1.5 };
                }
            }
            
            // Check CAP array if present
            if (typeof CAP !== 'undefined' && Array.isArray(CAP) && CAP.length > 0) {
                const maxCap = Math.max(...CAP.map(c => (Array.isArray(c) && typeof c[0] === 'number') ? c[0] : 0));
                if (maxCap > 0) {
                    return { source: 'window.CAP max timestamp', value: maxCap + 2.5 };
                }
            }
            
            return null;
        }""")
        
        if js_detected and js_detected.get("value"):
            val = float(js_detected["value"])
            print(f"  [Duration] Detected from {js_detected['source']}: {val:.2f}s")
            return val
    except Exception as e:
        print(f"  [Duration] JS eval notice: {e}")

    # 2. Static regex analysis of file content
    dur_match = re.search(r'DUR\s*=\s*([0-9.]+)', file_content)
    if dur_match:
        val = float(dur_match.group(1))
        print(f"  [Duration] Detected from static regex 'DUR = {val}': {val:.2f}s")
        return val

    # Match sum of data-d in HTML
    data_d_matches = re.findall(r'data-d\s*=\s*["\']([0-9.]+)["\']', file_content)
    if data_d_matches:
        val = sum(float(x) for x in data_d_matches)
        print(f"  [Duration] Detected from sum of data-d ({len(data_d_matches)} sections): {val:.2f}s")
        return val

    # Match reset condition like t >= 16.5
    reset_match = re.search(r't\s*>=\s*([0-9.]+)', file_content)
    if reset_match:
        val = float(reset_match.group(1))
        print(f"  [Duration] Detected from reset trigger 't >= {val}': {val:.2f}s")
        return val

    print(f"  [Duration] Using default duration: {default_duration:.2f}s")
    return default_duration


def get_audio_duration(audio_path: Path) -> float:
    """Get the duration of an audio file in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    res = subprocess.check_output(cmd).decode().strip()
    return float(res)


def convert_html_to_video(
    html_path: Path,
    output_mp4: Path = None,
    audio_path: Path = None,
    override_duration: float = None,
    width: int = 1080,
    height: int = 1920,
    fps: int = 60,
    crf: int = 18
) -> Path:
    """
    Converts a single HTML animation file into a high-quality vertical video (MP4)
    with synchronized, looping background audio.
    """
    html_path = Path(html_path).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if output_mp4 is None:
        output_mp4 = OUTPUT_DIR / f"{html_path.stem}.mp4"
    else:
        output_mp4 = Path(output_mp4).resolve()

    # Audio selection
    if audio_path is None:
        music_tracks = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav")) + list(MUSIC_DIR.glob("*.m4a"))
        if not music_tracks:
            raise RuntimeError(f"No audio files found in {MUSIC_DIR}!")
        audio_path = random.choice(music_tracks)
    else:
        audio_path = Path(audio_path).resolve()
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        file_content = f.read()

    print(f"\n{'=' * 60}")
    print(f"🎬 Processing: {html_path.name}")
    print(f"🎵 Audio: {audio_path.name}")
    print(f"📐 Target Resolution: {width}x{height} @ {fps}fps")

    temp_rec_dir = TEMP_DIR / f"rec_{int(time.time() * 1000)}"
    temp_rec_dir.mkdir(parents=True, exist_ok=True)

    # 1. Playwright Video Capture
    file_uri = html_path.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--disable-notifications"
            ]
        )
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            record_video_dir=str(temp_rec_dir),
            record_video_size={"width": width, "height": height}
        )
        page = context.new_page()
        page.goto(file_uri, wait_until="load")

        # Hide any UI replay/debug controls
        page.add_style_tag(content="""
            .ui, #rp, button, [onclick*="restart"], [onclick*="start"] {
                display: none !important;
                opacity: 0 !important;
                visibility: hidden !important;
            }
        """)

        # Determine duration
        if override_duration is not None and override_duration > 0:
            duration = float(override_duration)
            print(f"  [Duration] Using explicit override: {duration:.2f}s")
        else:
            duration = detect_duration(page, file_content)

        # Trigger clean restart from t=0
        page.evaluate("""() => {
            if (typeof restart === 'function') restart();
            else if (typeof start === 'function') start();
            else if (typeof reset === 'function') { reset(); if (typeof start === 'function') start(); }
        }""")

        print(f"⏺️  Recording animation for {duration:.2f}s...")
        time.sleep(duration)

        page.close()
        context.close()
        browser.close()

    # 2. Locate recorded raw video
    recorded_videos = list(temp_rec_dir.glob("*.webm"))
    if not recorded_videos:
        raise RuntimeError("Recording failed - no .webm file found in temp directory.")
    raw_video = recorded_videos[0]

    # 3. Audio analysis & loop handling
    audio_dur = get_audio_duration(audio_path)
    print(f"  [Audio] Track duration: {audio_dur:.2f}s | Video length: {duration:.2f}s")
    if audio_dur < duration:
        loop_times = math.ceil(duration / audio_dur)
        print(f"  🔁 Music is shorter than video ({audio_dur:.1f}s < {duration:.1f}s). Looping ~{loop_times} times.")
    else:
        print(f"  ✂️  Music is longer than video. Trimming to match exact {duration:.2f}s video duration.")

    # 4. FFmpeg Encoding with Looping Audio & Fade Out
    fade_start = max(0.0, duration - 0.5)
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-stream_loop", "-1",       # Loop audio indefinitely to prevent running out
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "192k",
        "-af", f"afade=t=out:st={fade_start:.2f}:d=0.5",
        "-t", str(duration),
        str(output_mp4)
    ]

    print("⚡ Merging audio & video via FFmpeg...")
    subprocess.check_call(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Clean up temp recording files
    for item in temp_rec_dir.glob("*"):
        item.unlink(missing_ok=True)
    temp_rec_dir.rmdir()

    # Extract high-clarity cover thumbnail from the near-end of the animation (duration - 1.2s)
    thumb_time = max(1.0, duration - 1.2)
    thumb_path = output_mp4.with_suffix(".jpg")
    thumb_cmd = [
        "ffmpeg", "-y",
        "-ss", f"{thumb_time:.2f}",
        "-i", str(output_mp4),
        "-frames:v", "1",
        "-update", "1",
        "-q:v", "2",
        str(thumb_path)
    ]
    try:
        subprocess.check_call(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"🖼️ Cover thumbnail generated: {thumb_path.name} (at {thumb_time:.2f}s)")
    except Exception as e:
        print(f"⚠️ Thumbnail generation notice: {e}")

    # Inject high-clarity completed diagram into Frame 0 of output_mp4 (2 frames / ~0.033s)
    if thumb_path.exists():
        try:
            temp_injected = output_mp4.with_name(f"{output_mp4.stem}_injected.mp4")
            inject_cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", "0.04", "-i", str(thumb_path),
                "-i", str(output_mp4),
                "-filter_complex", "[0:v]settb=AVTB,setpts=N/60/TB[v0]; [1:v]settb=AVTB,setpts=PTS-STARTPTS[v1]; [v0][v1]concat=n=2:v=1:a=0[outv]",
                "-map", "[outv]", "-map", "1:a:0?",
                "-c:v", "libx264", "-preset", "fast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps),
                "-c:a", "copy",
                str(temp_injected)
            ]
            subprocess.check_call(inject_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            temp_injected.replace(output_mp4)
            print(f"🖼️ Injected completed diagram into Frame 0 (thumbnail guaranteed at t=0s)")
        except Exception as ie:
            print(f"⚠️ Frame 0 injection notice: {ie}")

    size_mb = output_mp4.stat().st_size / (1024 * 1024)
    print(f"✅ Generated: {output_mp4.name} ({size_mb:.2f} MB)")
    print(f"{'=' * 60}\n")
    return output_mp4


def batch_convert(html_dir: Path = HTML_DIR, output_dir: Path = OUTPUT_DIR):
    """Batch convert all HTML files found in html_sources/"""
    html_files = sorted(list(html_dir.glob("*.html")))
    if not html_files:
        print(f"No HTML files found in {html_dir}")
        return

    print(f"Found {len(html_files)} HTML files to convert in {html_dir}")
    generated = []
    for h in html_files:
        try:
            out_file = convert_html_to_video(h)
            generated.append(out_file)
        except Exception as e:
            print(f"❌ Failed to convert {h.name}: {e}")

    print(f"\n🎉 Finished processing! {len(generated)}/{len(html_files)} videos created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert animated HTML files to 9:16 videos with background music.")
    parser.add_argument("--html", type=str, help="Path to single HTML file")
    parser.add_argument("--audio", type=str, help="Optional path to specific audio file")
    parser.add_argument("--duration", type=float, help="Optional override for animation duration (in seconds)")
    parser.add_argument("--all", action="store_true", help="Batch convert all HTML files in html_sources/")
    args = parser.parse_args()

    if args.all:
        batch_convert()
    elif args.html:
        convert_html_to_video(Path(args.html), audio_path=Path(args.audio) if args.audio else None, override_duration=args.duration)
    else:
        # Default: process first available HTML file
        candidates = sorted(list(HTML_DIR.glob("*.html")))
        if candidates:
            convert_html_to_video(candidates[0])
        else:
            print("No HTML files found in html_sources/. Use --html <path> or --all.")
