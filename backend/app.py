import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

from routes.analyze import analyze_bp
from routes.history import history_bp
from routes.report import report_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/ping')
def ping():
    return 'ok', 200

@app.route("/health")
def health():
    return {"status": "ok"}, 200

app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE_MB', 100)) * 1024 * 1024

app.register_blueprint(analyze_bp)
app.register_blueprint(history_bp)
app.register_blueprint(report_bp)

os.makedirs(os.getenv('TEMP_VIDEO_DIR', './tmp_videos'), exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ok", "service": "Frauda AI Backend", "version": "1.0"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
