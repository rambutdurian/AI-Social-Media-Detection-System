"""
URL Downloader — Fixed version with cookie support
Supports: YouTube, TikTok, Instagram, Facebook
"""
import os
import uuid
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

def download_video_from_url(url: str, output_dir=None) -> tuple:
    """
    Download video from social media URL.
    Returns (local_file_path, video_title).
    Raises ValueError with user-friendly message on failure.

    Strategy:
      Attempt 1 — Chrome cookies (required for Instagram/private content)
      Attempt 2 — Edge cookies (fallback browser)
      Attempt 3 — No cookies (works for most public YouTube/TikTok)
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

    attempts = [
        {**base_opts, 'cookiesfrombrowser': ('chrome',)},
        {**base_opts, 'cookiesfrombrowser': ('edge',)},
        base_opts,
    ]

    for opts in attempts:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown') if info else 'Unknown'
                ext = info.get('ext', 'mp4') if info else 'mp4'
                final_path = os.path.join(TEMP_DIR, output_filename + '.' + ext)
                if os.path.exists(final_path):
                    return final_path, title
                # yt-dlp sometimes picks a different extension — scan for the file
                found = _find_downloaded_file(output_filename)
                if found:
                    return found, title

        except yt_dlp.utils.DownloadError as e:
            err = str(e).lower()
            # Immediately surface actionable errors — no point retrying
            if 'private' in err or 'login' in err or 'unavailable' in err:
                if 'instagram' in url.lower():
                    raise ValueError(
                        "Instagram requires login. Please open Chrome, log into Instagram, "
                        "then try again. Or upload the video file directly."
                    )
                raise ValueError(
                    "This video is private or unavailable. Please try a public video."
                )
            if 'copyright' in err or 'blocked' in err:
                raise ValueError(
                    "This video is blocked due to copyright restrictions. Try a different video."
                )
            # Cookie-related or generic error — try next attempt
        except Exception:
            pass  # Try next attempt

    raise ValueError(
        "Could not download this video after multiple attempts. "
        "Try uploading the video file directly instead."
    )
