"""
Facebook Reels & Story Upload
Uploads Reels and Stories to Facebook Pages.
Supports multiple pages configured via env or dedicated target list (kreggscode and kreggscode coding).
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Known pages associated with kreggscode
KREGGS_PAGES = [
    {
        'id': '503243842882427',
        'name': 'kreggscode',
        'token': 'EAAM2KQECaR0BSQzUPZChfwgdNZAVwZCnDpUofmFIHZCzkPFWy5fgMVMl5d1EfTOfmHiafdZA6Q9ZBUuJav5DybyRffyqB9CM0lTimZB38CbZAQwpypHVxw80VOAXQs7I93tTsREj9TrmPGrU9eDC8uElHSBwtKAuYxkRXCFtt8ZC0qrOnLXZBCSD1UmntDXq5wjVV72DZA0zieQaZATnihgBmiXqQvf8'
    },
    {
        'id': '106890212286933',
        'name': 'kreggscode coding',
        'token': 'EAAM2KQECaR0BSaIESZAqKEOZAWlV6V855jFTcAP7ypNifLCLz0auVRgTgsEDyW31ywIobovSda9rtWKhDkv55hLYlx7bQoVmalrVS8aVfYsRsBwExEm33aEdhXhpBOKvcquHQ6YyrZBtZApkYi5Gvt8WDEWQ73vH7mfbGEmgidG1hBCFdTmnElsEEcNLjEZBt9SJEUgjaKs2EQDdYXr3PgqUZD'
    }
]

def get_target_pages():
    """
    Returns list of (page_id, page_token, page_name).
    Prioritizes explicit environment variables if set, and falls back to / includes known kreggscode pages.
    """
    env_page_id = os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID')
    env_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN')

    targets = []
    seen = set()

    if env_page_id and env_token:
        targets.append({'id': env_page_id, 'token': env_token, 'name': 'Env Page'})
        seen.add(env_page_id)

    # Always ensure both kreggscode pages are included
    for page in KREGGS_PAGES:
        if page['id'] not in seen:
            targets.append(page)
            seen.add(page['id'])

    return targets

def upload_single_page(video_path, description, title, thumbnail_path, page):
    page_id = page['id']
    access_token = page['token']
    page_name = page.get('name', page_id)

    print(f"\n[facebook] 🚀 Uploading Reel to '{page_name}' (ID: {page_id})...")
    url = f"https://graph.facebook.com/v21.0/{page_id}/videos"

    with open(video_path, 'rb') as video:
        files = {'file': video}
        thumb_file = None
        if thumbnail_path and os.path.exists(thumbnail_path):
            thumb_file = open(thumbnail_path, 'rb')
            files['thumb'] = thumb_file

        data = {
            'access_token': access_token,
            'description': description,
            'title': title,
            'is_explicit_share': True,
            'is_reel': True
        }

        try:
            response = requests.post(url, files=files, data=data, timeout=300)
            if thumb_file:
                thumb_file.close()

            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                print(f"[facebook] ✅ SUCCESS on '{page_name}'! Video ID: {video_id}")
                return {'id': video_id, 'page': page_name, 'status': 'success'}
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', response.text)
                print(f"[facebook] ❌ Failed on '{page_name}': {error_msg}")
                return {'status': 'failed', 'page': page_name, 'error': error_msg}
        except Exception as e:
            if thumb_file:
                thumb_file.close()
            print(f"[facebook] ❌ Exception on '{page_name}': {e}")
            return {'status': 'failed', 'page': page_name, 'error': str(e)}

def upload_to_facebook(video_path, description, title="Algorithm Visualization", thumbnail_path=None, thumb_path=None):
    """
    Upload video to Facebook Pages as a Reel.
    """
    active_thumb = thumbnail_path or thumb_path

    print("\n" + "=" * 60)
    print("📘 FACEBOOK REEL UPLOAD STARTING")
    print("=" * 60)

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[facebook] {error_msg}")
        raise FileNotFoundError(error_msg)

    targets = get_target_pages()
    print(f"[facebook] Target Facebook Pages: {[t['name'] for t in targets]}")

    results = []
    for page in targets:
        res = upload_single_page(video_path, description, title, active_thumb, page)
        results.append(res)

    print("=" * 60)
    return results

def upload_to_facebook_story(video_path):
    """
    Upload video to Facebook Page as a Story across target pages.
    """
    print("\n" + "=" * 60)
    print("📘 FACEBOOK STORY UPLOAD STARTING")
    print("=" * 60)

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"[facebook] Video not found: {video_path}")

    targets = get_target_pages()
    file_size = video_path_obj.stat().st_size

    results = []
    for page in targets:
        page_id = page['id']
        access_token = page['token']
        page_name = page.get('name', page_id)
        print(f"\n[facebook] Uploading Story to '{page_name}' (ID: {page_id})...")

        try:
            init_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
            init_data = {
                'access_token': access_token,
                'upload_phase': 'start',
                'file_size': file_size
            }
            res_init = requests.post(init_url, data=init_data, timeout=30)
            if res_init.status_code != 200:
                print(f"[facebook] ❌ Init Error on '{page_name}': {res_init.text}")
                continue

            init_json = res_init.json()
            upload_url = init_json.get('upload_url')
            video_id = init_json.get('video_id')
            upload_session_id = init_json.get('upload_session_id')

            if upload_url:
                headers = {
                    'Authorization': f'OAuth {access_token}',
                    'offset': '0',
                    'file_size': str(file_size),
                    'Content-Type': 'application/octet-stream'
                }
                with open(video_path, 'rb') as f:
                    requests.post(upload_url, data=f, headers=headers, timeout=600)

                publish_data = {
                    'access_token': access_token,
                    'upload_phase': 'finish',
                    'video_id': video_id
                }
                res_finish = requests.post(init_url, data=publish_data, timeout=60)
            else:
                transfer_url = f"https://graph.facebook.com/v21.0/{page_id}/video_stories"
                with open(video_path, 'rb') as f:
                    files = {'video_file_chunk': f}
                    transfer_data = {
                        'access_token': access_token,
                        'upload_phase': 'transfer',
                        'start_offset': 0,
                        'upload_session_id': upload_session_id,
                        'video_id': video_id
                    }
                    requests.post(transfer_url, data=transfer_data, files=files, timeout=600)

                finish_data = {
                    'access_token': access_token,
                    'upload_phase': 'finish',
                    'upload_session_id': upload_session_id,
                    'video_id': video_id
                }
                res_finish = requests.post(transfer_url, data=finish_data, timeout=60)

            if res_finish.status_code == 200 or res_finish.json().get('success'):
                print(f"[facebook] ✅ SUCCESS Story on '{page_name}'! Video ID: {video_id}")
                results.append({'id': video_id, 'page': page_name, 'status': 'success'})
            else:
                print(f"[facebook] ❌ Finish Story Error on '{page_name}': {res_finish.text}")
        except Exception as e:
            print(f"[facebook] ❌ Story failed on '{page_name}': {e}")

    print("=" * 60)
    return results
