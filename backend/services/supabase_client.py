import os
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)


def save_analysis(result: dict) -> dict:
    """Save analysis result to Supabase. Returns saved record with generated ID."""
    supabase = get_supabase()
    row = {
        "media_type": result.get("mediaType", "video"),
        "file_name": result.get("fileName"),
        "source_url": result.get("sourceUrl"),
        "content_type": result.get("contentType", "general"),
        "risk_score": result["riskScore"],
        "trust_score": result["trustScore"],
        "confidence": result["confidence"],
        "risk_level": result["riskLevel"],
        "risk_label": result["riskLabel"],
        "analysis_time": result.get("analysisTime"),
        "frames_analyzed": result.get("framesAnalyzed"),
        "faces_detected": result.get("facesDetected", 0),
        "signal_breakdown": result.get("signalBreakdown"),
        "detection_metrics": result.get("detectionMetrics"),
        "explainable_findings": result.get("explainableFindings", []),
        "detection_timeline": result.get("detectionTimeline"),
        "risk_impact": result.get("riskImpact"),
        "what_to_do": result.get("whatToDo"),
    }
    response = supabase.table("analyses").insert(row).execute()
    return response.data[0] if response.data else {}


def get_history(limit=50) -> list:
    """Fetch recent analysis history, newest first (summary columns only)."""
    supabase = get_supabase()
    response = (
        supabase.table("analyses")
        .select(
            "id, created_at, media_type, file_name, source_url, "
            "risk_score, risk_level, risk_label, confidence, analysis_time"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_analysis_by_id(analysis_id: str) -> dict:
    """Fetch full analysis record by UUID."""
    supabase = get_supabase()
    response = (
        supabase.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .single()
        .execute()
    )
    return response.data or {}
