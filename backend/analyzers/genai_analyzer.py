# analyzers/genai_analyzer.py
# Uses Google Gemini to generate dynamic, scenario-aware analysis.
#
# LINE-BY-LINE EXPLANATION:
# This file sends the raw signal data from OpenCV/URL analysis to Gemini
# and asks it to produce human-readable advice. Instead of hardcoded
# "do this / don't do that" lists, Gemini writes them fresh based on the
# actual score and content type every time.
#
# There are 3 scenarios the LLM handles differently:
#   Scenario A — Investment scam (contentType='investment', score >= 50)
#   Scenario B — General AI content (AI detected but not malicious)
#   Scenario C — Identity/impersonation abuse (contentType='job'/'health' + known figure names)

import os
import json
import re

# --- We use the NEW google-genai SDK (the old google.generativeai is deprecated) ---
from google import genai
from google.genai import types

# Load the API key from the .env file.
# os.environ.get() reads environment variables — dotenv already loaded them in app.py.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# A list of known public figures in Malaysia whose impersonation is a major scam vector.
# If any of these names appear in flags or context, we route to Scenario C.
KNOWN_FIGURES = [
    'anwar ibrahim', 'anwar', 'tony fernandes', 'tony', 'mahathir', 'najib',
    'elon musk', 'warren buffett', 'bill gates', 'mark zuckerberg',
    'pm malaysia', 'prime minister', 'datuk', 'tan sri',
    'ceo', 'chairman', 'managing director'
]


def _detect_scenario(content_type: str, ai_score: int, flags: list) -> str:
    """
    Decides which of the 3 LLM scenarios to use.

    How it works:
    - Joins all flags into a single lowercase string so we can search it
    - If any known figure name appears → Scenario C (Identity Abuse)
    - If content_type is investment and score is high → Scenario A (Investment Scam)
    - Otherwise → Scenario B (General AI Content)
    """
    flags_text = ' '.join(flags).lower()

    # Check for Scenario C first — it takes priority
    for figure in KNOWN_FIGURES:
        if figure in flags_text:
            return 'C'

    # Check for Scenario A
    if content_type == 'investment' and ai_score >= 50:
        return 'A'

    # Default to Scenario B
    return 'B'


