"""
FRAUDA — ML Performance Evaluation Script
==========================================
Usage:
  1. Put real videos in: ml/test_videos/real/   (label = 0)
  2. Put fake videos in: ml/test_videos/fake/   (label = 1)
  3. Run: python ml/evaluate.py
  4. Results saved to: ml/results/evaluation_report.json

Minimum: 4 videos (2 real + 2 fake). Ideal: 20 (10 + 10).
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)

from services.scorer import aggregate_score
from services.signal_engine import (
    check_blur,
    check_brightness,
    check_facial_stability,
    check_temporal,
)
from services.video_processor import extract_frames
from services.xception_signal import check_xception

REAL_DIR = os.path.join(os.path.dirname(__file__), 'test_videos', 'real')
FAKE_DIR = os.path.join(os.path.dirname(__file__), 'test_videos', 'fake')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
THRESHOLD = 15  # risk_score > 50 → predicted fake


def analyze_video(video_path):
    """
    Run full analysis pipeline on a single video.
    Returns risk_score (0-100).
    Uses lower thresholds suited for short compressed clips.
    """
    try:
        frames, _ = extract_frames(video_path, fps=2, max_frames=40)
    except Exception as e:
        print(f"      Frame extract error: {e}")
        return None

    if not frames or len(frames) < 2:
        return None

    signal_results = {
        "brightness": check_brightness(frames),
        "temporal":   check_temporal(frames),
        "blur":       check_blur(frames),
        "facial_stability": check_facial_stability(frames),
        "xception":   check_xception(frames)
    }

    scores = aggregate_score(signal_results)
    return scores["riskScore"]


def run_evaluation():
    print("\nFRAUDA — ML Evaluation Starting...\n")

    video_paths = []
    true_labels = []

    for f in sorted(os.listdir(REAL_DIR)) if os.path.exists(REAL_DIR) else []:
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
            video_paths.append(os.path.join(REAL_DIR, f))
            true_labels.append(0)

    for f in sorted(os.listdir(FAKE_DIR)) if os.path.exists(FAKE_DIR) else []:
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.webm')):
            video_paths.append(os.path.join(FAKE_DIR, f))
            true_labels.append(1)

    if len(video_paths) < 4:
        print("ERROR: Not enough videos. Add at least 2 real + 2 fake videos.")
        return

    print(f"Found {true_labels.count(0)} real videos, {true_labels.count(1)} fake videos\n")

    scores = []
    predicted_labels = []
    valid_true = []
    failed = []

    for i, (path, label) in enumerate(zip(video_paths, true_labels)):
        name = os.path.basename(path)
        label_str = "REAL" if label == 0 else "FAKE"
        print(f"[{i + 1}/{len(video_paths)}] {name} (True: {label_str})... ", end="", flush=True)

        try:
            score = analyze_video(path)
            if score is None:
                print("SKIPPED (no frames)")
                failed.append(name)
                continue
            predicted = 1 if score > THRESHOLD else 0
            scores.append(score)
            predicted_labels.append(predicted)
            valid_true.append(label)
            correct = "OK" if predicted == label else "WRONG"
            print(f"score={score} → {'FAKE' if predicted else 'REAL'} [{correct}]")
        except Exception as e:
            print(f"ERROR: {e}")
            failed.append(name)

    if len(predicted_labels) < 2:
        print("\nNot enough successful analyses to compute metrics.")
        return

    print(f"\nResults for {len(predicted_labels)} videos:\n")

    accuracy = accuracy_score(valid_true, predicted_labels)
    f1 = f1_score(valid_true, predicted_labels, zero_division=0)

    try:
        auc_roc = roc_auc_score(valid_true, scores)
    except ValueError:
        auc_roc = None
        print("AUC-ROC could not be calculated (need both classes present)")

    cm = confusion_matrix(valid_true, predicted_labels)

    print(f"  Accuracy : {accuracy * 100:.1f}%")
    print(f"  F1 Score : {f1:.3f}")
    if auc_roc is not None:
        print(f"  AUC-ROC  : {auc_roc:.3f}")
    print(f"\n  Confusion Matrix:")
    print(f"  True Neg  (Real→Real) : {cm[0][0]}  |  False Pos (Real→Fake): {cm[0][1]}")
    print(f"  False Neg (Fake→Real) : {cm[1][0]}  |  True Pos  (Fake→Fake): {cm[1][1]}")
    print(f"\n{classification_report(valid_true, predicted_labels, target_names=['Real', 'Fake'])}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    report = {
        "total_videos": len(video_paths),
        "analyzed": len(predicted_labels),
        "failed": failed,
        "threshold_used": THRESHOLD,
        "accuracy": round(accuracy * 100, 2),
        "f1_score": round(f1, 3),
        "auc_roc": round(auc_roc, 3) if auc_roc is not None else None,
        "confusion_matrix": cm.tolist(),
        "scores_per_video": [
            {
                "file": os.path.basename(p),
                "true_label": t,
                "risk_score": s,
                "predicted": pred,
                "correct": t == pred,
            }
            for p, t, s, pred in zip(video_paths, valid_true, scores, predicted_labels)
        ],
    }

    report_path = os.path.join(RESULTS_DIR, 'evaluation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nFull evaluation report saved to: {report_path}")
    print("Use these numbers (Accuracy / F1 / AUC-ROC) in your presentation slides.\n")


if __name__ == '__main__':
    run_evaluation()
