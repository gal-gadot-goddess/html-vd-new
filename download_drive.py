"""
Google Drive Asset Downloader for html-vd-new
Downloads HTML files and background audio tracks from Google Drive folders.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html_sources"
MUSIC_DIR = BASE_DIR / "music"

HTML_FOLDER_URL = "https://drive.google.com/drive/folders/19LQ5ofL1ScBKGiidAH7tNxM0xruG1TJ-"
MUSIC_FOLDER_URL = "https://drive.google.com/drive/folders/19zTCpkmKpZwUm8j8gnvfHZqVJqfwEz9I"

def download_folder(folder_url: str, output_path: Path):
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"\n📥 Downloading from Google Drive: {folder_url}")
    print(f"📁 Destination: {output_path}")
    
    cmd = [
        sys.executable, "-m", "gdown",
        folder_url,
        "-O", str(output_path),
        "--folder",
        "--remaining-ok"
    ]
    try:
        subprocess.check_call(cmd)
        print(f"✅ Download complete: {len(list(output_path.glob('*')))} files in {output_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Google Drive download warning: {e}")
        print("💡 Note: If you receive HTTP 401 or permission errors, ensure the Google Drive folder")
        print("   is shared as 'Anyone with the link can view' (Viewer).")

if __name__ == "__main__":
    download_folder(HTML_FOLDER_URL, HTML_DIR)
    download_folder(MUSIC_FOLDER_URL, MUSIC_DIR)
