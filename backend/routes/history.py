from flask import Blueprint, jsonify

from services.supabase_client import get_analysis_by_id, get_history

history_bp = Blueprint('history', __name__)


@history_bp.route('/history', methods=['GET'])
def history():
    """Return list of past analyses (summary fields only)."""
    try:
        records = get_history(limit=50)
        return jsonify({"history": records}), 200
    except Exception as e:
        print(f"[Error] /history: {e}")
        return jsonify({"error": "Could not retrieve analysis history."}), 500


@history_bp.route('/history/<analysis_id>', methods=['GET'])
def get_single(analysis_id):
    """Return full analysis record by UUID."""
    try:
        record = get_analysis_by_id(analysis_id)
        if not record:
            return jsonify({"error": "Analysis not found."}), 404
        return jsonify(record), 200
    except Exception as e:
        print(f"[Error] /history/{analysis_id}: {e}")
        return jsonify({"error": "Could not retrieve analysis."}), 500
