# analyzers/url_analyzer.py

import re
import tldextract
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {
    '.xyz', '.top', '.click', '.work', '.loan', '.win',
    '.gq', '.ml', '.cf', '.ga', '.tk', '.pw', '.cc'
}

BRANDS = [
    'paypal', 'amazon', 'facebook', 'google', 'microsoft', 'apple',
    'netflix', 'instagram', 'tiktok', 'youtube', 'twitter', 'binance',
    'coinbase', 'maybank', 'cimb', 'rhb', 'publicbank'
]

SCAM_KEYWORDS = [
    'free-money', 'get-rich', 'crypto-profit', 'bitcoin-earn',
    'investment-guaranteed', 'double-your', 'verify-account',
    'account-suspended', 'click-here-now', 'limited-time',
    'claim-now', 'winner', 'prize', 'urgent-offer'
]

TYPO_PATTERNS = {
    'paypal':   r'p[a4]yp[a4][l1]',
    'amazon':   r'[a4]m[a4]z[0o]n',
    'facebook': r'f[a4]c[e3]b[0o][0o]k',
    'google':   r'g[0o][0o]g[l1][e3]',
}


def analyze_url(url: str) -> dict:
    """
    Analyzes a URL structure for phishing and scam indicators.
    Returns: { score (int), flags (list), details (dict) }
    """
    # Use a plain Python int for score — never a list or numpy type
    risk_score = 0
    flags      = []
    details    = {}

    try:
        ext       = tldextract.extract(url)
        domain    = ext.domain.lower()
        suffix    = '.' + ext.suffix.lower()
        subdomain = ext.subdomain.lower()
        url_lower = url.lower()
        reg_domain = ext.registered_domain.lower()

        details['domain'] = reg_domain
        details['tld']    = suffix

        # 1. Suspicious TLD
        if suffix in SUSPICIOUS_TLDS:
            risk_score += 25
            flags.append(f'Suspicious domain extension ({suffix}) — free TLDs are heavily used in scam sites')

        # 2. Brand impersonation
        for brand in BRANDS:
            if brand in domain and domain != brand:
                risk_score += 35
                flags.append(f'Possible impersonation: contains "{brand}" in domain but is not the real {brand}.com')
                break

        # 3. Typosquatting
        for brand, pattern in TYPO_PATTERNS.items():
            if re.search(pattern, domain) and domain != brand:
                risk_score += 40
                flags.append(f'Typosquatting: domain resembles "{brand}" using character substitution')
                break

        # 4. Scam keywords in URL path
        for kw in SCAM_KEYWORDS:
            if kw in url_lower:
                risk_score += 15
                flags.append(f'Scam keyword in URL: "{kw}"')
                break

        # 5. Excessive subdomains
        if subdomain and len(subdomain.split('.')) >= 3:
            risk_score += 20
            flags.append('Excessive subdomain depth — a common technique to disguise the real domain')

        # 6. Raw IP address as URL
        if re.match(r'https?://\d{1,3}(\.\d{1,3}){3}', url):
            risk_score += 35
            flags.append('URL uses a raw IP address instead of a domain name — major phishing indicator')

        # 7. Very long URL
        if len(url) > 200:
            risk_score += 15
            flags.append(f'Unusually long URL ({len(url)} characters) — may be hiding the true destination')

        # 8. Heavy URL encoding
        if url.count('%') > 5:
            risk_score += 15
            flags.append(f'Heavy URL encoding ({url.count("%")} encoded chars) — used to obscure content')

    except Exception as e:
        flags.append(f'URL parse error: {str(e)}')

    # Ensure score is always a plain Python int, capped at 100
    final_score = int(min(risk_score, 100))

    return {
        'score':   final_score,
        'flags':   flags,
        'details': details
    }
