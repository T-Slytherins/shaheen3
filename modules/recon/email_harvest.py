#!/usr/bin/env python3
"""Email harvesting via theHarvester and passive sources"""

import subprocess
import re
import requests
from core.logger import get_logger

log = get_logger("Email")


class EmailModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, domain: str) -> dict:
        log.info(f"[Email] Harvesting: {domain}")
        emails = set()

        # theHarvester
        harvested = self._theharvester(domain)
        emails.update(harvested)

        # Hunter.io (public API, no key required for basic results)
        hunter = self._hunter_io(domain)
        emails.update(hunter)

        # Scrape Google via passive search
        google = self._google_scrape(domain)
        emails.update(google)

        result = sorted(emails)
        log.info(f"  [Email] {len(result)} emails found")
        return {"emails": result, "count": len(result)}

    def _theharvester(self, domain: str) -> list:
        try:
            out = subprocess.check_output(
                ["theHarvester", "-d", domain, "-b", "all", "-l", "500"],
                timeout=120, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
            return list(set(re.findall(pattern, out)))
        except Exception as e:
            log.debug(f"  [Email] theHarvester error: {e}")
            return []

    def _hunter_io(self, domain: str) -> list:
        try:
            r = requests.get(
                f"https://hunter.io/api/v2/domain-search?domain={domain}&limit=100",
                timeout=15
            )
            data = r.json()
            return [e["value"] for e in data.get("data", {}).get("emails", [])]
        except Exception:
            return []

    def _google_scrape(self, domain: str) -> list:
        """Pattern-match emails from search snippets (no API key needed)."""
        pattern = r"[a-zA-Z0-9._%+\-]+@" + re.escape(domain)
        try:
            r = requests.get(
                f"https://www.google.com/search?q=site:{domain}+email",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15
            )
            return list(set(re.findall(pattern, r.text)))
        except Exception:
            return []
