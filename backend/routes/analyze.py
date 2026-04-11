import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, jsonify, request

from services.scorer import aggregate_score, build_action_guide, build_detection_metrics
from services.signal_engine import (
    check_blur,
    check_brightness,
    check_facial_stability,
    check_temporal,
)
from services.face_forensics_signal import check_face_forensics
from services.fft_signal import check_fft
from services.blink_signal import check_blink
from services.supabase_client import save_analysis
from services.url_downloader import download_video_from_url, is_supported_url
from services.video_processor import delete_temp_video, extract_frames, save_temp_video
from services.xception_signal import check_xception

analyze_bp = Blueprint('analyze', __name__)

ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.webm', '.mkv'}


@analyze_bp.route('/analyze', methods=['POST'])
def analyze():
    start_time = time.time()
    temp_path = None
    file_name = None
    source_url = None

    try:
        # ── Input: file upload OR social media URL ──────────────────────
        if 'video' in request.files:
            file = request.files['video']
            if not file.filename:
                return jsonify({"error": "No file selected."}), 400

            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({
                    "error": "We only support MP4, AVI, MOV, and WEBM files. "
                             "Try saving your video in a different format."
                }), 415

            temp_path = save_temp_video(file, ext)
            file_name = file.filename

        elif request.is_json and request.json.get('url'):
            url = request.json['url'].strip()
            if not is_supported_url(url):
                return jsonify({
                    "error": "Unsupported URL. We support TikTok, YouTube, Instagram, "
                             "and Facebook links."
                }), 400

            temp_path, title = download_video_from_url(url)
            source_url = url
            file_name = title

        else:
            return jsonify({
                "error": "Please upload a video file or provide a social media URL."
            }), 400

        # ── Frame extraction ────────────────────────────────────────────
        frames, frames_analyzed = extract_frames(temp_path, fps=1, max_frames=15)

        if len(frames) == 0:
            return jsonify({
                "error": "We couldn't read any frames from this video. "
                         "The file may be corrupted or in an unsupported format."
            }), 400

        # ── Run all detection signals in parallel ───────────────────────
        signal_fns = {
            "brightness":       check_brightness,
            "temporal":         check_temporal,
            "blur":             check_blur,
            "facial_stability": check_facial_stability,
            "face_forensics":   check_face_forensics,
            "xception":         check_xception,
            "fft":              check_fft,
            "blink":            check_blink,
        }
        signal_results = {}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(fn, frames): name for name, fn in signal_fns.items()}
            for future in as_completed(futures):
                name = futures[future]
                signal_results[name] = future.result()

        faces_detected = round(signal_results["facial_stability"].get("avg_faces", 0))

        if faces_detected == 0:
            return jsonify({
                "error": "No face detected in this video. Our tool works best on videos showing a person speaking directly to camera."
            }), 400

        # ── Score aggregation ───────────────────────────────────────────
        scores = aggregate_score(signal_results)
        detection_metrics = build_detection_metrics(signal_results, scores["riskScore"])
        what_to_do = build_action_guide(scores["riskLevel"])

        # ── Build explainable findings & timeline ───────────────────────
        explainable_findings = []
        detection_timeline = []
        for signal_name, result in signal_results.items():
            if result.get("triggered") and result.get("explanation"):
                explainable_findings.append(result["explanation"])
                detection_timeline.append({
                    "signal": signal_name,
                    "explanation": result["explanation"],
                })

        risk_impact = {
            "financial": "high" if scores["riskLevel"] == "high" else "low",
            "reputation": scores["riskLevel"],
            "misinformation": "medium" if scores["riskLevel"] != "low" else "low",
        }

        analysis_time = round(time.time() - start_time, 2)

        result = {
            "mediaType": "video",
            "contentType": request.form.get("contentType", "general"),
            "fileName": file_name,
            "sourceUrl": source_url,
            "riskScore": scores["riskScore"],
            "trustScore": scores["trustScore"],
            "confidence": scores["confidence"],
            "riskLevel": scores["riskLevel"],
            "riskLabel": scores["riskLabel"],
            "analysisTime": analysis_time,
            "framesAnalyzed": frames_analyzed,
            "facesDetected": faces_detected,
            "signalBreakdown": signal_results,
            "detectionMetrics": detection_metrics,
            "detectionTimeline": detection_timeline,
            "explainableFindings": explainable_findings,
            "riskImpact": risk_impact,
            "whatToDo": what_to_do,
        }

        # ── Save to Supabase (non-blocking on failure) ──────────────────
        try:
            saved = save_analysis(result)
            result["id"] = saved.get("id")
        except Exception as db_err:
            print(f"[DB] Failed to save to Supabase: {db_err}")

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print(f"[Error] /analyze failed: {e}")
        return jsonify({
            "error": "Something went wrong during analysis. "
                     "Try uploading a shorter clip and try again."
        }), 500

    finally:
        delete_temp_video(temp_path)
