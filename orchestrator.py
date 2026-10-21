"""
Automated Pipeline Orchestrator for html-vd-new
Coordinates: Google Drive Sync -> Video Render -> AI Metadata -> Social Media Upload
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html_sources"
OUTPUT_DIR = BASE_DIR / "output"
HISTORY_FILE = BASE_DIR / "history.json"
METADATA_FILE = BASE_DIR / "metadata.json"

from sync_gdrive import sync_all
from converter import convert_html_to_video
from generate_metadata import clean_filename_to_title, generate_ai_metadata
from publish import publish_video

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(history: list):
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")

def run_pipeline(publish: bool = True, force: bool = False):
    print("\n" + "=" * 60)
    print("🎬 STARTING AUTOMATION CYCLE")
    print("=" * 60)

    # 1. Sync from Google Drive if Service Account is configured
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY"):
        try:
            print("\n☁️ [Step 1] Syncing assets from Google Drive...")
            sync_all()
        except Exception as e:
            print(f"⚠️ Google Drive sync warning: {e}")
    else:
        print("\nℹ️ [Step 1] GOOGLE_SERVICE_ACCOUNT_KEY not set. Using local html_sources/ assets.")

    # 2. Select HTML file to process
    html_files = sorted(list(HTML_DIR.glob("*.html")))
    if not html_files:
        print("❌ No HTML files found in html_sources/!")
        return

    history = load_history()
    processed_names = {entry.get("file") for entry in history}

    # Find unrendered file, or pick the first if forcing/all done
    target_file = None
    for h in html_files:
        if force or h.name not in processed_names:
            target_file = h
            break

    if not target_file:
        print("🎉 All HTML files have already been processed! Using latest file for this run.")
        target_file = html_files[-1]

    topic_title = clean_filename_to_title(target_file.name)
    print(f"\n🎯 [Step 2] Selected Topic: '{topic_title}' ({target_file.name})")

    # 3. Generate AI Metadata with Pollinations AI
    print("\n🧠 [Step 3] Generating AI metadata via Pollinations AI...")
    metadata = generate_ai_metadata(topic_title)
    METADATA_FILE.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Metadata saved to metadata.json (Title: '{metadata.get('title')}')")

    # 4. Render 1080p 60FPS Video with Looping Background Audio
    print("\n📹 [Step 4] Rendering vertical video (1080x1920 @ 60FPS)...")
    video_path = convert_html_to_video(target_file)
    print(f"✅ Video render complete: {video_path.name}")

    # 5. Upload to Facebook and Instagram
    if publish:
        print("\n🌐 [Step 5] Publishing to social media platforms...")
        publish_res = publish_video(video_path, metadata)
    else:
        print("\nℹ️ [Step 5] Skipping social publish (run with --publish to upload).")
        publish_res = {"status": "skipped"}

    # 6. Update History
    history.append({
        "file": target_file.name,
        "title": metadata.get("title"),
        "video": video_path.name,
        "publish": publish_res
    })
    save_history(history)

    print("\n" + "=" * 60)
    print("✅ CYCLE COMPLETED SUCCESSFULLY!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Automation Pipeline Orchestrator")
    parser.add_argument("--publish", action="store_true", help="Publish generated video to social media")
    parser.add_argument("--force", action="store_true", help="Force process even if already in history")
    args = parser.parse_args()

    run_pipeline(publish=args.publish, force=args.force)
