import cv2
import numpy as np

# Cached at module level — loading takes ~30ms per call otherwise
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)


def check_brightness(frames):
    """
    Signal 1 — Brightness Consistency.
    Triggered if std > 60 (extreme, unnatural brightness swings across frames).
    Threshold raised to 60 so natural real-world lighting variation (outdoor/indoor scenes)
    does not false-positive; only rapid, large-scale flicker typical of low-quality AI video triggers.
    """
    brightness_values = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg = np.mean(gray)
        brightness_values.append(avg)

    avg_brightness = float(np.mean(brightness_values))
    std_brightness = float(np.std(brightness_values))
    triggered = bool(std_brightness > 60)

    if triggered:
        explanation = (
            f"Extreme brightness instability detected (std={round(std_brightness, 1)}) — "
            "rapid large-scale lighting swings are a hallmark of low-quality AI video generation."
        )
    else:
        explanation = f"Brightness appears natural (avg={round(avg_brightness, 0)}/255, std={round(std_brightness, 1)})."

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "avg_brightness": round(avg_brightness, 2),
        "std_brightness": round(std_brightness, 2),
        "explanation": explanation,
    }


def check_temporal(frames):
    """
    Signal 2 — Temporal Frame Difference.
    Triggered if mean_diff > 15 (abrupt jumps), < 2 (frozen/static),
    OR std_diff < 2 (robotically consistent motion — deepfake artifact).
    """
    if len(frames) < 2:
        return {
            "score": 0,
            "triggered": False,
            "mean_diff": 0,
            "std_diff": 0,
            "explanation": "Not enough frames for temporal analysis.",
        }

    diffs = []
    for i in range(1, len(frames)):
        prev = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY).astype(float)
        curr = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY).astype(float)
        diff = float(np.mean(np.abs(curr - prev)))
        diffs.append(diff)

    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs))
    # Threshold: mean_diff > 30 = extreme abrupt jumps (scene cuts or severe GAN artifacts).
    # Threshold: mean_diff < 1.5 = near-frozen / looped frames.
    # Upper bound raised from 15 → 30 so real videos with natural movement (gestures,
    # walking, camera pans) do not false-positive.
    triggered = bool(mean_diff > 30 or mean_diff < 1.5)

    if triggered:
        if mean_diff < 1.5:
            explanation = (
                f"Near-frozen frames detected (diff={round(mean_diff, 1)}) — "
                "static or looped AI video artifact."
            )
        else:
            explanation = (
                f"Extreme abrupt frame transitions (diff={round(mean_diff, 1)}) — "
                "severe GAN rendering artifact or unnatural scene jump."
            )
    else:
        explanation = f"Frame transitions appear natural (diff={round(mean_diff, 1)}, variance={round(std_diff, 1)})."

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "mean_diff": round(mean_diff, 2),
        "std_diff": round(std_diff, 2),
        "explanation": explanation,
    }


def check_blur(frames):
    """
    Signal 3 — Full-Frame Over-Sharpness Detection.

    Counterintuitively, many deepfake videos are SHARPER than authentic phone footage.
    GAN-generated faces are rendered at pixel-perfect clarity, whereas real videos
    shot on consumer devices have natural softness from autofocus, motion, and sensor noise.

    Triggered if avg Laplacian variance > 200 (unnaturally crisp — GAN output artifact).
    Real phone videos typically show variance 15–120.
    High-quality GAN output and sharp deepfake composites show variance 200+.
    """
    variances = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        variances.append(lap_var)

    avg_variance = float(np.mean(variances))
    triggered = bool(avg_variance > 200)

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "avg_variance": round(avg_variance, 2),
        "explanation": (
            f"Unnaturally high image sharpness (variance={round(avg_variance, 0)}) — "
            "GAN-generated content is rendered at pixel-perfect clarity, unlike natural camera footage."
            if triggered else
            f"Image sharpness appears consistent with natural camera footage (variance={round(avg_variance, 0)})."
        ),
    }


def check_facial_stability(frames):
    """
    Signal 4 — Facial Detection Stability.
    Triggered if std deviation of face count > 1.5.
    Threshold raised from 0.5 → 1.5 so natural head turns, partial off-frame moments,
    and normal camera movement in real videos do not false-positive. Only severe,
    rapid face flickering (multiple faces appearing/disappearing) triggers.
    """
    face_counts = []

    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        face_counts.append(len(faces))

    avg_faces = float(np.mean(face_counts)) if face_counts else 0.0
    std_faces = float(np.std(face_counts)) if face_counts else 0.0
    triggered = bool(std_faces > 1.5)

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "avg_faces": round(avg_faces, 2),
        "std_faces": round(std_faces, 3),
        "explanation": (
            f"Facial inconsistency detected (variation={round(std_faces, 2)}) — "
            "face presence fluctuates across frames, a common deepfake artifact."
            if triggered else
            f"Face detection stable across frames (avg={round(avg_faces, 1)}, variation={round(std_faces, 2)})."
        ),
    }
