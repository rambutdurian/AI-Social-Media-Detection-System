# app.py — AI Fraud Detection Backend v3.0
import os, traceback, time, uuid
import numpy as np
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

load_dotenv()


# ── Custom JSON encoder — handles ALL numpy types globally ────────────────────
class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):  return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.bool_):    return bool(obj)
        if isinstance(obj, np.ndarray):  return obj.tolist()
        return super().default(obj)


app = Flask(__name__)
app.json_provider_class = NumpyJSONProvider
app.json = NumpyJSONProvider(app)

CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_VIDEO = {'mp4', 'avi', 'mov'}  # Only video formats per spec

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── CUSTOM ERROR HANDLERS ─────────────────────────────────────────────────────
# Flask triggers this automatically when the uploaded file exceeds MAX_CONTENT_LENGTH.
# Without this, Flask returns a generic HTML error page. This gives a plain JSON message.
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'This file is too big. Try uploading a shorter clip (under 100 MB).'}), 413


def allowed(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def score_to_verdict(score: int):
    """Maps AI score (0-100) to verdict string and risk label."""
    if score >= 70:
        return 'DEEPFAKE', 'High Risk'
    if score >= 40:
        return 'INCONCLUSIVE', 'Medium Risk'
    return 'AUTHENTIC', 'Low Risk'


# ── PRE-LOAD models once at startup ──────────────────────────────────────────
def preload_models():
    print('\n[STARTUP] Pre-loading models into memory...')
    t = time.time()

    try:
        from analyzers.content_analyzer import get_clf
        get_clf()
        print(f'[STARTUP] HuggingFace text model ready ({time.time()-t:.1f}s)')
    except Exception as e:
        print(f'[STARTUP] Text model skipped: {e}')

    try:
        import cv2
        cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        print(f'[STARTUP] OpenCV ready ({time.time()-t:.1f}s)')
    except Exception as e:
        print(f'[STARTUP] OpenCV skipped: {e}')

    print(f'[STARTUP] Done in {time.time()-t:.1f}s — server is ready!\n')


# ── IMPORT analyzers ──────────────────────────────────────────────────────────
from analyzers.video_analyzer    import analyze_video, extract_frames
from analyzers.url_analyzer      import analyze_url
from analyzers.content_analyzer  import analyze_content
from analyzers.metadata_analyzer import analyze_metadata
from analyzers.score_aggregator  import aggregate_media_scores, aggregate_url_scores
from analyzers.multi_signal      import run_multi_signal
from analyzers.genai_analyzer    import generate_llm_analysis
from db import log_analysis, get_history, log_analysis_history, get_analysis_history


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': '3.1',
                    'capabilities': ['video', 'url']})


# ── VIDEO ANALYSIS ────────────────────────────────────────────────────────────
@app.route('/analyze/video', methods=['POST'])
def analyze_video_route():
    """Analyzes an uploaded video for deepfake content using XceptionNet + 4-signal pipeline."""
    filepath = None
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'code': 400,
                            'message': 'Invalid video source or unreadable format.'}), 400

        file         = request.files['file']
        content_type = request.form.get('contentType', 'general')

        if not file.filename or not allowed(file.filename, ALLOWED_VIDEO):
            return jsonify({'status': 'error', 'code': 415,
                            'message': 'We only support MP4, AVI, and MOV files.'}), 415

        video_name = file.filename
        filename   = secure_filename(f'{int(time.time())}_{video_name}')
        filepath   = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        print(f'[VIDEO] Analyzing: {filename}')
        start = time.time()

        # Frame extraction
        try:
            frames, meta = extract_frames(filepath)
        except Exception:
            return jsonify({'status': 'error', 'code': 500,
                            'message': 'Frame extraction failed during preprocessing.'}), 500

        if not frames:
            return jsonify({'status': 'error', 'code': 400,
                            'message': 'Invalid video source or unreadable format.'}), 400

        # 4-signal OpenCV pipeline
        multi_result = run_multi_signal(frames)

        # No-face check — signals are unreliable without a detectable face
        avg_faces = multi_result.get('signals', {}).get('face_stability', {}).get('avg_faces', 1)
        if avg_faces == 0:
            os.remove(filepath)
            return jsonify({
                'noFaceDetected': True,
                'message': "We couldn't find a face in this video. Our tool works best on videos showing a person's face.",
            }), 200

        # 4-signal scoring: each triggered signal contributes 25 pts (max 100)
        # brightness > 140 → 25, temporal diff > 20 → 25, blur var < 100 → 25, face std > 0.5 → 25
        signals  = multi_result.get('signals', {})
        ai_score = int(sum(s.get('score', 0) for s in signals.values() if isinstance(s, dict)))

        confidence       = float(min(95, 50 + ai_score / 2))
        verdict, risk_label = score_to_verdict(ai_score)
        risk_level_simple   = 'high' if ai_score >= 70 else 'medium' if ai_score >= 40 else 'low'
        trust_score         = 100 - ai_score
        timestamp           = datetime.now(timezone.utc).isoformat()
        reasons             = multi_result.get('reasons', [])
        explanation         = multi_result.get('explanation', '')

        # Dynamic LLM analysis — Gemini generates scenario-aware advice (A/B/C)
        llm_result = generate_llm_analysis(
            content_type, ai_score, int(confidence), reasons, signals
        )

        print(f'[VIDEO] Done in {round(time.time()-start,2)}s — ai_score={ai_score}, verdict={verdict}')

        # Supabase — new analysis_history table
        db_record = {
            'video_name':    video_name,
            'source_type':   'upload',
            'verdict':       verdict,
            'confidence_score': round(confidence, 2),
            'ai_score':      ai_score,
            'risk_level':    risk_label,
            'frames_analyzed': len(frames),
            'reasons':       reasons,
            'explanation':   explanation,
        }
        analysis_id = log_analysis_history(db_record)

        # Also log to legacy analysis_logs for URL history compatibility
        log_analysis('video', content_type, risk_level_simple, ai_score, db_record)

        os.remove(filepath)
        filepath = None

        return jsonify({
            'status': 'success',
            'data': {
                # Spec fields (Page 10)
                'analysis_id':    analysis_id,
                'video_name':     video_name,
                'verdict':        verdict,
                'confidence_score': round(confidence / 100, 3),
                'ai_score':       ai_score,
                'risk_level':     risk_label,
                'frames_analyzed': len(frames),
                'reasons':        reasons,
                'explanation':    explanation,
                'timestamp':      timestamp,
                # Frontend-compatible fields (existing mapToResult)
                'trustScore':     trust_score,
                'riskLevel':      risk_level_simple,
                'riskImpact': {
                    'financial':      risk_level_simple,
                    'reputation':     'medium' if ai_score >= 40 else 'low',
                    'misinformation': 'low',
                },
                'detectionMetrics': {
                    'aiGenerated':   ai_score,
                    'deepfake':      ai_score,
                    'impersonation': 0,
                    'misinformation': 0,
                    'cryptoScam':    0,
                    'romanceScam':   0,
                    'phishing':      0,
                    'identityTheft': 0,
                },
                'verdict':             llm_result.get('verdict', verdict),
                'riskSummary':         llm_result.get('riskSummary', ''),
                'scenario':            llm_result.get('scenario', 'B'),
                'officialSources':     llm_result.get('officialSources', []),
                'identityTrustScore':  llm_result.get('identityTrustScore'),
                'identityEvidence':    llm_result.get('identityEvidence', []),
                'explainableFindings': llm_result.get('explainableFindings', reasons),
                'whatToDo':            llm_result.get('whatToDo', {
                    'dontDo':        ['Do not share or forward this video without verification'],
                    'shouldDo':      ['Report to relevant authorities if financial fraud is suspected'],
                    'verifyThrough': ['Securities Commission Malaysia: sc.com.my',
                                     'Investment Checker: investor.gov.my'],
                }),
                'analysisTime': round(time.time() - start, 2),
            }
        }), 200

    except TimeoutError:
        return jsonify({'status': 'error', 'code': 504,
                        'message': 'Processing timed out. Try a shorter video.'}), 504
    except Exception as e:
        traceback.print_exc()
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'status': 'error', 'code': 500,
                        'message': 'Frame extraction failed during preprocessing.'}), 500


# ── IMAGE REJECTION ───────────────────────────────────────────────────────────
# Frauda is a VIDEO deepfake detector. Images are not accepted.
# This route exists to give a clear error if someone tries to upload an image.
@app.route('/analyze/image', methods=['POST'])
def analyze_image_route():
    return jsonify({'error': 'We only support MP4, AVI, and MOV files. Try saving your video in a different format.'}), 415


# ── URL ANALYSIS — runs all 3 analyzers IN PARALLEL ──────────────────────────
@app.route('/analyze/url', methods=['POST'])
def analyze_url_route():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing url'}), 400

        url          = data['url'].strip()
        content_type = data.get('contentType', 'general')

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        print(f'[URL] Analyzing: {url}')
        start = time.time()

        # ── Run all 3 analyzers at the same time in parallel threads ──────────
        # Before: url → wait → content → wait → metadata → wait = 15-30s
        # After:  all 3 run simultaneously = only as slow as the slowest one
        url_result      = None
        content_result  = None
        metadata_result = None

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_url      = executor.submit(analyze_url,      url)
            future_content  = executor.submit(analyze_content,  url, content_type)
            future_metadata = executor.submit(analyze_metadata, url)

            url_result      = future_url.result(timeout=15)
            content_result  = future_content.result(timeout=20)
            metadata_result = future_metadata.result(timeout=12)

        result = aggregate_url_scores(url, content_type, url_result, content_result, metadata_result)
        result['analysisTime'] = round(time.time() - start, 2)
        print(f'[URL] Done in {result["analysisTime"]}s — score={result["riskScore"]}')

        # Save to Supabase history.
        log_analysis('url', content_type, result.get('riskLevel', 'unknown'),
                     result.get('riskScore', 0), result)

        return jsonify(result), 200

    except TimeoutError:
        # TimeoutError is raised when future.result(timeout=N) runs out of time.
        # 504 = "Gateway Timeout" — the correct HTTP code when an upstream call takes too long.
        return jsonify({'error': 'This took too long. Try uploading a shorter video and try again.'}), 504

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── ANALYSIS HISTORY ─────────────────────────────────────────────────────────
@app.route('/history', methods=['GET'])
def history_route():
    """Returns the last N video analysis logs from analysis_history for the History Dashboard."""
    try:
        limit = int(request.args.get('limit', 50))
        rows  = get_analysis_history(limit)
        return jsonify({'status': 'success', 'data': rows}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'code': 500, 'message': str(e)}), 500


# ── PDF REPORT GENERATOR ──────────────────────────────────────────────────────
# Accepts the analysis result JSON from the frontend and returns a PDF file.
# The frontend sends the result it already has (no need to re-analyze).
@app.route('/generate-report', methods=['POST'])
def generate_report_route():
    try:
        from flask import send_file
        from report_generator import generate_pdf_report
        import io

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing result data'}), 400

        # Build the PDF bytes from the result
        pdf_bytes = generate_pdf_report(data)

        # Wrap bytes in BytesIO so Flask can stream it as a file download
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        # send_file() tells the browser to download it as a file, not display in browser
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='frauda-report.pdf'
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── START ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'AI Fraud Detection Backend v3.0')
    print(f'Running at http://localhost:{port}')
    print(f'Endpoints: /analyze/video  /analyze/image  /analyze/url')
    preload_models()
    app.run(debug=False, port=port)
