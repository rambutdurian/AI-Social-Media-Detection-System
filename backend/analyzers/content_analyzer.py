# analyzers/content_analyzer.py
# Fetches and analyzes the text content of a webpage for scam indicators.
# Used by the /analyze/url endpoint as the "Content Analysis" signal (50% weight).

import re
import requests
from bs4 import BeautifulSoup

# ── Scam phrase lists ─────────────────────────────────────────────────────────

# Phrases commonly found on investment scam pages
INVESTMENT_SCAM_PHRASES = [
    'guaranteed returns', 'risk-free investment', 'double your money',
    'get rich', 'passive income', 'crypto trading bot', 'investment opportunity',
    'exclusive investment', '100% profit', 'zero risk', 'no risk',
    'whatsapp me', 'telegram group', 'dm for details', 'join now',
    'limited slots', 'guaranteed profit',
]

# Phrases used in phishing pages to steal credentials or personal info
PHISHING_PHRASES = [
    'verify your account', 'confirm your identity', 'update payment',
    'click here immediately', 'your account is suspended', 'urgent action required',
    'otp required', 'login to confirm', 'verify now', 'account will be closed',
    'unusual activity detected', 'reactivate your account',
]

# Urgency/pressure tactics used to rush victims into acting without thinking
URGENCY_PHRASES = [
    'act now', 'limited time', 'hurry', 'today only', 'last chance',
    'expiring soon', 'immediate action', 'do not delay', 'offer ends',
    'only a few spots left',
]

# ── HuggingFace model (optional, loaded once at startup) ─────────────────────

_clf = None  # Module-level cache — only loaded once


def get_clf():
    """
    Loads and caches a lightweight HuggingFace zero-shot text classifier.

    'Zero-shot' means the model can classify text into any labels you give it
    without needing to be trained on those specific labels first.

    This is called once at startup by preload_models() in app.py.
    If the model can't be downloaded (no internet, not enough RAM), it
    gracefully returns None and the rest of analyze_content() still works
    using only the rule-based checks.
    """
    global _clf
    if _clf is None:
        try:
            from transformers import pipeline
            # device=-1 means run on CPU (no GPU required)
            # This model is ~260MB and needs to be downloaded once
            _clf = pipeline(
                'zero-shot-classification',
                model='typeform/distilbert-base-uncased-mnli',
                device=-1,
            )
        except Exception as e:
            # Not a fatal error — rule-based checks still run without this
            print(f'[ContentAnalyzer] HuggingFace model unavailable (non-fatal): {e}')
            _clf = None
    return _clf


# ── Private helper ────────────────────────────────────────────────────────────

