# analyzers/score_aggregator.py

ACTIONS = {
    'investment': {
        'dontDo': [
            'Do NOT transfer money or share banking details',
            'Do NOT share IC, passport, or personal documents',
            'Do NOT click investment links from this source',
        ],
        'shouldDo': [
            'Verify with Securities Commission Malaysia — sc.com.my',
            'Check Bank Negara fraud alert list — bnm.gov.my/fraudalert',
            'Verify celebrity endorsement through their OFFICIAL verified social accounts',
            'Consult a licensed financial adviser before any investment',
        ],
        'verifyThrough': [
            'sc.com.my — Securities Commission investor alert list',
            'bnm.gov.my/fraudalert — Bank Negara Malaysia',
            'Celebrity official verified Instagram/Facebook/TikTok only',
        ]
    },
    'job': {
        'dontDo': [
            'Do NOT pay training fees, equipment costs, or upfront deposits',
            'Do NOT share NRIC, EPF, or bank account before company is verified',
        ],
        'shouldDo': [
            'Search company on SSM Malaysia — ssm.com.my',
            'Find the company on LinkedIn and check for verified badge + employee count',
            'Call the company directly using the number from their official website only',
        ],
        'verifyThrough': [
            'ssm.com.my — Companies Commission of Malaysia',
            'LinkedIn company profile — check for verified badge',
            'Jobstreet / Indeed company reviews',
        ]
    },
    'health': {
        'dontDo': [
            'Do NOT purchase unverified supplements or health products',
            'Do NOT stop prescribed medicine without consulting your doctor',
        ],
        'shouldDo': [
            'Check if product is registered with Ministry of Health Malaysia',
            'Verify doctor credentials at mmc.gov.my (Malaysian Medical Council)',
        ],
        'verifyThrough': [
            'moh.gov.my — Ministry of Health Malaysia',
            'mmc.gov.my — Malaysian Medical Council',
            'bfad.gov.ph / fda.gov for product registration status',
        ]
    },
    'news': {
        'dontDo': [
            'Do NOT share before cross-checking with credible sources',
            'Do NOT make decisions based on a single unverified source',
        ],
        'shouldDo': [
            'Check Sebenarnya.my — Malaysia official fact-checking portal',
            'Search for the same story on Bernama, The Star, or Reuters',
        ],
        'verifyThrough': [
            'sebenarnya.my — Malaysia official fact checker',
            'Bernama.com / Reuters / BBC',
            'Snopes.com / FactCheck.org',
        ]
    },
    'general': {
        'dontDo': [
            'Do NOT share personal or financial information',
            'Do NOT forward this content without verifying first',
        ],
        'shouldDo': [
            'Verify through the official website of the organisation involved',
            'Report to CyberSecurity Malaysia if fraudulent — cyber999.com',
        ],
        'verifyThrough': [
            'cyber999.com — CyberSecurity Malaysia hotline',
            'Official verified social media accounts only',
            'Snopes.com / FactCheck.org',
        ]
    }
}


def _safe_int(val):
    """Converts any numeric value (including numpy types) to a plain Python int."""
    try:
        return int(val)
    except Exception:
        return 0


