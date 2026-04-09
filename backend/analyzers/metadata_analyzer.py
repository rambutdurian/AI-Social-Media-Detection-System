# analyzers/metadata_analyzer.py
# Checks domain age (WHOIS), SSL, and redirect chains.
# All network calls have strict timeouts so they never hang.

import requests
import tldextract
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout


def _whois_lookup(domain: str) -> dict:
    """WHOIS lookup — called in a thread with a timeout."""
    try:
        import whois
        w       = whois.whois(domain)
        created = w.creation_date

        if isinstance(created, list):
            created = created[0]
        if not created:
            return {'error': 'No creation date found'}
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        age_days = int((datetime.now(timezone.utc) - created).days)
        return {
            'age_days':   age_days,
            'registered': str(created.date()),
            'registrar':  str(w.registrar or 'Unknown'),
        }
    except Exception as e:
        return {'error': str(e)}


def analyze_metadata(url: str) -> dict:
    """
    Checks domain age, SSL certificate, and redirect chain.
    WHOIS: 5s timeout. Redirect check: 4s timeout.
    """
    risk_score = 0
    flags      = []
    details    = {}

    try:
        ext    = tldextract.extract(url)
        domain = ext.registered_domain
        details['domain'] = domain

        # ── CHECK 1: Domain Age (WHOIS with 5s timeout) ───────────────────────
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_whois_lookup, domain)
                whois_data = future.result(timeout=5)

            if 'error' in whois_data:
                flags.append('Domain age could not be verified (WHOIS unavailable)')
            else:
                age = whois_data['age_days']
                details.update({
                    'domain_age_days':   age,
                    'domain_registered': whois_data['registered'],
                    'registrar':         whois_data['registrar'],
                })
                if age < 30:
                    risk_score += 45
                    flags.append(f'Domain registered only {age} days ago — extremely high risk')
                elif age < 90:
                    risk_score += 30
                    flags.append(f'Domain registered {age} days ago — less than 3 months old')
                elif age < 365:
                    risk_score += 12
                    flags.append(f'Domain less than 1 year old ({age} days)')
                else:
                    details['age_note'] = f'Domain is {age // 365}+ years old — positive signal'

        except FuturesTimeout:
            flags.append('WHOIS lookup timed out — domain age unverified')
        except Exception as e:
            flags.append(f'WHOIS error: {str(e)[:60]}')

        # ── CHECK 2: HTTPS ────────────────────────────────────────────────────
        if not url.startswith('https://'):
            risk_score += 25
            flags.append('No HTTPS — connection is unencrypted')
        else:
            details['ssl'] = 'HTTPS present'

        # ── CHECK 3: Redirect chain (4s timeout) ──────────────────────────────
        try:
            resp           = requests.head(url, allow_redirects=True, timeout=4)
            redirect_count = int(len(resp.history))
            final_url      = resp.url

            details['redirects'] = redirect_count
            details['final_url'] = final_url

            if redirect_count >= 3:
                risk_score += 15
                flags.append(f'{redirect_count} redirects detected — destination hidden')

            orig_domain  = tldextract.extract(url).registered_domain
            final_domain = tldextract.extract(final_url).registered_domain
            if orig_domain != final_domain and final_domain:
                risk_score += 20
                flags.append(f'Redirects to a different domain: {final_domain}')

        except requests.Timeout:
            details['redirects'] = 0
        except Exception:
            details['redirects'] = 0

    except Exception as e:
        flags.append(f'Metadata error: {str(e)[:80]}')

    return {
        'score':   int(min(risk_score, 100)),
        'flags':   flags,
        'details': details
    }
