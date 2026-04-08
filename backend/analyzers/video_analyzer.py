# analyzers/video_analyzer.py
# Optimized for speed: analyzes 15 frames instead of 30,
# and DeepFace is skipped by default (add ENABLE_DEEPFACE=true to .env to enable).

import cv2
import numpy as np
import os

CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Set ENABLE_DEEPFACE=true in your .env file to enable DeepFace (slower but more accurate)
ENABLE_DEEPFACE = os.environ.get('ENABLE_DEEPFACE', 'false').lower() == 'true'


def extract_frames(video_path: str, max_frames: int = 15):
    """
    Extracts up to 15 frames from a video at regular intervals.
    15 frames is enough for reliable detection and much faster than 30.
    """
    cap    = cv2.VideoCapture(video_path)
    frames = []

    if not cap.isOpened():
        raise ValueError(f'Cannot open video: {video_path}')

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = float(cap.get(cv2.CAP_PROP_FPS) or 25)
    duration_s   = total_frames / fps
    interval     = max(1, int(total_frames / max_frames))

    frame_idx = 0
    while len(frames) < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        frame_idx += interval

    cap.release()
    return frames, {
        'total_frames': int(total_frames),
        'fps':          round(fps, 2),
        'duration_s':   round(duration_s, 1)
    }


def signal_brightness(frames: list) -> dict:
    """SIGNAL 1: Unnaturally uniform brightness = AI indicator."""
    values        = [float(np.mean(f)) for f in frames]
    avg           = float(np.mean(values))
    triggered     = bool(avg > 140)
    return {
        'triggered':      triggered,
        'score':          25 if triggered else 0,
        'avg_brightness': round(avg, 2),
        'explanation': (
            f'Unnatural brightness (avg={avg:.0f}/255) — AI generators often produce over-lit frames.'
            if triggered else
            f'Brightness appears natural (avg={avg:.0f}/255).'
        )
    }


def signal_temporal(frames: list) -> dict:
    """SIGNAL 2: Abrupt pixel changes between frames = AI motion artifacts."""
    if len(frames) < 2:
        return {'triggered': False, 'score': 0, 'explanation': 'Not enough frames'}

    diffs     = [float(np.mean(cv2.absdiff(frames[i], frames[i+1]))) for i in range(len(frames)-1)]
    mean_diff = float(np.mean(diffs))
    triggered = bool(mean_diff > 20)
    return {
        'triggered':   triggered,
        'score':       25 if triggered else 0,
        'mean_diff':   round(mean_diff, 2),
        'explanation': (
            f'Temporal distortion detected (diff={mean_diff:.1f}) — unnatural motion between frames.'
            if triggered else
            f'Frame transitions appear natural (diff={mean_diff:.1f}).'
        )
    }


def signal_blur(frames: list) -> dict:
    """SIGNAL 3: Unnaturally smooth faces = deepfake indicator (Laplacian method)."""
    scores    = [float(cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()) for f in frames]
    avg_var   = float(np.mean(scores))
    triggered = bool(avg_var < 100)
    return {
        'triggered':    triggered,
        'score':        25 if triggered else 0,
        'avg_variance': round(avg_var, 2),
        'explanation':  (
            f'Unnatural smoothing (variance={avg_var:.0f}) — AI faces lack natural skin texture.'
            if triggered else
            f'Image sharpness appears natural (variance={avg_var:.0f}).'
        )
    }


def signal_face_stability(frames: list) -> dict:
    """SIGNAL 4: Inconsistent face detection = deepfake generator struggling."""
    cascade     = cv2.CascadeClassifier(CASCADE_PATH)
    face_counts = []

    for frame in frames:
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
        face_counts.append(int(len(faces)))

    if not face_counts:
        return {'triggered': False, 'score': 0, 'explanation': 'No frames to analyze'}

    std       = float(np.std(face_counts))
    avg       = float(np.mean(face_counts))
    triggered = bool(std > 0.5)
    return {
        'triggered':   triggered,
        'score':       25 if triggered else 0,
        'std_faces':   round(std, 3),
        'avg_faces':   round(avg, 2),
        'explanation': (
            f'Facial inconsistency detected (variation={std:.2f}) — face presence fluctuates across frames.'
            if triggered else
            f'Face detection stable across frames (variation={std:.2f}).'
        )
    }


def run_deepface_analysis(frames: list) -> dict:
    """
    OPTIONAL: DeepFace deep learning analysis.
    Only runs if ENABLE_DEEPFACE=true in .env — it adds ~10s per analysis.
    """
    if not ENABLE_DEEPFACE:
        return {'available': False, 'reason': 'DeepFace disabled (set ENABLE_DEEPFACE=true to enable)'}

    try:
        from deepface import DeepFace
        import tempfile

        anomaly_count = 0
        analyzed      = 0

        for frame in frames[:3]:   # Only check 3 frames to stay fast
            try:
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                    cv2.imwrite(f.name, frame)
                    temp_path = f.name
                result = DeepFace.analyze(temp_path, actions=['emotion'],
                                          enforce_detection=False, silent=True)
                os.unlink(temp_path)
                if isinstance(result, list): result = result[0]
                if result.get('dominant_emotion', '') == 'neutral':
                    anomaly_count += 1
                analyzed += 1
            except Exception:
                continue

        if analyzed == 0:
            return {'available': False, 'reason': 'No faces detected'}

        ratio       = float(anomaly_count / analyzed)
        bonus_score = int(ratio * 20)
        return {
            'available':     True,
            'bonus_score':   bonus_score,
            'anomaly_ratio': round(ratio, 2),
            'explanation':   f'DeepFace: {anomaly_count}/{analyzed} frames showed neutral/unnatural expressions.'
        }

    except ImportError:
        return {'available': False, 'reason': 'DeepFace not installed'}
    except Exception as e:
        return {'available': False, 'reason': str(e)}


def analyze_video(video_path: str) -> dict:
    """MAIN FUNCTION: runs 4 core signals + optional DeepFace."""
    flags, signals = [], {}

    try:
        frames, meta = extract_frames(video_path, max_frames=15)
    except Exception as e:
        return {'score': 50, 'flags': [f'Could not read video: {e}'], 'details': {}}

    if len(frames) < 3:
        return {'score': 30, 'flags': ['Video too short to analyze'], 'details': {}}

    s1 = signal_brightness(frames);     signals['brightness']     = s1
    s2 = signal_temporal(frames);       signals['temporal']       = s2
    s3 = signal_blur(frames);           signals['blur']           = s3
    s4 = signal_face_stability(frames); signals['face_stability'] = s4

    composite = int(s1['score'] + s2['score'] + s3['score'] + s4['score'])

    for sig in [s1, s2, s3, s4]:
        if sig.get('triggered'):
            flags.append(sig['explanation'])

    df = run_deepface_analysis(frames)
    signals['deepface'] = df
    if df.get('available') and df.get('bonus_score', 0) > 0:
        composite += df['bonus_score']
        flags.append(df['explanation'])

    composite  = int(min(composite, 100))
    confidence = int(min(95, 50 + composite // 2))

    if not flags:
        flags.append('No strong deepfake indicators detected in this video.')

    return {
        'score':           composite,
        'confidence':      confidence,
        'flags':           flags,
        'signals':         signals,
        'details':         meta,
        'frames_analyzed': int(len(frames))
    }
