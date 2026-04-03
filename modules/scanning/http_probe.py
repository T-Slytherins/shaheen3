#!/usr/bin/env python3
"""HTTP/HTTPS probing — live host detection, headers, tech fingerprinting"""

import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from core.logger import get_logger

log = get_logger("HTTPProbe")


class HTTPProbeModule:
    def __init__(self, cfg):
        self.cfg      = cfg
        self._info    = {}
        self._session = requests.Session()
        self._session.headers["User-Agent"] = cfg.get("user_agent",
            "Mozilla/5.0 (X11; Linux x86_64) Shaheen3/1.0")
        if cfg.get("proxy"):
            proxies = {"http": cfg.get("proxy"), "https": cfg.get("proxy")}
            self._session.proxies.update(proxies)

    def run(self, targets: list) -> list:
        """Probe all targets and return list of live HTTPS/HTTP URLs."""
        log.info(f"[HTTPProbe] Probing {len(targets)} hosts")
        live = []

        def _probe(host: str):
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}" if not host.startswith("http") else host
                try:
                    r = self._session.get(url, timeout=self.cfg.get("timeout", 10),
                                          allow_redirects=True, verify=False)
                    info = {
                        "url":            r.url,
                        "status":         r.status_code,
                        "title":          self._get_title(r.text),
                        "server":         r.headers.get("Server", ""),
                        "content_type":   r.headers.get("Content-Type", ""),
                        "content_length": len(r.content),
                        "technologies":   self._fingerprint(r),
                        "headers":        dict(r.headers),
                        "security_headers": self._check_security_headers(r.headers),
                    }
                    self._info[url] = info
                    return url
                except Exception:
                    pass
            return None

        with ThreadPoolExecutor(max_workers=self.cfg.get("threads", 10)) as ex:
            futures = {ex.submit(_probe, t): t for t in targets}
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    live.append(result)

        log.info(f"  [HTTPProbe] {len(live)} live hosts")
        return live

    def get_http_info(self) -> dict:
        return self._info

    def _get_title(self, html: str) -> str:
        m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        return m.group(1).strip()[:200] if m else ""

    def _fingerprint(self, r: requests.Response) -> list:
        techs = []
        html    = r.text
        headers = r.headers

        checks = {
            "WordPress":    ("wp-content" in html or "wp-includes" in html),
            "Drupal":       ("Drupal.settings" in html or "X-Generator" in headers and "Drupal" in headers.get("X-Generator","")),
            "Joomla":       ("/components/com_" in html),
            "Laravel":      ("laravel_session" in r.cookies),
            "Django":       ("csrfmiddlewaretoken" in html),
            "React":        ("__reactFiber" in html or "react-dom" in html),
            "Vue.js":       ("__vue__" in html or "vue.min.js" in html),
            "Angular":      ("ng-version" in html),
            "jQuery":       ("jquery" in html.lower()),
            "Bootstrap":    ("bootstrap" in html.lower()),
            "nginx":        ("nginx" in headers.get("Server", "").lower()),
            "Apache":       ("apache" in headers.get("Server", "").lower()),
            "IIS":          ("Microsoft-IIS" in headers.get("Server", "")),
            "Cloudflare":   ("cloudflare" in headers.get("Server", "").lower() or "CF-Ray" in headers),
            "AWS":          ("AmazonS3" in headers.get("Server", "") or "amazonaws.com" in r.url),
        }
        for tech, detected in checks.items():
            if detected:
                techs.append(tech)
        return techs

    def _check_security_headers(self, headers) -> dict:
        required = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Permissions-Policy",
            "X-XSS-Protection",
        ]
        return {h: headers.get(h, "MISSING") for h in required}