def _build_prompt(scenario: str, content_type: str, ai_score: int,
                  confidence: int, flags: list, signals: dict) -> str:
    """
    Builds the exact text prompt we send to Gemini.
    The prompt is carefully structured to get back JSON — not a paragraph of text.
    """

    # Summarize the technical signals into readable text for the LLM
    signal_summary = []
    for name, data in signals.items():
        if isinstance(data, dict) and data.get('triggered'):
            signal_summary.append(f"- {name}: {data.get('explanation', '')}")

    signals_text = '\n'.join(signal_summary) if signal_summary else '- No strong signals triggered'
    flags_text   = '\n'.join(f'- {f}' for f in flags[:5]) if flags else '- None'

    # ── SCENARIO A: Investment Scam ───────────────────────────────────────────
    if scenario == 'A':
        return f"""You are a financial fraud forensics expert for Malaysia. Analyze this deepfake investment video.

TECHNICAL DETECTION RESULTS:
- AI Score: {ai_score}/100 (higher = more likely AI-generated)
- Confidence: {confidence}%
- Content Type: {content_type}
- Triggered Signals:
{signals_text}
- Detection Flags:
{flags_text}

This video is LIKELY an investment scam deepfake targeting Malaysian investors.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "scenario": "A",
  "verdict": "One sentence expert verdict about this specific video",
  "riskSummary": "2-3 sentences explaining what makes this dangerous for investors",
  "explainableFindings": [
    "Finding 1 — specific technical observation from the signals above",
    "Finding 2 — why this pattern is suspicious",
    "Finding 3 — what a real financial video would look like instead",
    "Finding 4 — connection to known investment scam tactics in Malaysia"
  ],
  "whatToDo": {{
    "dontDo": [
      "Do NOT transfer any money or share banking details with this source",
      "Do NOT share IC, passport, or EPF account details",
      "Do NOT click investment links promoted in this video"
    ],
    "shouldDo": [
      "Verify with Securities Commission Malaysia — sc.com.my/investor-alert",
      "Check Bank Negara Malaysia fraud alert — bnm.gov.my/fraudalert",
      "Verify the celebrity endorsement on their OFFICIAL verified social accounts only",
      "Consult a licensed financial adviser registered with SC Malaysia"
    ],
    "verifyThrough": [
      "sc.com.my — Securities Commission Malaysia investor alert list",
      "bnm.gov.my/fraudalert — Bank Negara Malaysia official fraud alerts",
      "Celebrity/CEO's verified Instagram, Facebook, or TikTok only",
      "ssm.com.my — Companies Commission of Malaysia to verify investment firms"
    ]
  }},
  "officialSources": [
    {{"name": "SC Warns Public on Deepfake Investment Scams", "url": "https://www.sc.com.my/resources/media/media-release/sc-warns-public-on-deepfake-investment-scams-impersonating-prominent-personalities"}},
    {{"name": "Investment Checker — Securities Commission Malaysia", "url": "https://www.sc.com.my/investor-alert"}}
  ]
}}"""

    # ── SCENARIO C: Identity/Impersonation Abuse ──────────────────────────────
    elif scenario == 'C':
        return f"""You are an identity fraud expert specializing in deepfake impersonation of public figures.

TECHNICAL DETECTION RESULTS:
- AI Score: {ai_score}/100
- Confidence: {confidence}%
- Content Type: {content_type}
- Triggered Signals:
{signals_text}
- Detection Flags:
{flags_text}

This video likely impersonates a known public figure (politician, CEO, or celebrity).

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "scenario": "C",
  "verdict": "One sentence expert verdict about the impersonation attempt",
  "identityTrustScore": {max(5, 100 - ai_score)},
  "identityEvidence": [
    "Visual evidence 1 — specific facial/motion inconsistency detected",
    "Visual evidence 2 — voice/lighting/background mismatch",
    "Visual evidence 3 — behavioral patterns inconsistent with known recordings"
  ],
  "riskSummary": "2-3 sentences about the danger of this impersonation",
  "explainableFindings": [
    "Finding 1 — technical signal that proves manipulation",
    "Finding 2 — what was detected in the frame analysis",
    "Finding 3 — comparison to authentic content patterns",
    "Finding 4 — who could be harmed and how"
  ],
  "whatToDo": {{
    "dontDo": [
      "Do NOT assume this is the real person speaking",
      "Do NOT share or forward this video as authentic",
      "Do NOT make financial or voting decisions based on this content",
      "Do NOT click any links promoted by the person in this video"
    ],
    "shouldDo": [
      "Verify through the official verified social media accounts of the real person",
      "Check official government or company websites for authentic statements",
      "Report the deepfake to the platform (TikTok/Facebook/YouTube) immediately",
      "Report to CyberSecurity Malaysia — cyber999.com or call 1-300-88-2999"
    ],
    "verifyThrough": [
      "Official verified social media of the impersonated person only",
      "Bernama.com — Malaysian national news agency for official statements",
      "cyber999.com — CyberSecurity Malaysia reporting portal",
      "sebenarnya.my — Malaysia official government fact-checking portal"
    ]
  }}
}}"""

    # ── SCENARIO B: General AI Content (no specific scam detected) ───────────
    else:
        return f"""You are a digital media forensics expert analyzing AI-generated content.

TECHNICAL DETECTION RESULTS:
- AI Score: {ai_score}/100
- Confidence: {confidence}%
- Content Type: {content_type}
- Triggered Signals:
{signals_text}
- Detection Flags:
{flags_text}

This content shows signs of AI generation but no specific high-risk scam patterns were confirmed.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "scenario": "B",
  "verdict": "One sentence summary of whether this content is AI-generated and low/medium/high concern",
  "riskSummary": "2-3 sentences explaining what AI indicators were found and what this means",
  "explainableFindings": [
    "Finding 1 — specific AI signal detected",
    "Finding 2 — what the signal means in plain language",
    "Finding 3 — comparison to how real human-recorded video behaves",
    "Finding 4 — overall reliability assessment"
  ],
  "whatToDo": {{
    "dontDo": [
      "Do NOT share this content as verified or authentic",
      "Do NOT forward without adding context that it may be AI-generated"
    ],
    "shouldDo": [
      "Cross-reference with the original source or official website of the person/organization",
      "Use a reverse video search to find the original source",
      "Check if the same content appears on verified official accounts"
    ],
    "verifyThrough": [
      "Official website or verified social media of the source",
      "sebenarnya.my — Malaysia official fact-checking portal",
      "Snopes.com or FactCheck.org for global verification"
    ]
  }}
}}"""


