#!/usr/bin/env python3
"""Breach data lookup via HaveIBeenPwned-compatible APIs"""

import requests
from core.logger import get_logger

log = get_logger("Breach")

HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"


class BreachModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, domain: str) -> dict:
        log.info(f"[Breach] Checking domain: {domain}")
        results = {"domain_check": self._domain_check(domain)}
        return results

    def _domain_check(self, domain: str) -> list:
        """Check HIBP for breaches associated with domain."""
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breaches",
                headers={"User-Agent": "Shaheen3-Scanner"},
                timeout=15
            )
            if r.status_code == 200:
                all_breaches = r.json()
                # Filter to domain-related breaches
                related = [b for b in all_breaches
                           if domain.lower() in b.get("Domain", "").lower()]
                log.info(f"  [Breach] {len(related)} related breaches found")
                return [{
                    "name":         b.get("Name"),
                    "title":        b.get("Title"),
                    "breach_date":  b.get("BreachDate"),
                    "pwn_count":    b.get("PwnCount"),
                    "data_classes": b.get("DataClasses", []),
                    "description":  b.get("Description", "")[:300],
                } for b in related]
        except Exception as e:
            log.debug(f"  [Breach] HIBP check error: {e}")
        return []
