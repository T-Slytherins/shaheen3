#!/usr/bin/env python3
"""Full DNS record enumeration + zone transfer attempts"""

import subprocess
from core.logger import get_logger

log = get_logger("DNS")

RECORD_TYPES = ["A","AAAA","MX","NS","TXT","SOA","CNAME","PTR","SRV","CAA","DMARC","SPF"]


class DNSModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, domain: str) -> dict:
        log.info(f"[DNS] Full enumeration: {domain}")
        results = {"records": {}, "zone_transfers": [], "dnsec": False}

        # Standard records
        for rtype in RECORD_TYPES:
            results["records"][rtype] = self._dig(domain, rtype)

        # DMARC / SPF
        results["records"]["DMARC"] = self._dig(f"_dmarc.{domain}", "TXT")
        results["records"]["SPF"]   = [r for r in results["records"].get("TXT", [])
                                        if "v=spf" in r.lower()]

        # Zone transfer
        ns_list = results["records"].get("NS", [])
        for ns in ns_list:
            zt = self._zone_transfer(domain, ns)
            if zt:
                results["zone_transfers"].append({"ns": ns, "records": zt})
                log.warning(f"  [!!] Zone transfer SUCCESS on {ns}")

        # DNSSEC check
        results["dnssec"] = self._check_dnssec(domain)

        return results

    def _dig(self, name: str, rtype: str) -> list:
        try:
            out = subprocess.check_output(
                ["dig", "+short", name, rtype],
                timeout=10, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            return [l.strip() for l in out.splitlines() if l.strip()]
        except Exception:
            return []

    def _zone_transfer(self, domain: str, ns: str) -> list:
        try:
            out = subprocess.check_output(
                ["dig", "AXFR", domain, f"@{ns.rstrip('.')}"],
                timeout=15, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            if "Transfer failed" in out or "REFUSED" in out:
                return []
            return [l.strip() for l in out.splitlines() if l.strip() and not l.startswith(";")]
        except Exception:
            return []

    def _check_dnssec(self, domain: str) -> bool:
        try:
            out = subprocess.check_output(
                ["dig", "+dnssec", domain, "A"],
                timeout=10, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            return "RRSIG" in out
        except Exception:
            return False
