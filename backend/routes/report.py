import io

from flask import Blueprint, jsonify, request, send_file

from services.pdf_generator import generate_report
from services.supabase_client import get_analysis_by_id

report_bp = Blueprint('report', __name__)


@report_bp.route('/report/generate', methods=['POST'])
def generate_from_result():
    """Generate a PDF directly from the analysis JSON body — no DB lookup needed."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No analysis data provided."}), 400

        # Map camelCase frontend keys → snake_case expected by pdf_generator
        record = {
            "risk_score": data.get("riskScore", 0),
            "trust_score": data.get("trustScore", 100),
            "confidence": data.get("confidence", 50),
            "risk_level": data.get("riskLevel", "low"),
            "risk_label": data.get("riskLabel", "Low Risk"),
            "content_type": data.get("contentType", "general"),
            "media_type": data.get("mediaType", "video"),
            "analysis_time": data.get("analysisTime", 0),
            "explainable_findings": data.get("explainableFindings", []),
            "signal_breakdown": data.get("signalBreakdown", {}),
            "what_to_do": data.get("whatToDo", {}),
        }

        pdf_bytes = generate_report(record)
        aid = (data.get("id") or "result")[:8]

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'frauda-report-{aid}.pdf',
        )
    except Exception as e:
        print(f"[Error] /report/generate: {e}")
        return jsonify({"error": "Could not generate report. Please try again."}), 500


@report_bp.route('/report/<analysis_id>', methods=['GET'])
def download_report(analysis_id):
    """Generate and stream a PDF report for the given analysis ID (requires Supabase)."""
    try:
        record = get_analysis_by_id(analysis_id)
        if not record:
            return jsonify({"error": "Analysis not found."}), 404

        pdf_bytes = generate_report(record)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'frauda-report-{analysis_id[:8]}.pdf',
        )
    except Exception as e:
        print(f"[Error] /report/{analysis_id}: {e}")
        return jsonify({"error": "Could not generate report. Please try again."}), 500
