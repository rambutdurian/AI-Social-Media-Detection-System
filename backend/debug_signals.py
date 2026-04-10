"""
Debug script — checks what signal values the fake and real videos are getting.
Run from backend folder:
    python debug_signals.py
"""
import os
import sys
sys.path.insert(0, '.')

from services.video_processor import extract_frames
from services.signal_engine import check_brightness, check_temporal, check_blur, check_facial_stability

FAKE_DIR = 'ml/test_videos/fake'
REAL_DIR = 'ml/test_videos/real'

def check_video(path, label):
    try:
        frames, n = extract_frames(path, fps=2, max_frames=40)
        if not frames:
            print(f"  [{label}] {os.path.basename(path)} — NO FRAMES")
            return None

        blur     = check_blur(frames)
        temporal = check_temporal(frames)
        bright   = check_brightness(frames)
        faces    = check_facial_stability(frames)

        total_score = blur['score'] + temporal['score'] + bright['score'] + faces['score']

        print(f"\n  [{label}] {os.path.basename(path)} ({n} frames)")
        print(f"    blur      : score={blur['score']}  triggered={blur['triggered']}  variance={blur.get('avg_variance','?')}")
        print(f"    temporal  : score={temporal['score']}  triggered={temporal['triggered']}  mean_diff={temporal.get('mean_diff','?')}")
        print(f"    brightness: score={bright['score']}  triggered={bright['triggered']}  avg={bright.get('avg_brightness','?')}")
        print(f"    faces     : score={faces['score']}  triggered={faces['triggered']}  std={faces.get('std_faces','?')}")
        print(f"    TOTAL SCORE: {total_score}")
        return total_score

    except Exception as e:
        print(f"  [{label}] {os.path.basename(path)} ERROR: {e}")
        return None


print("=" * 60)
print("  FRAUDA — Signal Debug")
print("=" * 60)

# Check first 5 fake videos
print("\n--- FAKE VIDEOS ---")
fake_scores = []
if os.path.exists(FAKE_DIR):
    for f in sorted(os.listdir(FAKE_DIR))[:5]:
        if f.endswith('.mp4'):
            s = check_video(os.path.join(FAKE_DIR, f), 'FAKE')
            if s is not None:
                fake_scores.append(s)

# Check first 5 real videos
print("\n--- REAL VIDEOS ---")
real_scores = []
if os.path.exists(REAL_DIR):
    for f in sorted(os.listdir(REAL_DIR))[:5]:
        if f.endswith('.mp4'):
            s = check_video(os.path.join(REAL_DIR, f), 'REAL')
            if s is not None:
                real_scores.append(s)

print("\n" + "=" * 60)
print(f"  Fake scores: {fake_scores}  avg={round(sum(fake_scores)/len(fake_scores),1) if fake_scores else 'N/A'}")
print(f"  Real scores: {real_scores}  avg={round(sum(real_scores)/len(real_scores),1) if real_scores else 'N/A'}")
print("=" * 60)
print("\nUse these values to set the right THRESHOLD in evaluate.py")
print("Ideal threshold = midpoint between avg fake and avg real scores")
