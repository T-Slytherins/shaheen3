#!/usr/bin/env python3
"""Whois & domain registration lookup"""

import subprocess
import re
from core.logger import get_logger

log = get_logger("Whois")


class WhoisModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, domain: str) -> dict:
        log.debug(f"[Whois] Querying: {domain}")
        result = {"domain": domain, "raw": "", "parsed": {}}
        try:
            out = subprocess.check_output(
                ["whois", domain], timeout=30, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            result["raw"]    = out
            result["parsed"] = self._parse(out)
        except Exception as e:
            log.warning(f"[Whois] Failed for {domain}: {e}")
            result["error"] = str(e)
        return result

    def _parse(self, raw: str) -> dict:
        fields = {
            "registrar":      r"Registrar:\s*(.+)",
            "creation_date":  r"Creation Date:\s*(.+)",
            "expiry_date":    r"Registry Expiry Date:\s*(.+)",
            "updated_date":   r"Updated Date:\s*(.+)",
            "name_servers":   r"Name Server:\s*(.+)",
            "registrant_org": r"Registrant Organization:\s*(.+)",
            "registrant_email": r"Registrant Email:\s*(.+)",
            "status":         r"Domain Status:\s*(.+)",
        }
        parsed = {}
        for key, pattern in fields.items():
            matches = re.findall(pattern, raw, re.IGNORECASE)
            parsed[key] = [m.strip() for m in matches] if matches else []
        return parsed
