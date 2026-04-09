# report_generator.py — PDF Forensic Report Generator
#
# LINE-BY-LINE EXPLANATION:
# This file builds a professional PDF report using the FPDF2 library.
# It takes the full analysis result dict (the same JSON we send to the frontend)
# and formats it into a downloadable PDF with:
#   - A header with Frauda branding
#   - Trust Score and Risk Level prominently displayed
#   - All triggered signals with their explanations
#   - The "What To Do" action list
#   - Official source links
#   - A footer with timestamp

import io
from datetime import datetime
from fpdf import FPDF


# ── Unicode sanitizer — fpdf2 defaults to Latin-1 encoding ───────────────────
# Gemini LLM output contains smart quotes, em dashes, ellipsis, etc.
# These are valid UTF-8 but crash FPDF's Latin-1 encoder with UnicodeEncodeError.
# This function converts them to ASCII equivalents before rendering.
def _sanitize(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        '\u2018': "'", '\u2019': "'",    # left/right single quotation marks
        '\u201c': '"', '\u201d': '"',    # left/right double quotation marks
        '\u2013': '-', '\u2014': '-',    # en dash, em dash
        '\u2026': '...', '\u00a0': ' ',  # ellipsis, non-breaking space
        '\u2022': '-', '\u00b7': '-',    # bullet, middle dot
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    # Safety net: replace anything still not representable in Latin-1 with '?'
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ── Custom FPDF subclass ──────────────────────────────────────────────────────
# We extend FPDF to add a custom header and footer that appear on every page.
class FraudaReport(FPDF):
    """
    FPDF subclass with Frauda-branded header/footer.
    header() and footer() are called automatically by FPDF on each new page.
    """

    def header(self):
        """Prints the Frauda logo area and report title at the top of each page."""
        # Set a dark blue background bar
        self.set_fill_color(15, 23, 42)       # Dark navy blue (slate-900)
        self.rect(0, 0, 210, 20, 'F')          # Full-width filled rectangle, 20mm tall

        # White bold title text
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.cell(0, 10, _sanitize('FRAUDA - AI Trust Intelligence Report'), align='L')

        # Timestamp on the right
        self.set_font('Helvetica', '', 8)
        self.set_text_color(148, 163, 184)     # Slate-400 gray
        self.set_xy(0, 7)
        self.cell(200, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}', align='R')

        # Reset text color back to black for body content
        self.set_text_color(0, 0, 0)
        self.ln(15)                            # Move down past the header bar


    def footer(self):
        """Prints page number and disclaimer at the bottom of each page."""
        self.set_y(-15)                        # Position 15mm from the bottom
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()} | Frauda AI Trust Intelligence | For informational purposes only', align='C')


# ── Helper functions ──────────────────────────────────────────────────────────

def _risk_color(risk_level: str) -> tuple:
    """Returns (R, G, B) color tuple based on risk level."""
    return {
        'high':   (239, 68, 68),    # Red-500
        'medium': (245, 158, 11),   # Amber-500
        'low':    (34, 197, 94),    # Green-500
    }.get(risk_level, (107, 114, 128))  # Gray fallback