def _build_common(trust_score, composite, risk_level, content_type, all_flags, signals_detail):
    """Builds the shared response fields used by both media and URL analysis."""
    # Cast everything to plain Python ints to avoid JSON serialization errors
    composite   = _safe_int(composite)
    trust_score = _safe_int(trust_score)

    is_fin  = content_type in ('investment', 'job')
    is_info = content_type in ('news', 'health')

    # All comparisons use plain Python ints — no numpy types
    financial_risk = (
        'high'   if is_fin and composite > 60 else
        'medium' if is_fin and composite > 30 else
        'medium' if composite > 70 else
        'low'
    )
    reputation_risk = (
        'high'   if composite > 65 else
        'medium' if composite > 35 else
        'low'
    )
    misinfo_risk = (
        'high'   if is_info and composite > 55 else
        'medium' if is_info and composite > 25 else
        'medium' if composite > 50 else
        'low'
    )

    # Get individual signal scores safely
    url_score      = _safe_int(signals_detail.get('url_score', 0))
    content_score  = _safe_int(signals_detail.get('content_score', 0))
    metadata_score = _safe_int(signals_detail.get('metadata_score', 0))
    deepfake_score = _safe_int(signals_detail.get('deepfake_score', composite))

    # crypto scam score — only meaningful for investment content type
    crypto_score = deepfake_score if content_type == 'investment' else 0

    return {
        'trustScore': trust_score,
        'riskScore':  composite,
        'riskLevel':  risk_level,
        'riskImpact': {
            'financial':      financial_risk,
            'reputation':     reputation_risk,
            'misinformation': misinfo_risk,
        },
        'explainableFindings': all_flags or ['No strong indicators detected — content appears low risk'],
        'whatToDo': ACTIONS.get(content_type, ACTIONS['general']),
        # All 8 metrics the frontend expects — no missing fields, all plain ints
        'detectionMetrics': {
            'aiGenerated':   deepfake_score,
            'deepfake':      deepfake_score,
            'impersonation': url_score,
            'misinformation':content_score,
            'cryptoScam':    crypto_score,
            'romanceScam':   0,
            'phishing':      url_score,
            'identityTheft': metadata_score,
        },
        'contentType': content_type,
    }


def aggregate_media_scores(media_type: str, content_type: str, media_result: dict) -> dict:
    """
    Builds the final response for VIDEO and IMAGE analysis.
    Called by the /analyze/video and /analyze/image endpoints.
    """
    composite   = _safe_int(media_result.get('score', 0))
    trust_score = _safe_int(100 - composite)
    risk_level  = 'high' if composite >= 65 else 'medium' if composite >= 35 else 'low'

    all_flags = media_result.get('flags', [])

    # Build signal timeline
    signals  = media_result.get('signals', {})
    timeline = []
    for sig_name, sig_data in signals.items():
        if isinstance(sig_data, dict) and sig_data.get('triggered'):
            timeline.append({
                'signal':      sig_name,
                'explanation': str(sig_data.get('explanation', ''))
            })

    result = _build_common(
        trust_score, composite, risk_level, content_type,
        all_flags, {'deepfake_score': composite}
    )
    result['mediaType']         = media_type
    result['confidence']        = _safe_int(media_result.get('confidence', min(95, 50 + composite // 2)))
    result['detectionTimeline'] = timeline
    result['framesAnalyzed']    = _safe_int(media_result.get('frames_analyzed', 1))
    result['facesDetected']     = _safe_int(media_result.get('faces_detected', 0))
    result['signalBreakdown']   = signals
    return result


def aggregate_url_scores(url: str, content_type: str, url_result: dict, content_result: dict, metadata_result: dict) -> dict:
    """
    Builds the final response for URL / social media link analysis.
    Called by the /analyze/url endpoint.
    Weights: URL=25%, Content=50%, Metadata=25%
    """
    url_s      = _safe_int(url_result.get('score', 0))
    content_s  = _safe_int(content_result.get('score', 0))
    metadata_s = _safe_int(metadata_result.get('score', 0))

    composite   = int(url_s * 0.25 + content_s * 0.50 + metadata_s * 0.25)
    composite   = min(composite, 100)
    trust_score = 100 - composite
    risk_level  = 'high' if composite >= 65 else 'medium' if composite >= 35 else 'low'

    all_flags = (
        url_result.get('flags', []) +
        content_result.get('flags', []) +
        metadata_result.get('flags', [])
    )

    result = _build_common(
        trust_score, composite, risk_level, content_type,
        all_flags, {
            'url_score':      url_s,
            'content_score':  content_s,
            'metadata_score': metadata_s,
        }
    )
    result['mediaType'] = 'url'
    result['url']       = url
    result['detectionTimeline'] = [
        {'signal': 'URL Analysis',        'score': url_s,      'flags': url_result.get('flags', [])},
        {'signal': 'Content Analysis',    'score': content_s,  'flags': content_result.get('flags', [])},
        {'signal': 'Domain Intelligence', 'score': metadata_s, 'flags': metadata_result.get('flags', [])},
    ]
    return result
