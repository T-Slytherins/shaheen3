#!/usr/bin/env python3
"""Certificate Transparency log scanning"""

import ssl
import socket
import requests
from core.logger import get_logger

log = get_logger("Certs")

CRT_API = "https://crt.sh/?q={}&output=json"


class CertModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, domain: str) -> dict:
        log.info(f"[Certs] Fetching certificate data: {domain}")
        results = {"crtsh": [], "live_cert": {}}
        results["crtsh"]    = self._crtsh(domain)
        results["live_cert"] = self._get_live_cert(domain)
        return results

    def _crtsh(self, domain: str) -> list:
        try:
            r    = requests.get(CRT_API.format(domain), timeout=20)
            data = r.json()
            seen = set()
            certs = []
            for entry in data:
                cid = entry.get("id")
                if cid in seen:
                    continue
                seen.add(cid)
                certs.append({
                    "id":          cid,
                    "logged_at":   entry.get("entry_timestamp", ""),
                    "not_before":  entry.get("not_before", ""),
                    "not_after":   entry.get("not_after", ""),
                    "common_name": entry.get("common_name", ""),
                    "issuer":      entry.get("issuer_name", ""),
                    "san":         entry.get("name_value", "").split("\n"),
                })
            log.info(f"  [Certs] {len(certs)} certificates found on crt.sh")
            return certs
        except Exception as e:
            log.warning(f"  [Certs] crt.sh error: {e}")
            return []

    def _get_live_cert(self, domain: str, port: int = 443) -> dict:
        try:
            ctx  = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        "subject":   dict(x[0] for x in cert.get("subject", [])),
                        "issuer":    dict(x[0] for x in cert.get("issuer", [])),
                        "version":   cert.get("version"),
                        "not_before": cert.get("notBefore"),
                        "not_after":  cert.get("notAfter"),
                        "san":        [v for _, v in cert.get("subjectAltName", [])],
                        "protocol":   ssock.version(),
                        "cipher":     ssock.cipher(),
                    }
        except Exception as e:
            log.debug(f"  [Certs] Live cert failed for {domain}: {e}")
            return {}