def _fetch_text(url: str, timeout: int = 8) -> str:
    """
    Fetches a webpage and returns its visible text content.

    Steps:
    1. Send an HTTP GET request pretending to be a normal browser
       (some sites block requests without a User-Agent header).
    2. Parse the raw HTML with BeautifulSoup.
    3. Remove non-visible tags: <script>, <style>, <noscript>, <meta>.
    4. Extract all remaining text, collapse whitespace.
    5. Truncate to 5000 characters so analysis stays fast.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0 Safari/537.36'
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()  # Raises an exception for 4xx/5xx HTTP errors

    soup = BeautifulSoup(resp.text, 'lxml')

    # Remove tags whose content is never visible to real users
    for tag in soup(['script', 'style', 'meta', 'noscript']):
        tag.decompose()

    text = soup.get_text(separator=' ', strip=True)

    # Collapse multiple spaces/newlines into a single space
    text = re.sub(r'\s+', ' ', text)

    return text[:5000]  # Cap at 5000 chars — enough to catch scam language


# ── Main public function ──────────────────────────────────────────────────────

def analyze_content(url: str, content_type: str = 'general') -> dict:
    """
    Fetches the webpage at `url` and scans its text for scam indicators.

    Called by the /analyze/url endpoint with a 20-second thread timeout.
    Weights 50% of the final URL composite risk score.

    Args:
        url:          The full URL to analyze (e.g. 'https://example.com').
        content_type: Category hint from the user ('investment', 'job',
                      'health', 'news', 'general'). Used for context-specific checks.

    Returns:
        {
            'score':   int   — risk score 0–100 (higher = more suspicious),
            'flags':   list  — human-readable explanations of what was found,
            'details': dict  — extra metadata (char count, classifier result, etc.)
        }
    """
    risk_score = 0
    flags      = []
    details    = {}

    try:
        # ── Fetch page text ───────────────────────────────────────────────────
        text       = _fetch_text(url)
        text_lower = text.lower()
        details['char_count'] = len(text)

        # ── CHECK 1: Investment / financial scam language ─────────────────────
        # Scammers use specific phrases to lure victims into fake investments.
        # We check how many of these phrases appear and score proportionally.
        matched_inv = [p for p in INVESTMENT_SCAM_PHRASES if p in text_lower]
        if matched_inv:
            # Each phrase adds 10 points, capped at 40 total for this check
            risk_score += min(40, len(matched_inv) * 10)
            # Show the first 3 matched phrases in the flag message
            flags.append(
                f'Investment scam language detected: "{", ".join(matched_inv[:3])}"'
            )

        # ── CHECK 2: Phishing / credential theft language ─────────────────────
        # Phishing pages try to trick users into entering passwords or OTPs.
        matched_phish = [p for p in PHISHING_PHRASES if p in text_lower]
        if matched_phish:
            risk_score += min(35, len(matched_phish) * 12)
            flags.append(
                f'Phishing language detected: "{", ".join(matched_phish[:3])}"'
            )

        # ── CHECK 3: Urgency / pressure tactics ───────────────────────────────
        # Scammers create artificial urgency so victims act without thinking.
        matched_urgency = [p for p in URGENCY_PHRASES if p in text_lower]
        if matched_urgency:
            risk_score += min(15, len(matched_urgency) * 5)
            flags.append(
                f'Urgency/pressure tactics found: "{", ".join(matched_urgency[:2])}"'
            )

        # ── CHECK 4: Investment content-type bonus ────────────────────────────
        # Only applies when the user selected "Investment" as the content type.
        # Looks for the combination of financial transaction words AND
        # investment promises — a strong pattern for Malaysian investment scams.
        if content_type == 'investment':
            has_financial_words = any(
                kw in text_lower for kw in ['ringgit', ' rm ', 'myr', 'transfer', 'bank account']
            )
            has_promise_words = any(
                kw in text_lower for kw in ['profit', 'earn', 'returns', 'investment', 'dividends']
            )
            if has_financial_words and has_promise_words:
                risk_score += 20
                flags.append(
                    'Financial transaction language combined with investment promises — '
                    'consistent with Malaysian investment scam pattern'
                )

        # ── CHECK 5: HuggingFace zero-shot classification (optional) ──────────
        # If the model loaded successfully, ask it to classify the page text.
        # We use only the first 512 characters (the model's input limit).
        # This is optional: if the model is unavailable, this block is skipped.
        try:
            clf = get_clf()
            if clf and len(text) > 50:
                snippet    = text[:512]
                labels     = ['investment scam', 'phishing', 'legitimate content']
                clf_result = clf(snippet, candidate_labels=labels)

                top_label = clf_result['labels'][0]   # Most likely category
                top_score = clf_result['scores'][0]   # Confidence 0.0–1.0

                details['clf_label']      = top_label
                details['clf_confidence'] = round(top_score, 3)

                # Only add points if the model is confident it's a scam
                if top_label in ('investment scam', 'phishing') and top_score > 0.6:
                    # Add up to 20 bonus points based on model confidence
                    bonus = int(top_score * 20)
                    risk_score += bonus
                    flags.append(
                        f'AI text classifier: page content resembles "{top_label}" '
                        f'({top_score:.0%} confidence)'
                    )
        except Exception:
            # HuggingFace classifier is entirely optional — never let it crash the app
            pass

    # ── Error handling ────────────────────────────────────────────────────────
    # These exceptions mean we couldn't fetch or parse the page.
    # We still return a valid dict (score=0) so the URL pipeline doesn't crash.
    except requests.Timeout:
        flags.append('Page took too long to load — content could not be verified')
        details['fetch_error'] = 'timeout'

    except requests.RequestException as e:
        flags.append(f'Could not fetch page content: {str(e)[:80]}')
        details['fetch_error'] = str(e)[:80]

    except Exception as e:
        flags.append(f'Content analysis error: {str(e)[:80]}')

    return {
        'score':   int(min(risk_score, 100)),  # Always a plain Python int, max 100
        'flags':   flags,
        'details': details,
    }