def _section_title(pdf: FraudaReport, title: str):
    """Draws a colored section header bar with white title text."""
    pdf.set_fill_color(30, 58, 138)            # Blue-900
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, _sanitize(f'  {title}'), fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _bullet(pdf: FraudaReport, text: str, color: tuple = (55, 65, 81)):
    """Draws one bullet point line."""
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*color)
    # Use a small filled circle as bullet
    pdf.set_x(15)
    pdf.cell(5, 6, '-', ln=False)         # chr(149) = bullet •
    pdf.set_x(20)
    pdf.multi_cell(175, 6, _sanitize(text))
    pdf.set_text_color(0, 0, 0)


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def generate_pdf_report(result: dict) -> bytes:
    """
    Builds the full PDF report from the analysis result dict.

    Parameters:
      result — the full JSON dict returned by /analyze/video or /analyze/url

    Returns:
      bytes — the raw PDF file content, ready to send as an HTTP response

    How it works:
    1. Creates the FPDF object
    2. Adds pages/sections in order
    3. Uses pdf.output() to get the bytes (not write to a file)
    """

    pdf = FraudaReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # ── SECTION 1: SUMMARY SCORES ─────────────────────────────────────────────
    _section_title(pdf, 'Analysis Summary')

    trust_score = result.get('trustScore', 0)
    risk_score  = result.get('riskScore', 0)
    risk_level  = result.get('riskLevel', 'unknown')
    content_type = result.get('contentType', 'general')
    media_type   = result.get('mediaType', 'unknown')
    analysis_time = result.get('analysisTime', 0)

    r, g, b = _risk_color(risk_level)

    # Trust Score — large colored number
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(r, g, b)
    pdf.set_x(10)
    pdf.cell(60, 16, f'{trust_score}', align='C')

    # Labels next to the score
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(72)
    pdf.cell(0, 8, f'Trust Score / 100', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.set_x(72)
    pdf.cell(0, 6, f'AI Risk Score: {risk_score}/100', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(72)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 6, f'Risk Level: {risk_level.upper()}', new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 0, 0)

    pdf.ln(3)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 5, f'Content Type: {content_type}  |  Media Type: {media_type}  |  Analysis Time: {analysis_time}s', new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ── SECTION 2: LLM VERDICT (if available) ────────────────────────────────
    llm_verdict  = result.get('verdict', '')
    risk_summary = result.get('riskSummary', '')

    if llm_verdict or risk_summary:
        _section_title(pdf, 'Expert AI Verdict')
        if llm_verdict:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.multi_cell(0, 6, _sanitize(llm_verdict))
            pdf.ln(2)
        if risk_summary:
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, _sanitize(risk_summary))
        pdf.ln(4)

    # ── SECTION 3: EXPLAINABLE FINDINGS ──────────────────────────────────────
    findings = result.get('explainableFindings', [])
    if findings:
        _section_title(pdf, 'Why This Looks Suspicious — Forensic Findings')
        for i, finding in enumerate(findings, 1):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(30, 58, 138)
            pdf.set_x(10)
            pdf.cell(8, 6, f'{i}.', ln=False)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(18)
            pdf.multi_cell(185, 6, _sanitize(str(finding)))
        pdf.ln(4)

    # ── SECTION 4: SIGNAL BREAKDOWN (Video only) ──────────────────────────────
    signals = result.get('signalBreakdown', {})
    if signals:
        _section_title(pdf, 'Technical Signal Breakdown (OpenCV Analysis)')
        signal_names = {
            'brightness':     'Signal 1 — Brightness Consistency',
            'temporal':       'Signal 2 — Temporal Frame Differences',
            'blur':           'Signal 3 — Laplacian Blur / Texture',
            'face_stability': 'Signal 4 — Facial Detection Stability',
            'deepface':       'Signal 5 — DeepFace (Optional)',
        }
        for key, sig_data in signals.items():
            if not isinstance(sig_data, dict):
                continue
            label     = signal_names.get(key, key)
            triggered = sig_data.get('triggered', False)
            score     = sig_data.get('score', 0)
            expl      = sig_data.get('explanation', '')

            pdf.set_font('Helvetica', 'B', 10)
            r2, g2, b2 = (239, 68, 68) if triggered else (34, 197, 94)
            pdf.set_text_color(r2, g2, b2)
            status = f'[TRIGGERED +{score}pts]' if triggered else '[CLEAR]'
            pdf.set_x(10)
            pdf.cell(0, 6, _sanitize(f'{label}  {status}'), new_x='LMARGIN', new_y='NEXT')

            if expl:
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(75, 85, 99)
                pdf.set_x(15)
                pdf.multi_cell(185, 5, _sanitize(expl))

        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # ── SECTION 5: IDENTITY ABUSE (Scenario C only) ───────────────────────────
    identity_score   = result.get('identityTrustScore')
    identity_evidence = result.get('identityEvidence', [])

    if identity_score is not None:
        _section_title(pdf, 'Identity Abuse Assessment')
        pdf.set_font('Helvetica', 'B', 14)
        r3, g3, b3 = _risk_color('low' if identity_score > 60 else 'medium' if identity_score > 30 else 'high')
        pdf.set_text_color(r3, g3, b3)
        pdf.cell(0, 10, f'Identity Trust Score: {identity_score}/100', new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(0, 0, 0)

        if identity_evidence:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, 'Evidence of Impersonation:', new_x='LMARGIN', new_y='NEXT')
            for ev in identity_evidence:
                _bullet(pdf, _sanitize(str(ev)), color=(239, 68, 68))
        pdf.ln(4)

    # ── SECTION 6: WHAT TO DO ─────────────────────────────────────────────────
    what_to_do = result.get('whatToDo', {})
    if what_to_do:
        _section_title(pdf, 'Action Guide — What You Should Do')

        dont_do    = what_to_do.get('dontDo', [])
        should_do  = what_to_do.get('shouldDo', [])
        verify     = what_to_do.get('verifyThrough', [])

        if dont_do:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(239, 68, 68)
            pdf.cell(0, 6, 'DO NOT:', new_x='LMARGIN', new_y='NEXT')
            for item in dont_do:
                _bullet(pdf, _sanitize(str(item)), color=(239, 68, 68))
            pdf.ln(2)

        if should_do:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(34, 197, 94)
            pdf.cell(0, 6, 'YOU SHOULD:', new_x='LMARGIN', new_y='NEXT')
            for item in should_do:
                _bullet(pdf, _sanitize(str(item)), color=(34, 197, 94))
            pdf.ln(2)

        if verify:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(59, 130, 246)
            pdf.cell(0, 6, 'VERIFY THROUGH:', new_x='LMARGIN', new_y='NEXT')
            for item in verify:
                _bullet(pdf, _sanitize(str(item)), color=(59, 130, 246))
        pdf.ln(4)

    # ── SECTION 7: OFFICIAL SOURCES (Scenario A) ─────────────────────────────
    official_sources = result.get('officialSources', [])
    if official_sources:
        _section_title(pdf, 'Official Reference Sources')
        for src in official_sources:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(10)
            pdf.cell(0, 6, _sanitize(str(src.get('name', ''))), new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(59, 130, 246)
            pdf.set_x(15)
            pdf.cell(0, 5, _sanitize(str(src.get('url', ''))), new_x='LMARGIN', new_y='NEXT')
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # ── SECTION 8: DISCLAIMER ─────────────────────────────────────────────────
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(107, 114, 128)
    pdf.multi_cell(0, 5, _sanitize(
        'DISCLAIMER: This report is generated by Frauda AI Trust Intelligence and is intended '
        'for informational purposes only. It does not constitute legal, financial, or law '
        'enforcement advice. AI-based detection has limitations and should be used alongside '
        'human verification. Always verify through official sources listed above.'
    ))

    # ── OUTPUT: Get bytes (not write to disk) ─────────────────────────────────
    # pdf.output() with no filename returns the PDF as a bytestring.
    # We wrap it in io.BytesIO so it can be sent as an HTTP file response.
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes
