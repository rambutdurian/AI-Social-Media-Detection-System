"""
URL Downloader — YouTube Android client bypass + multi-platform support
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

    YouTube strategy (server has no browser, so skip cookies):
      Attempt 1 — Android client (bypasses YouTube bot detection)
      Attempt 2 — Web client fallback

    Other platforms (Instagram, TikTok, Facebook):
      Attempt 1 — no cookies (works for public content)
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

    if platform == 'youtube':
        # YouTube requires PO tokens on server IPs in 2025.
        # tv_embedded client bypasses this — it's designed for embedded players
        # and skips PO token verification for public videos.
        attempts = [
            {
                **base_opts,
                'extractor_args': {'youtube': {'player_client': ['tv_embedded']}},
            },
            {
                **base_opts,
                'extractor_args': {'youtube': {'player_client': ['android_embedded']}},
            },
            {
                **base_opts,
                'extractor_args': {'youtube': {'player_client': ['mweb']}},
            },
        ]
    else:
        # Instagram, TikTok, Facebook — no-cookie attempt works for public content
        attempts = [base_opts]

    last_err = None
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
            last_err = err
            # Surface actionable errors immediately — no point retrying
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
            # Generic error — try next attempt
        except Exception as e:
            last_err = str(e).lower()

    raise ValueError(
        "Could not download this video. "
        "For YouTube, try a different public video or upload the file directly."
    )
