import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
)

# Brand colours
FRAUDA_DARK = colors.HexColor('#0A1628')
FRAUDA_BLUE = colors.HexColor('#1E40AF')
FRAUDA_LIGHT_BLUE = colors.HexColor('#3B82F6')
FRAUDA_WHITE = colors.white
TEXT_LIGHT = colors.HexColor('#94A3B8')
RISK_LOW = colors.HexColor('#22C55E')
RISK_MODERATE = colors.HexColor('#F59E0B')
RISK_HIGH = colors.HexColor('#EF4444')


def _risk_color(risk_level):
    if risk_level == 'low':
        return RISK_LOW
    if risk_level == 'moderate':
        return RISK_MODERATE
    return RISK_HIGH


def generate_report(record: dict) -> bytes:
    """Generate PDF report from an analysis record dict. Returns raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # ── Styles ─────────────────────────────────────────────────────────────
    S = {
        'header': ParagraphStyle('header', fontSize=20, textColor=FRAUDA_WHITE,
                                 fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2),
        'sub': ParagraphStyle('sub', fontSize=9, textColor=TEXT_LIGHT,
                              fontName='Helvetica', alignment=TA_CENTER, spaceAfter=6),
        'section': ParagraphStyle('section', fontSize=11, textColor=FRAUDA_LIGHT_BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=4),
        'body': ParagraphStyle('body', fontSize=9, textColor=colors.HexColor('#1E293B'),
                               fontName='Helvetica', spaceAfter=3),
        'disclaimer': ParagraphStyle('disclaimer', fontSize=7, textColor=TEXT_LIGHT,
                                     fontName='Helvetica', alignment=TA_CENTER),
        'footer': ParagraphStyle('footer', fontSize=7,
                                 textColor=colors.HexColor('#CBD5E1'),
                                 fontName='Helvetica', alignment=TA_CENTER),
    }

    # ── Header ─────────────────────────────────────────────────────────────
    story.append(Paragraph("FRAUDA - AI Trust Intelligence", S['header']))
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    story.append(Paragraph(f"Report Generated: {generated_at}", S['sub']))
    story.append(HRFlowable(width="100%", thickness=1, color=FRAUDA_BLUE))
    story.append(Spacer(1, 8 * mm))

    # ── Summary ────────────────────────────────────────────────────────────
    risk_level = record.get('risk_level', 'low')
    risk_score = record.get('risk_score', 0)
    trust_score = record.get('trust_score', 100)
    confidence = record.get('confidence', 50)
    risk_label = record.get('risk_label', 'Low Risk')
    analysis_time = record.get('analysis_time', 0)
    content_type = record.get('content_type', 'general')
    media_type = record.get('media_type', 'video')
    risk_color = _risk_color(risk_level)

    def ps(name, **kw):
        kw.setdefault('fontName', 'Helvetica')
        return ParagraphStyle(name, **kw)

    story.append(Paragraph("Analysis Summary", S['section']))

    inner = Table([
        [Paragraph(f"Trust Score / 100",
                   ps('ts_title', fontSize=10, fontName='Helvetica-Bold',
                      textColor=FRAUDA_DARK))],
        [Paragraph(f"AI Risk Score: <b>{risk_score}/100</b>",
                   ps('ts_risk', fontSize=9))],
        [Paragraph(f"Risk Level: <b>{risk_label.upper()}</b>",
                   ps('ts_rl', fontSize=9, fontName='Helvetica-Bold',
                      textColor=risk_color))],
        [Paragraph(
            f"Content: {content_type} | Media: {media_type} | Time: {analysis_time}s | "
            f"Confidence: {confidence}%",
            ps('ts_meta', fontSize=8, textColor=colors.HexColor('#64748B'))
        )],
    ], colWidths=[130 * mm])

    summary_table = Table([[
        Paragraph(
            f"<b>{trust_score}</b>",
            ps('big', fontSize=28, fontName='Helvetica-Bold', textColor=risk_color)
        ),
        inner,
    ]], colWidths=[30 * mm, 130 * mm])

    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6 * mm))

    # ── Forensic Findings ──────────────────────────────────────────────────
    findings = record.get('explainable_findings', [])
    if findings:
        story.append(Paragraph("Why This Looks Suspicious — Forensic Findings", S['section']))
        for i, finding in enumerate(findings, 1):
            story.append(Paragraph(f"{i}. {finding}", S['body']))
        story.append(Spacer(1, 5 * mm))

    # ── Signal Breakdown Table ─────────────────────────────────────────────
    story.append(Paragraph("Technical Signal Breakdown (OpenCV Analysis)", S['section']))

    signal_breakdown = record.get('signal_breakdown', {})
    signal_map = [
        ('brightness', 'Signal 1 — Brightness Consistency'),
        ('temporal', 'Signal 2 — Temporal Frame Differences'),
        ('blur', 'Signal 3 — Laplacian Blur / Texture'),
        ('facial_stability', 'Signal 4 — Facial Detection Stability'),
        ('xception', 'Signal 5 — XceptionNet Deep Learning'),
    ]

    def cell(text, **kw):
        return Paragraph(text, ps('c', fontSize=8, **kw))

    table_data = [[cell('Signal', fontName='Helvetica-Bold'),
                   cell('Status', fontName='Helvetica-Bold'),
                   cell('Details', fontName='Helvetica-Bold')]]

    for key, label in signal_map:
        sig = signal_breakdown.get(key, {})
        if not sig:
            continue
        available = sig.get('available', True)
        triggered = sig.get('triggered', False)
        explanation = sig.get('explanation') or sig.get('reason', 'No data')

        if not available:
            status_text, status_color = 'DISABLED', colors.HexColor('#94A3B8')
        elif triggered:
            status_text, status_color = 'TRIGGERED +25pts', RISK_HIGH
        else:
            status_text, status_color = 'CLEAR', RISK_LOW

        table_data.append([
            cell(label, fontName='Helvetica-Bold'),
            cell(f"[{status_text}]", fontName='Helvetica-Bold', textColor=status_color),
            cell(explanation),
        ])

    sig_table = Table(table_data, colWidths=[55 * mm, 38 * mm, 67 * mm])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FRAUDA_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), FRAUDA_WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 6 * mm))

    # ── Action Guide ───────────────────────────────────────────────────────
    story.append(Paragraph("Action Guide — What You Should Do", S['section']))
    what_to_do = record.get('what_to_do', {})

    action_sections = [
        ("DO NOT:", what_to_do.get('dontDo', []), RISK_HIGH),
        ("YOU SHOULD:", what_to_do.get('shouldDo', []), FRAUDA_BLUE),
        ("VERIFY THROUGH:", what_to_do.get('verifyThrough', []), RISK_LOW),
    ]

    for heading, items, color in action_sections:
        story.append(Paragraph(
            f"<b>{heading}</b>",
            ps('act_h', fontSize=9, fontName='Helvetica-Bold', textColor=color, spaceAfter=2)
        ))
        for item in items:
            story.append(Paragraph(
                f"- {item}",
                ps('act_i', fontSize=8, leftIndent=10, spaceAfter=2)
            ))
        story.append(Spacer(1, 3 * mm))

    # ── Disclaimer & Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1')))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "DISCLAIMER: This report is generated by Frauda AI Trust Intelligence and is intended "
        "for informational purposes only. It does not constitute legal, financial, or law "
        "enforcement advice. AI-based detection has limitations and should be used alongside "
        "human verification. Always verify through official sources listed above.",
        S['disclaimer']
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "Page 1 | Frauda AI Trust Intelligence | For informational purposes only",
        S['footer']
    ))

    doc.build(story)
    return buffer.getvalue()
