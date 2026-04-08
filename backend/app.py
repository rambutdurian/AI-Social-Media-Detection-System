# app.py — AI Fraud Detection Backend v3.0
import os, traceback, time
import numpy as np
from flask import Flask, request, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from analyzers.video_analyzer    import analyze_video
from analyzers.url_analyzer      import analyze_url
from analyzers.content_analyzer  import analyze_content
from analyzers.metadata_analyzer import analyze_metadata
from analyzers.score_aggregator  import aggregate_media_scores, aggregate_url_scores
from db import log_analysis


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': '3.1',
                    'capabilities': ['video', 'url']})


# ── VIDEO ANALYSIS ────────────────────────────────────────────────────────────
@app.route('/analyze/video', methods=['POST'])
def analyze_video_route():
    filepath = None
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file         = request.files['file']
        content_type = request.form.get('contentType', 'general')

        if not file.filename or not allowed(file.filename, ALLOWED_VIDEO):
            # 415 = "Unsupported Media Type" — the correct HTTP code for wrong file format
            return jsonify({'error': 'We only support MP4, AVI, and MOV files. Try saving your video in a different format.'}), 415

        filename = secure_filename(f'{int(time.time())}_{file.filename}')
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        print(f'[VIDEO] Analyzing: {filename}')
        start = time.time()

        video_result = analyze_video(filepath)

        # ── No-face check: if OpenCV found zero faces across all frames,
        #    our deepfake signals are unreliable (they depend on a face being present).
        #    Return a 200 OK but with a special flag so the frontend can show a warning.
        avg_faces = video_result.get('signals', {}).get('face_stability', {}).get('avg_faces', 1)
        if avg_faces == 0:
            os.remove(filepath)
            return jsonify({
                'noFaceDetected': True,
                'message': "We couldn't find a face in this video. Our tool works best on videos showing a person's face.",
            }), 200

        result       = aggregate_media_scores('video', content_type, video_result)
        result['analysisTime'] = round(time.time() - start, 2)
        print(f'[VIDEO] Done in {result["analysisTime"]}s — score={result["riskScore"]}')

        # Save to Supabase history. This runs after the analysis is done.
        # If it fails, the user still gets their result — see db.py for why.
        log_analysis('video', content_type, result.get('riskLevel', 'unknown'),
                     result.get('riskScore', 0), result)

        os.remove(filepath)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500


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


# ── START ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'AI Fraud Detection Backend v3.0')
    print(f'Running at http://localhost:{port}')
    print(f'Endpoints: /analyze/video  /analyze/image  /analyze/url')
    preload_models()
    app.run(debug=False, port=port)
