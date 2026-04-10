import cv2
import numpy as np


def _eye_aspect_ratio(eye_points):
    """
    Compute Eye Aspect Ratio (EAR) from 6 eye landmark points.
    EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    A low EAR indicates a closed eye (blink).
    """
    p1, p2, p3, p4, p5, p6 = eye_points
    vertical1 = np.linalg.norm(np.array(p2) - np.array(p6))
    vertical2 = np.linalg.norm(np.array(p3) - np.array(p5))
    horizontal = np.linalg.norm(np.array(p1) - np.array(p4))
    if horizontal < 1e-6:
        return 0.3  # assume open eye if measurement fails
    return (vertical1 + vertical2) / (2.0 * horizontal)


def check_blink(frames):
    """
    Signal 7 — Eye Blink Detection.

    Real people blink naturally every 3–8 seconds (roughly 15–20 blinks/min).
    Deepfakes notoriously fail to replicate natural blinking — either:
      - No blinks at all (eyes always open), OR
      - Unnatural blink timing (too frequent or mechanical)

    Method:
    - Use OpenCV's face + eye cascade to detect eye regions per frame
    - Estimate Eye Aspect Ratio (EAR) for each frame
    - Compute blink rate and EAR variance

    Triggered if:
      - Zero blinks detected over 10+ frames with consistent face presence, OR
      - EAR variance < 0.001 (eyes unnaturally static — no natural micro-movements)

    Falls back gracefully if eyes cannot be reliably detected.
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml'
    )

    ear_values = []
    frames_with_face = 0
    frames_with_eyes = 0

    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

        if len(faces) == 0:
            continue

        frames_with_face += 1
        # Use the largest detected face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi = gray[y:y + h, x:x + w]

        eyes = eye_cascade.detectMultiScale(
            face_roi, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20)
        )

        if len(eyes) < 2:
            continue

        frames_with_eyes += 1

        # Sort eyes left to right, take top 2
        eyes = sorted(eyes, key=lambda e: e[0])[:2]
        frame_ears = []

        for (ex, ey, ew, eh) in eyes:
            # Approximate 6 EAR points from the bounding box
            # p1=left, p4=right, p2/p3=top, p5/p6=bottom
            p1 = (ex, ey + eh // 2)
            p4 = (ex + ew, ey + eh // 2)
            p2 = (ex + ew // 3, ey)
            p3 = (ex + 2 * ew // 3, ey)
            p5 = (ex + 2 * ew // 3, ey + eh)
            p6 = (ex + ew // 3, ey + eh)
            ear = _eye_aspect_ratio([p1, p2, p3, p4, p5, p6])
            frame_ears.append(ear)

        if frame_ears:
            ear_values.append(float(np.mean(frame_ears)))

    # Not enough data to make a judgment
    if frames_with_face < 5 or frames_with_eyes < 3:
        return {
            "score": 0,
            "triggered": False,
            "available": False,
            "reason": (
                "Insufficient face/eye data for blink analysis "
                f"({frames_with_face} frames with face, {frames_with_eyes} with eyes detected)."
            ),
        }

    ear_array = np.array(ear_values)
    ear_variance = float(np.var(ear_array))
    avg_ear = float(np.mean(ear_array))

    # Detect blinks: EAR drops below 0.25 = closed eye
    BLINK_THRESHOLD = 0.25
    blink_count = 0
    in_blink = False
    for ear in ear_values:
        if ear < BLINK_THRESHOLD and not in_blink:
            blink_count += 1
            in_blink = True
        elif ear >= BLINK_THRESHOLD:
            in_blink = False

    # At 1fps sampling over N frames ≈ N seconds of video
    # Expected blinks: 1 per 4 seconds minimum
    expected_min_blinks = max(1, frames_with_eyes // 4)
    no_blink = blink_count == 0 and frames_with_eyes >= 8
    static_eyes = ear_variance < 0.001

    triggered = bool(no_blink or static_eyes)

    if triggered:
        if no_blink and static_eyes:
            explanation = (
                f"No natural blinking detected over {frames_with_eyes} frames and "
                f"eyes appear unnaturally static (EAR variance={round(ear_variance, 5)}) — "
                "strong deepfake indicator."
            )
        elif no_blink:
            explanation = (
                f"No eye blinks detected over {frames_with_eyes} frames "
                f"(expected at least {expected_min_blinks}) — "
                "deepfakes commonly fail to reproduce natural human blinking."
            )
        else:
            explanation = (
                f"Eyes appear unnaturally static (EAR variance={round(ear_variance, 5)}, "
                f"avg EAR={round(avg_ear, 3)}) — real eyes have constant micro-movements."
            )
    else:
        explanation = (
            f"Natural eye movement detected — {blink_count} blinks over {frames_with_eyes} frames "
            f"(EAR variance={round(ear_variance, 4)})."
        )

    return {
        "score": 25 if triggered else 0,
        "triggered": triggered,
        "available": True,
        "blink_count": blink_count,
        "frames_with_eyes": frames_with_eyes,
        "ear_variance": round(ear_variance, 5),
        "avg_ear": round(avg_ear, 3),
        "explanation": explanation,
    }
