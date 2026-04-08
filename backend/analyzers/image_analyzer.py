# analyzers/image_analyzer.py

import cv2
import numpy as np
from PIL import Image as PILImage
import os

CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'


def load_image(image_path: str):
    """Loads an image safely using both OpenCV and Pillow."""
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        pil_img = PILImage.open(image_path).convert('RGB')
        img_cv  = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    else:
        pil_img = PILImage.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    return img_cv, pil_img


def check_blur_sharpness(img_cv) -> dict:
    """Checks image sharpness using Laplacian variance. Low variance = AI-smoothed."""
    gray      = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    variance  = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    triggered = bool(variance < 80)
    return {
        'triggered':   triggered,
        'score':       20 if triggered else 0,
        'variance':    round(variance, 2),
        'explanation': (
            f'Unnatural smoothing in image (sharpness={variance:.0f}). '
            f'AI-generated images lack natural texture at skin and hair edges.'
            if triggered else
            f'Image sharpness appears natural (variance={variance:.0f}).'
        )
    }


def check_noise_pattern(img_cv) -> dict:
    """Checks dark-area noise level. AI images are suspiciously clean."""
    gray        = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    dark_mask   = gray < 50
    dark_pixels = gray[dark_mask]

    if len(dark_pixels) < 100:
        return {'triggered': False, 'score': 0, 'explanation': 'Not enough dark areas for noise analysis'}

    noise_std = float(np.std(dark_pixels.astype(float)))
    triggered = bool(noise_std < 2.0)
    return {
        'triggered':   triggered,
        'score':       15 if triggered else 0,
        'noise_std':   round(noise_std, 3),
        'explanation': (
            f'Suspiciously low image noise (std={noise_std:.2f}). '
            f'Real camera sensors produce natural noise — AI images are artificially clean.'
            if triggered else
            f'Noise pattern within natural range (std={noise_std:.2f}).'
        )
    }


def check_color_balance(img_cv) -> dict:
    """Checks RGB channel balance. AI generators often shift channels unnaturally."""
    channels       = cv2.split(img_cv)
    means          = [float(np.mean(ch)) for ch in channels]
    channel_spread = float(max(means) - min(means))
    triggered      = bool(channel_spread > 40)
    return {
        'triggered':     triggered,
        'score':         10 if triggered else 0,
        'channel_means': [round(m, 1) for m in means],
        'spread':        round(channel_spread, 2),
        'explanation': (
            f'Unusual color channel imbalance detected (spread={channel_spread:.0f}). '
            f'Indicates possible color manipulation or AI generation artifacts.'
            if triggered else
            f'Color balance appears natural.'
        )
    }


def check_face_presence(img_cv) -> dict:
    """Detects human faces using OpenCV Haar Cascade."""
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    gray         = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    faces        = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
    face_count   = int(len(faces))
    return {
        'face_count':  face_count,
        'faces_found': bool(face_count > 0),
        'face_boxes':  [{'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)} for x, y, w, h in faces]
    }


def check_symmetry(img_cv) -> dict:
    """Checks left-right facial symmetry. AI faces often have subtle asymmetry."""
    gray  = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w  = gray.shape
    left  = gray[:, :w // 2]
    right = cv2.flip(gray[:, w // 2:], 1)
    min_w = min(left.shape[1], right.shape[1])
    diff  = float(np.mean(np.abs(
        left[:, :min_w].astype(float) - right[:, :min_w].astype(float)
    )))
    triggered = bool(diff > 30)
    return {
        'triggered':   triggered,
        'score':       15 if triggered else 0,
        'asymmetry':   round(diff, 2),
        'explanation': (
            f'High facial asymmetry detected (score={diff:.0f}). '
            f'Deepfake faces often have unnatural left-right asymmetry.'
            if triggered else
            f'Facial symmetry appears within normal range.'
        )
    }


def run_deepface_image(img_cv) -> dict:
    """Optional DeepFace deep learning analysis. Skipped gracefully if not installed."""
    try:
        from deepface import DeepFace
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            cv2.imwrite(f.name, img_cv)
            temp_path = f.name

        result = DeepFace.analyze(
            temp_path,
            actions=['emotion', 'age'],
            enforce_detection=False,
            silent=True
        )
        os.unlink(temp_path)

        if isinstance(result, list):
            result = result[0]

        neutral = bool(result.get('dominant_emotion', '') == 'neutral')
        return {
            'available':        True,
            'bonus_score':      15 if neutral else 0,
            'dominant_emotion': str(result.get('dominant_emotion', 'unknown')),
            'age_estimate':     int(result.get('age', 0)) if result.get('age') else None,
            'explanation': (
                'DeepFace: face shows neutral/flat expression — AI-generated faces often lack natural emotion.'
                if neutral else
                f'DeepFace: detected {result.get("dominant_emotion", "unknown")} expression (natural).'
            )
        }
    except ImportError:
        return {'available': False, 'reason': 'DeepFace not installed'}
    except Exception as e:
        return {'available': False, 'reason': str(e)}


def analyze_image(image_path: str) -> dict:
    """MAIN FUNCTION: runs all image checks, returns score + flags + details."""
    flags, signals = [], {}

    try:
        img_cv, pil_img = load_image(image_path)
    except Exception as e:
        return {'score': 30, 'flags': [f'Could not load image: {e}'], 'details': {}}

    h, w    = img_cv.shape[:2]
    details = {
        'width':      int(w),
        'height':     int(h),
        'megapixels': round(float(w * h) / 1_000_000, 2)
    }

    if w < 64 or h < 64:
        return {'score': 20, 'flags': ['Image too small to analyze'], 'details': details}

    s_blur  = check_blur_sharpness(img_cv);  signals['blur']     = s_blur
    s_noise = check_noise_pattern(img_cv);   signals['noise']    = s_noise
    s_color = check_color_balance(img_cv);   signals['color']    = s_color
    s_face  = check_face_presence(img_cv);   signals['faces']    = s_face
    s_sym   = check_symmetry(img_cv);        signals['symmetry'] = s_sym

    if not s_face['faces_found']:
        s_sym = {'triggered': False, 'score': 0, 'explanation': 'No face detected — symmetry check skipped'}
        signals['symmetry'] = s_sym

    composite       = int(s_blur['score'] + s_noise['score'] + s_color['score'] + s_sym['score'])
    triggered_count = sum(1 for s in [s_blur, s_noise, s_color, s_sym] if s.get('triggered'))

    if s_face['faces_found'] and triggered_count >= 2:
        composite += 20
        flags.append(f'Human face detected alongside {triggered_count} AI-generation signals — high deepfake risk')

    for sig in [s_blur, s_noise, s_color, s_sym]:
        if sig.get('triggered'):
            flags.append(sig['explanation'])

    df = run_deepface_image(img_cv)
    signals['deepface'] = df
    if df.get('available') and df.get('bonus_score', 0) > 0:
        composite += df['bonus_score']
        flags.append(df['explanation'])

    composite  = int(min(composite, 100))
    confidence = int(min(95, 50 + composite // 2))

    if not flags:
        flags.append('No strong AI-generation indicators detected in this image.')

    return {
        'score':          composite,
        'confidence':     confidence,
        'flags':          flags,
        'signals':        signals,
        'details':        details,
        'faces_detected': int(s_face['face_count'])
    }
