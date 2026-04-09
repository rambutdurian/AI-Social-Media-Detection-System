# backend/analyzers/multi_signal.py
from analyzers.video_analyzer import (
    signal_brightness,
    signal_temporal,
    signal_blur,
    signal_face_stability,
)


def run_multi_signal(frames: list) -> dict:
    """
    Runs the 4-signal OpenCV pipeline on pre-extracted frames.
    Returns reasons (triggered signal explanations), explanation summary, and raw signals.
    """
    s1 = signal_brightness(frames)
    s2 = signal_temporal(frames)
    s3 = signal_blur(frames)
    s4 = signal_face_stability(frames)

    reasons = [
        sig['explanation']
        for sig in [s1, s2, s3, s4]
        if sig.get('triggered')
    ]

    if not reasons:
        reasons = ['No strong deepfake indicators detected in this video.']

    triggered_count = sum(1 for sig in [s1, s2, s3, s4] if sig.get('triggered'))
    if triggered_count > 0:
        explanation = (
            f"{triggered_count} of 4 detection signal(s) triggered. "
            + ' '.join(reasons[:2])
        )
    else:
        explanation = (
            'No deepfake signals triggered across brightness, '
            'motion, blur, and facial stability checks.'
        )

    return {
        'reasons': reasons,
        'explanation': explanation,
        'signals': {
            'brightness':     s1,
            'temporal':       s2,
            'blur':           s3,
            'face_stability': s4,
        },
    }
