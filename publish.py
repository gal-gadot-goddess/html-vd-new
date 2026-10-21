"""
Social Media Publishing Module for html-vd-new
Publishes rendered vertical videos to Facebook, Instagram, and Threads.
"""

import os
import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

try:
    from upload.upload_facebook import upload_to_facebook
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
except ImportError as e:
    print(f"⚠️  Import warning in publish.py: {e}")

def publish_video(video_path: Path, metadata: dict) -> dict:
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    title = metadata.get("title", video_path.stem)
    hashtags = metadata.get("hashtags", ["#Tech", "#Programming"])
    if isinstance(hashtags, list):
        hashtags_str = " ".join(hashtags)
    else:
        hashtags_str = str(hashtags)

    ig_caption = metadata.get("ig_caption", f"{title}\n\n{hashtags_str}")
    fb_caption = metadata.get("fb_caption", f"{title}\n\n{hashtags_str}")
    threads_caption = metadata.get("threads_caption", f"{title}\n\n{hashtags_str}")

    results = {}

    print(f"\n{'=' * 60}")
    print(f"🚀 PUBLISHING VIDEO: {video_path.name}")
    print(f"📌 Title: {title}")
    print(f"{'=' * 60}")

    # 1. Instagram Reels
    try:
        print("\n📸 [Instagram] Publishing Reel...")
        res_ig = upload_to_instagram(str(video_path), ig_caption)
        results["instagram"] = res_ig
        print("✅ [Instagram] Published successfully!")
    except Exception as e:
        print(f"⚠️  [Instagram] Failed: {e}")
        results["instagram"] = {"status": "error", "error": str(e)}

    # 2. Facebook Reels / Page
    try:
        print("\n📘 [Facebook] Publishing Reel...")
        res_fb = upload_to_facebook(str(video_path), fb_caption, title=title[:100])
        results["facebook"] = res_fb
        print("✅ [Facebook] Published successfully!")
    except Exception as e:
        print(f"⚠️  [Facebook] Failed: {e}")
        results["facebook"] = {"status": "error", "error": str(e)}

    # 3. Threads
    try:
        print("\n🧵 [Threads] Publishing Video Post...")
        res_threads = upload_to_threads(str(video_path), threads_caption)
        results["threads"] = res_threads
        print("✅ [Threads] Published successfully!")
    except Exception as e:
        print(f"⚠️  [Threads] Failed: {e}")
        results["threads"] = {"status": "error", "error": str(e)}

    print(f"\n{'=' * 60}")
    print("🏁 Publishing run finished.")
    print(f"{'=' * 60}\n")
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python publish.py <video_path> [metadata_json_path]")
        sys.exit(1)

    vpath = Path(sys.argv[1])
    mdata = {}
    if len(sys.argv) > 2 and Path(sys.argv[2]).exists():
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            mdata = json.load(f)

    publish_video(vpath, mdata)
