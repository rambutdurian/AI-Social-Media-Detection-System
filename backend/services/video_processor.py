import cv2
import os
import uuid


def extract_frames(video_path, fps=1, max_frames=30):
    """
    Extract frames from video at specified fps rate.
    Returns (list of BGR numpy arrays, count of frames extracted).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = max(1, int(video_fps / fps))

    frames = []
    frame_idx = 0

    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()
    return frames, len(frames)


def save_temp_video(file_obj, extension='.mp4'):
    """Save uploaded Flask file object to temp directory. Returns path."""
    temp_dir = os.getenv('TEMP_VIDEO_DIR', './tmp_videos')
    os.makedirs(temp_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{extension}"
    path = os.path.join(temp_dir, filename)
    file_obj.save(path)
    return path


def delete_temp_video(path):
    """Delete temp video after processing. Always call in finally block."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"[Cleanup] Could not delete temp file {path}: {e}")
