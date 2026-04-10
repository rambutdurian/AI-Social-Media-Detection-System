def aggregate_score(signal_results):
    """
    Score Aggregation.

    Each signal contributes equally. Score = (triggered / total_active) * 100.
    Signals 5/6/7 are optional — only counted if 'available' is True.

    Risk Levels:
      0–30   → low      (likely authentic)
      31–60  → moderate (some suspicious patterns)
      61–100 → high     (strong AI indicators)
    """
    # Core signals — always active
    base_signals = ['brightness', 'temporal', 'blur', 'facial_stability', 'face_forensics']
    triggered_count = sum(
        1 for s in base_signals if signal_results.get(s, {}).get('triggered', False)
    )
    total_signals = 5

    # Signal 5: XceptionNet (optional)
    xception = signal_results.get('xception', {})
    if xception.get('available', False):
        total_signals += 1
        if xception.get('triggered', False):
            triggered_count += 1

    # Signal 6: FFT frequency analysis (optional)
    fft = signal_results.get('fft', {})
    if fft.get('available', False):
        total_signals += 1
        if fft.get('triggered', False):
            triggered_count += 1

    # Signal 7: Eye blink detection (optional)
    blink = signal_results.get('blink', {})
    if blink.get('available', False):
        total_signals += 1
        if blink.get('triggered', False):
            triggered_count += 1

    ai_score = round((triggered_count / total_signals) * 100)
    confidence = min(95, 50 + ai_score // 2)

    if ai_score <= 15:
        risk_level = "low"
        risk_label = "Low Risk"
    elif ai_score <= 60:
        risk_level = "moderate"
        risk_label = "Moderate Risk"
    else:
        risk_level = "high"
        risk_label = "High Risk"

    trust_score = 100 - ai_score

    return {
        "riskScore": ai_score,
        "trustScore": trust_score,
        "confidence": confidence,
        "riskLevel": risk_level,
        "riskLabel": risk_label,
        "triggeredSignals": triggered_count,
        "totalSignals": total_signals,
    }


def build_detection_metrics(signal_results: dict, risk_score: int) -> dict:
    """
    Build detection metrics logically derived from actual signal results.
    All values 0-95. Invariant: if zero signals trigger, all metrics = 0.
    """
    blur_triggered     = signal_results.get('blur', {}).get('triggered', False)
    temporal_triggered = signal_results.get('temporal', {}).get('triggered', False)
    faces_triggered    = signal_results.get('facial_stability', {}).get('triggered', False)
    xception           = signal_results.get('xception', {})
    xception_triggered = xception.get('triggered', False) and xception.get('available', False)

    # AI-Generated: driven by blur (skin smoothing) and xception model
    ai_generated = 0
    if blur_triggered:
        ai_generated += 40
    if xception_triggered:
        ai_generated += 45
    if temporal_triggered:
        ai_generated += 10
    ai_generated = min(95, ai_generated)

    # Deepfake: driven by face instability + xception + temporal
    deepfake = 0
    if faces_triggered:
        deepfake += 35
    if xception_triggered:
        deepfake += 40
    if temporal_triggered:
        deepfake += 20
    if blur_triggered:
        deepfake += 10
    deepfake = min(95, deepfake)

    # Impersonation: high only when deepfake is high
    impersonation = min(90, int(deepfake * 0.85)) if deepfake > 50 else min(40, int(deepfake * 0.5))

    # Misinformation: scales with overall risk score
    misinformation = min(70, int(risk_score * 0.6)) if risk_score > 30 else 0

    # Identity theft: only when deepfake is significant
    identity_theft = min(30, int(deepfake * 0.3)) if deepfake > 60 else 0

    return {
        "aiGenerated":    ai_generated,
        "deepfake":       deepfake,
        "impersonation":  impersonation,
        "misinformation": misinformation,
        "phishing":       0,
        "cryptoScam":     0,
        "romanceScam":    0,
        "identityTheft":  identity_theft,
    }


def build_action_guide(risk_level):
    """Return plain-English action recommendations based on risk level."""
    guide = {
        "dontDo": [
            "Do NOT share personal or financial information",
            "Do NOT forward this content without verifying first",
        ],
        "shouldDo": [
            "Verify through the official website of the organisation involved",
            "Report to CyberSecurity Malaysia if fraudulent — cyber999.com",
        ],
        "verifyThrough": [
            "cyber999.com — CyberSecurity Malaysia hotline",
            "Official verified social media accounts only",
            "Snopes.com / FactCheck.org",
        ],
    }

    if risk_level == "high":
        guide["shouldDo"].insert(0, "Do NOT engage with this content or any links within it")
        guide["shouldDo"].append("Consider reporting to PDRM or MCMC")

    return guide
