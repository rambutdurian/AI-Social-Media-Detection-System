# analyzers/content_analyzer.py
# Fetches webpage text and analyzes it for scam patterns.
# Optimized for speed: short timeouts, lightweight AI model usage.

import requests
import re
from bs4 import BeautifulSoup

# ── AI model — loaded once and cached ────────────────────────────────────────
_clf = None

def get_clf():
    """Load the HuggingFace model once. Returns None if unavailable."""
    global _clf
    if _clf is None:
        try:
            from transformers import pipeline
            print('[AI] Loading text classification model...')
            _clf = pipeline(
                'text-classification',
                model='martin-ha/toxic-comment-model',
                device=-1,          # CPU — no GPU needed
                truncation=True,
                max_length=512
            )
            print('[AI] Text model loaded!')
        except Exception as e:
            print(f'[AI] Model load failed (will use phrase-only detection): {e}')
            _clf = None
    return _clf


# ── Scenario-aware scam phrases ───────────────────────────────────────────────
SCENARIO_PHRASES = {
    'investment': [
        'guaranteed returns', 'risk-free investment', '100% profit',
        'double your money', 'passive income guaranteed', 'secret strategy',
        'financial freedom', 'crypto millionaire', 'insider tip',
        'limited spots', 'act before midnight', 'exclusive members only',
    ],
    'job': [
        'work from home earn', 'no experience needed', 'unlimited earning',
        'make money fast', 'training fee required', 'pay upfront',
        'starter kit', 'immediate start', 'send your details',
    ],
    'health': [
        'doctors hate this', 'miracle cure', 'instant results',
        'banned supplement', 'ancient secret', 'reverses aging',
        'fda doesnt want', 'one weird trick', 'cures all',
    ],
    'news': [
        'they dont want you to know', 'mainstream media hiding',
        'cover-up exposed', 'wake up sheeple', 'plandemic', 'deep state',
        'shocking truth revealed', 'banned news',
    ],
    'general': [
        'click here now', 'you have been selected', 'congratulations you won',
        'verify your account', 'urgent action required',
        'gift card payment', 'wire transfer', 'send me your',
        'prince needs help', 'inheritance transfer',
    ],
}

URGENCY_WORDS = [
    'urgent', 'immediately', 'act now', 'expires today', 'last chance',
    'hurry', 'final notice', 'respond within 24', 'your account will be',
    'limited time', 'deadline',
]


def fetch_page(url: str) -> tuple:
    """
    Fetches a webpage and returns (clean_text, metadata_dict).
    Uses a short 7-second timeout so slow sites don't block the server.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=7)
        resp.raise_for_status()

        soup  = BeautifulSoup(resp.text, 'lxml')
        title = soup.find('title')
        meta  = soup.find('meta', attrs={'name': 'description'})

        # Remove noise elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        text = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True)).strip()

        # Limit to 1500 chars — enough for analysis, reduces AI processing time
        text = text[:1500]

        return text, {
            'title':       title.get_text(strip=True) if title else '',
            'description': meta.get('content', '') if meta else '',
            'status':      resp.status_code,
        }

    except requests.Timeout:
        return '', {'error': 'Page took too long to load (>7s)'}
    except requests.ConnectionError:
        return '', {'error': 'Could not connect to URL'}
    except Exception as e:
        return '', {'error': str(e)}


def analyze_content(url: str, content_type: str) -> dict:
    """
    Analyzes webpage content for scam patterns.
    Runs phrase detection (fast) + AI model (moderate).
    """
    risk_score = 0
    flags      = []
    details    = {}

    # Step 1: Fetch the page
    text, meta = fetch_page(url)
    details['meta'] = meta

    if not text or 'error' in meta:
        return {
            'score':   20,
            'flags':   [f'Could not load page: {meta.get("error", "unknown error")}'],
            'details': details
        }

    text_lower = text.lower()
    details['preview'] = text[:150] + '...'

    # Step 2: Scenario-aware phrase detection (very fast — just string matching)
    phrases    = SCENARIO_PHRASES.get(content_type, []) + SCENARIO_PHRASES['general']
    hits       = [p for p in phrases if p in text_lower]
    if hits:
        risk_score += min(len(hits) * 12, 40)
        flags.append(f'Found {len(hits)} scam-associated phrases for "{content_type}": {hits[:3]}')
    details['phrase_hits'] = hits[:5]

    # Step 3: AI model — manipulative language detection
    # Only run if model is loaded and text is long enough to be meaningful
    clf = get_clf()
    if clf and len(text.strip()) > 50:
        try:
            # Use only first 512 chars — faster and within model limit
            chunk  = text[:512]
            result = clf(chunk, truncation=True, max_length=512)[0]

            label = result['label'].lower()
            score = float(result['score'])

            # Model labels vary by version — handle all common ones
            is_toxic = label in ('toxic', 'label_1', '1', 'spam', 'hate')

            if is_toxic and score > 0.5:
                ai_points = int(score * 40)
                risk_score += ai_points
                flags.append(f'AI model: manipulative/harmful language detected ({score:.0%} confidence)')
            elif is_toxic and score > 0.3:
                risk_score += 10
                flags.append(f'AI model: some suspicious language patterns ({score:.0%} confidence)')

            details['ai_score'] = round(score, 3)

        except Exception as e:
            details['ai_error'] = str(e)

    # Step 4: Urgency tactic detection
    urgency_hits = [w for w in URGENCY_WORDS if w in text_lower]
    if len(urgency_hits) >= 2:
        risk_score += 15
        flags.append(f'Multiple urgency tactics detected: {urgency_hits[:3]}')

    # Step 5: Excessive ALL CAPS (common in scam content)
    words = text.split()
    if len(words) > 15:
        caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / len(words)
        if caps_ratio > 0.12:
            risk_score += 10
            flags.append(f'Excessive capitalisation ({caps_ratio:.0%} of words in ALL CAPS)')

    # Step 6: No trust signals (legitimate sites always have these)
    trust_signals = ['privacy policy', 'terms of service', 'contact us', 'about us', 'registered']
    if not any(ts in text_lower for ts in trust_signals):
        risk_score += 10
        flags.append('No privacy policy, terms, or contact information found — untransparent site')

    return {
        'score':   int(min(risk_score, 100)),
        'flags':   flags,
        'details': details
    }
