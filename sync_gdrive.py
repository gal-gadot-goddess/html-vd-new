"""
Google Drive Asset Synchronizer for html-vd-new
Uses GOOGLE_SERVICE_ACCOUNT_KEY from environment variables to authenticate and download
assets from the user's private Google Drive folders.
"""

import os
import io
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

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html_sources"
MUSIC_DIR = BASE_DIR / "music"

HTML_FOLDER_ID = "19LQ5ofL1ScBKGiidAH7tNxM0xruG1TJ-"
MUSIC_FOLDER_ID = "19zTCpkmKpZwUm8j8gnvfHZqVJqfwEz9I"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_service():
    key_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_str:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable not found!")
    info = json.loads(key_str)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def download_file(service, file_id: str, file_name: str, target_dir: Path):
    target_path = target_dir / file_name
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(str(target_path), "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return target_path

def sync_folder(service, folder_id: str, target_dir: Path, clean_extra: bool = True):
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📂 Syncing Folder (ID: {folder_id}) -> {target_dir.name}/")
    
    q = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=q, fields="files(id, name, mimeType, size)").execute()
    files = results.get("files", [])
    print(f"Found {len(files)} file(s) in Drive folder.")

    drive_filenames = set()
    for f in files:
        fname = f["name"]
        fid = f["id"]
        drive_filenames.add(fname)
        out_file = download_file(service, fid, fname, target_dir)
        print(f"  ⬇️ Downloaded: {fname} ({out_file.stat().st_size} bytes)")

    if clean_extra:
        # Remove local files in target_dir that aren't in the Drive folder
        for local_file in target_dir.iterdir():
            if local_file.is_file() and local_file.name not in drive_filenames and local_file.name != ".gitkeep":
                print(f"  🗑️ Removing extra local file not in Drive: {local_file.name}")
                local_file.unlink()

    return files

def sync_all():
    service = get_service()
    htmls = sync_folder(service, HTML_FOLDER_ID, HTML_DIR, clean_extra=True)
    music = sync_folder(service, MUSIC_FOLDER_ID, MUSIC_DIR, clean_extra=False)
    print("\n✅ Sync complete!")
    print(f"  HTML files synced: {[f['name'] for f in htmls]}")
    print(f"  Music tracks synced: {len(music)}")

if __name__ == "__main__":
    sync_all()
