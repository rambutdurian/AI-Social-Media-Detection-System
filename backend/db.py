# db.py — Supabase database helper for Frauda
#
# This file has ONE job: save an analysis result to the database.
# It is intentionally kept separate from app.py so you can update
# the database logic without touching the Flask routes.

import os
from dotenv import load_dotenv

load_dotenv()

# Read the Supabase connection details from your .env file.
# These are set once when the module is first imported.
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# We store the Supabase client in this variable so we only create it once.
# Creating a database connection on every request would be very slow.
_client = None


def get_client():
    """
    Returns a connected Supabase client.
    If the client was already created before, reuses it (singleton pattern).
    If SUPABASE_URL or SUPABASE_KEY are missing from .env, returns None.
    """
    global _client

    # If we already created the client, just return it immediately.
    if _client is not None:
        return _client

    # If the env vars are not set, we can't connect — return None.
    if not SUPABASE_URL or not SUPABASE_KEY:
        print('[DB] WARNING: SUPABASE_URL or SUPABASE_KEY not set in .env — history will not be saved.')
        return None

    # Create the client for the first time.
    from supabase import create_client
    _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print('[DB] Supabase client connected.')
    return _client


def log_analysis(analysis_type: str, content_type: str, risk_level: str, risk_score: int, result: dict):
    """
    Saves one analysis result to the 'analysis_logs' table in Supabase.

    Parameters:
      analysis_type — 'video' or 'url'
      content_type  — 'investment', 'job', 'health', 'news', or 'general'
      risk_level    — 'low', 'medium', or 'high'
      risk_score    — the numeric AI score (0–100)
      result        — the full analysis result dict (stored as JSON)

    If Supabase is not configured or the insert fails, this function
    prints a warning and returns without crashing the app.
    This is called 'failing silently' — a database error should never
    stop the user from seeing their analysis result.
    """
    try:
        client = get_client()

        # If Supabase isn't set up, just skip logging and move on.
        if client is None:
            return

        # .insert() adds one new row to the table.
        # .execute() actually sends the request to Supabase.
        client.table('analysis_logs').insert({
            'analysis_type': analysis_type,   # 'video' or 'url'
            'content_type':  content_type,    # which scam category
            'risk_level':    risk_level,       # low / medium / high
            'risk_score':    risk_score,       # 0–100
            'result_json':   result,           # the whole result as JSON
        }).execute()

        print(f'[DB] Logged: {analysis_type} | {content_type} | {risk_level} | score={risk_score}')

    except Exception as e:
        # If anything goes wrong (network, table doesn't exist, etc.),
        # just print a warning — don't crash the server.
        print(f'[DB] Failed to log analysis (non-fatal): {e}')


def log_analysis_history(record: dict) -> str:
    """
    Inserts one video analysis result into the 'analysis_history' table.

    Parameters:
      record — dict with keys: video_name, source_type, verdict, confidence_score,
               ai_score, risk_level, frames_analyzed, reasons (list), explanation

    Returns the UUID of the inserted row, or a random UUID if insert fails.
    """
    import uuid as _uuid
    fallback_id = str(_uuid.uuid4())
    try:
        client = get_client()
        if client is None:
            return fallback_id
        response = client.table('analysis_history').insert(record).execute()
        if response.data:
            return response.data[0].get('id', fallback_id)
        return fallback_id
    except Exception as e:
        print(f'[DB] Failed to log analysis_history (non-fatal): {e}')
        return fallback_id


def get_analysis_history(limit: int = 50) -> list:
    """
    Fetches the most recent video analysis logs from 'analysis_history'.

    Returns list of dicts ordered by newest first.
    """
    try:
        client = get_client()
        if client is None:
            return []
        response = (
            client.table('analysis_history')
            .select('*')
            .order('created_at', desc=True)
            .limit(limit)
            .execute()
        )
        print(f'[DB] Fetched {len(response.data)} analysis_history rows')
        return response.data
    except Exception as e:
        print(f'[DB] Failed to fetch analysis_history (non-fatal): {e}')
        return []


def get_history(limit: int = 20) -> list:
    """
    Fetches the most recent analysis logs from Supabase.

    Parameters:
      limit — maximum number of rows to return (default 20)

    Returns:
      list of dicts, ordered by newest first.
      Each dict has: id, analysis_type, content_type, risk_level, risk_score, created_at

    If Supabase is not configured, returns an empty list.
    """
    try:
        client = get_client()
        if client is None:
            return []

        # .select() chooses which columns to return (not the full result_json — that's huge)
        # .order() sorts by created_at descending (newest first)
        # .limit() caps how many rows we get
        response = (
            client.table('analysis_logs')
            .select('id, analysis_type, content_type, risk_level, risk_score, created_at')
            .order('created_at', desc=True)
            .limit(limit)
            .execute()
        )

        print(f'[DB] Fetched {len(response.data)} history rows')
        return response.data

    except Exception as e:
        print(f'[DB] Failed to fetch history (non-fatal): {e}')
        return []