def generate_llm_analysis(content_type: str, ai_score: int, confidence: int,
                           flags: list, signals: dict) -> dict:
    """
    MAIN FUNCTION — calls Gemini and returns the structured analysis.

    Returns a dict with the LLM's response merged with fallback data.
    If Gemini fails (no API key, network error, bad JSON), we return
    a safe fallback so the app never crashes due to LLM issues.

    Parameters:
      content_type — 'investment', 'job', 'health', 'news', 'general'
      ai_score     — 0-100 from the signal engine
      confidence   — 0-95 from the signal engine
      flags        — list of triggered signal explanations
      signals      — dict of raw signal data from video_analyzer
    """

    # ── GUARD: If no API key, return a static fallback immediately ────────────
    if not GEMINI_API_KEY:
        print('[GenAI] No GEMINI_API_KEY — skipping LLM analysis')
        return _fallback_response(content_type, ai_score, flags)

    try:
        # Step 1: Decide which scenario applies
        scenario = _detect_scenario(content_type, ai_score, flags)
        print(f'[GenAI] Scenario {scenario} detected for content_type={content_type}, score={ai_score}')

        # Step 2: Build the prompt
        prompt = _build_prompt(scenario, content_type, ai_score, confidence, flags, signals)

        # Step 3: Create Gemini client with the new SDK
        # genai.Client() connects to the Gemini API using our API key
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Step 4: Call Gemini — we use gemini-2.0-flash for speed
        # generate_content() sends the prompt and waits for the response
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,        # Lower = more consistent/factual output
                max_output_tokens=1200, # Enough for the full JSON response
            )
        )

        # Step 5: Extract the raw text from the response
        raw_text = response.text.strip()
        print(f'[GenAI] Got response ({len(raw_text)} chars)')

        # Step 6: Parse the JSON — Gemini sometimes wraps it in ```json ... ```
        # so we strip that if present
        json_text = raw_text
        if '```json' in json_text:
            # Extract content between ```json and ```
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()

        # Step 7: Parse the JSON string into a Python dict
        llm_result = json.loads(json_text)
        print(f'[GenAI] Parsed JSON successfully, scenario={llm_result.get("scenario")}')

        return llm_result

    except json.JSONDecodeError as e:
        print(f'[GenAI] JSON parse error: {e} — raw: {raw_text[:200]}')
        return _fallback_response(content_type, ai_score, flags)

    except Exception as e:
        print(f'[GenAI] Error: {e}')
        return _fallback_response(content_type, ai_score, flags)


def _fallback_response(content_type: str, ai_score: int, flags: list) -> dict:
    """
    Returns hardcoded but safe data when Gemini is unavailable.
    This ensures the app never shows an empty results panel.
    """
    from analyzers.score_aggregator import ACTIONS
    return {
        'scenario':  'B',
        'verdict':   f'AI analysis score: {ai_score}/100. Manual review recommended.',
        'riskSummary': 'Automated signal analysis completed. LLM enrichment unavailable.',
        'explainableFindings': flags or ['No strong deepfake indicators detected.'],
        'whatToDo':  ACTIONS.get(content_type, ACTIONS['general']),
    }
