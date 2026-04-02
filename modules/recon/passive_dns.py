#!/usr/bin/env python3
"""Passive DNS & analytics tracking — multiple sources"""

import requests
from core.logger import get_logger

log = get_logger("PassiveDNS")

SOURCES = {
    "securitytrails": "https://api.securitytrails.com/v1/domain/{}/subdomains",
    "hackertarget":   "https://api.hackertarget.com/hostsearch/?q={}",
    "threatcrowd":    "https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={}",
    "urlscan":        "https://urlscan.io/api/v1/search/?q=domain:{}&size=100",
    "riddler":        "https://riddler.io/search/exportcsv?q=pld:{}",
}


class PassiveDNSModule:
    def __init__(self, cfg):
        self.cfg  = cfg
        self.creds = cfg.get("credentials") or {}

    def run(self, domain: str) -> dict:
        log.info(f"[PassiveDNS] Querying passive sources: {domain}")
        results = {}

        results["hackertarget"] = self._hackertarget(domain)
        results["threatcrowd"]  = self._threatcrowd(domain)
        results["urlscan"]      = self._urlscan(domain)

        all_subs = set()
        for src, data in results.items():
            all_subs.update(data.get("subdomains", []))

        results["merged"] = sorted(all_subs)
        log.info(f"  [PassiveDNS] {len(results['merged'])} unique subdomains via passive DNS")
        return results

    def _hackertarget(self, domain: str) -> dict:
        try:
            r    = requests.get(SOURCES["hackertarget"].format(domain), timeout=15)
            subs = set()
            for line in r.text.splitlines():
                parts = line.split(",")
                if parts and parts[0].strip().endswith(f".{domain}"):
                    subs.add(parts[0].strip())
            return {"subdomains": list(subs), "source": "hackertarget"}
        except Exception as e:
            log.debug(f"  [PassiveDNS] hackertarget error: {e}")
            return {"subdomains": [], "source": "hackertarget"}

    def _threatcrowd(self, domain: str) -> dict:
        try:
            r    = requests.get(SOURCES["threatcrowd"].format(domain), timeout=15)
            data = r.json()
            subs = data.get("subdomains", [])
            return {"subdomains": subs, "source": "threatcrowd",
                    "ips": data.get("resolutions", [])[:20]}
        except Exception as e:
            log.debug(f"  [PassiveDNS] threatcrowd error: {e}")
            return {"subdomains": [], "source": "threatcrowd"}

    def _urlscan(self, domain: str) -> dict:
        try:
            r    = requests.get(SOURCES["urlscan"].format(domain), timeout=15,
                                headers={"User-Agent": "Shaheen3/1.0"})
            data = r.json()
            subs = set()
            for result in data.get("results", []):
                page = result.get("page", {})
                sub  = page.get("domain", "")
                if sub.endswith(f".{domain}") or sub == domain:
                    subs.add(sub)
            return {"subdomains": list(subs), "source": "urlscan",
                    "count": data.get("total", 0)}
        except Exception as e:
            log.debug(f"  [PassiveDNS] urlscan error: {e}")
            return {"subdomains": [], "source": "urlscan"}
