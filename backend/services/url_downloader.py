"""
URL Downloader — YouTube cookie-based bypass + multi-platform support
Supports: YouTube, TikTok, Instagram, Facebook
"""
import os
import uuid
import tempfile
import yt_dlp

TEMP_DIR = os.getenv('TEMP_VIDEO_DIR', './tmp_videos')
os.makedirs(TEMP_DIR, exist_ok=True)

SUPPORTED_DOMAINS = [
    'youtube.com', 'youtu.be',
    'tiktok.com', 'vm.tiktok.com',
    'instagram.com',
    'facebook.com', 'fb.watch'
]

def is_supported_url(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in SUPPORTED_DOMAINS)

def get_platform(url: str) -> str:
    url_lower = url.lower()
    if 'instagram.com' in url_lower:
        return 'instagram'
    if 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower:
        return 'tiktok'
    if 'facebook.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    return 'youtube'

def _find_downloaded_file(output_filename: str) -> str | None:
    """Scan TEMP_DIR for a file starting with the given UUID."""
    for f in os.listdir(TEMP_DIR):
        if f.startswith(output_filename):
            return os.path.join(TEMP_DIR, f)
    return None

def _get_cookies_file() -> str | None:
    """
    Write YouTube cookies from YOUTUBE_COOKIES env var to a temp file.
    The env var should contain the full Netscape cookies.txt content.
    Returns path to temp file, or None if env var not set.
    """
    cookies_content = os.getenv('YOUTUBE_COOKIES', '').strip()
    if not cookies_content:
        return None
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name

def download_video_from_url(url: str, output_dir=None) -> tuple:
    """
    Download video from social media URL.
    Returns (local_file_path, video_title).
    Raises ValueError with user-friendly message on failure.

    YouTube strategy:
      - If YOUTUBE_COOKIES env var is set, use cookies (most reliable on server IPs)
      - Fallback: try android_vr, android, mediaconnect clients
    """
    if not is_supported_url(url):
        raise ValueError(
            "Unsupported URL. We support YouTube, TikTok, Instagram, and Facebook links."
        )

    output_filename = str(uuid.uuid4())
    output_template = os.path.join(TEMP_DIR, output_filename + '.%(ext)s')

    base_opts = {
        'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'retries': 3,
    }

    platform = get_platform(url)
    cookies_file = None

    if platform == 'youtube':
        cookies_file = _get_cookies_file()

        attempts = []

        # With cookies — most reliable on datacenter IPs (Render/AWS)
        if cookies_file:
            attempts.append({
                **base_opts,
                'cookiefile': cookies_file,
                'extractor_args': {'youtube': {'player_client': ['web']}},
            })
            attempts.append({
                **base_opts,
                'cookiefile': cookies_file,
            })

        # Without cookies — try clients that skip PO token check
        attempts += [
            {**base_opts, 'extractor_args': {'youtube': {'player_client': ['android_vr']}}},
            {**base_opts, 'extractor_args': {'youtube': {'player_client': ['android']}}},
            {**base_opts, 'extractor_args': {'youtube': {'player_client': ['mediaconnect']}}},
            {**base_opts, 'extractor_args': {'youtube': {'player_client': ['android_vr', 'android', 'mediaconnect']}}},
        ]
    else:
        attempts = [base_opts]

    last_err = None
    try:
        for opts in attempts:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown') if info else 'Unknown'
                    ext = info.get('ext', 'mp4') if info else 'mp4'
                    final_path = os.path.join(TEMP_DIR, output_filename + '.' + ext)
                    if os.path.exists(final_path):
                        return final_path, title
                    found = _find_downloaded_file(output_filename)
                    if found:
                        return found, title

            except yt_dlp.utils.DownloadError as e:
                err = str(e).lower()
                last_err = err
                if 'private' in err or 'login' in err or 'unavailable' in err or 'members only' in err:
                    if platform == 'instagram':
                        raise ValueError(
                            "Instagram requires login for this video. Upload the video file directly instead."
                        )
                    raise ValueError(
                        "This video is private or unavailable. Please try a public video."
                    )
                if 'copyright' in err or 'blocked' in err:
                    raise ValueError(
                        "This video is blocked due to copyright restrictions. Try a different video."
                    )
                if 'age' in err or 'confirm your age' in err:
                    raise ValueError(
                        "This video requires age verification. Upload the video file directly instead."
                    )
            except Exception as e:
                last_err = str(e).lower()

        raise ValueError(
            "YouTube is blocking our server from downloading this video. "
            "Please download the video and upload it as a file instead."
        )
    finally:
        # Clean up temp cookies file
        if cookies_file and os.path.exists(cookies_file):
            os.remove(cookies_file)
