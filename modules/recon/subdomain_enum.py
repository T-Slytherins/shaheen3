#!/usr/bin/env python3
"""
Multi-source subdomain enumeration:
  Amass, Subfinder, Assetfinder, DNS brute force, Certificate Transparency
"""

import subprocess
import socket
import ssl
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core.logger import get_logger

log = get_logger("Subdomains")

CERT_API  = "https://crt.sh/?q=%25.{}&output=json"
BUFFEROVER = "https://dns.bufferover.run/dns?q=.{}"


class SubdomainModule:
    def __init__(self, cfg):
        self.cfg = cfg
        self._all: set = set()

    def run(self, domain: str) -> dict:
        log.info(f"[Subdomains] Enumerating: {domain}")
        sources = {}

        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {
                ex.submit(self._amass,       domain): "amass",
                ex.submit(self._subfinder,   domain): "subfinder",
                ex.submit(self._assetfinder, domain): "assetfinder",
                ex.submit(self._crtsh,       domain): "crtsh",
                ex.submit(self._bufferover,  domain): "bufferover",
                ex.submit(self._dns_brute,   domain): "dns_brute",
            }
            from concurrent.futures import as_completed
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    found = fut.result()
                    sources[name] = found
                    self._all.update(found)
                    log.info(f"  [{name}] {len(found)} subdomains")
                except Exception as e:
                    log.warning(f"  [{name}] error: {e}")
                    sources[name] = []

        # Resolve alive ones
        alive = self._resolve(list(self._all), domain)
        return {"sources": sources, "all": sorted(self._all), "alive": alive}

    # ── Tool wrappers ─────────────────────────────────────────────
    def _run_tool(self, cmd: list, domain: str) -> list:
        try:
            out = subprocess.check_output(cmd, timeout=120, stderr=subprocess.DEVNULL)
            return [l.strip() for l in out.decode(errors="ignore").splitlines()
                    if l.strip().endswith(f".{domain}") or l.strip() == domain]
        except Exception:
            return []

    def _amass(self, domain: str) -> list:
        return self._run_tool(["amass", "enum", "-passive", "-d", domain], domain)

    def _subfinder(self, domain: str) -> list:
        return self._run_tool(["subfinder", "-d", domain, "-silent"], domain)

    def _assetfinder(self, domain: str) -> list:
        return self._run_tool(["assetfinder", "--subs-only", domain], domain)

    def _crtsh(self, domain: str) -> list:
        try:
            r = requests.get(CERT_API.format(domain), timeout=15)
            data = r.json()
            names = set()
            for entry in data:
                for n in entry.get("name_value", "").split("\n"):
                    n = n.strip().lower().lstrip("*.")
                    if n.endswith(domain):
                        names.add(n)
            return list(names)
        except Exception:
            return []

    def _bufferover(self, domain: str) -> list:
        try:
            r = requests.get(BUFFEROVER.format(domain), timeout=10)
            data = r.json()
            results = data.get("FDNS_A", []) + data.get("RDNS", [])
            subs = set()
            for entry in results:
                parts = entry.split(",")
                for p in parts:
                    p = p.strip().lower()
                    if p.endswith(f".{domain}"):
                        subs.add(p)
            return list(subs)
        except Exception:
            return []

    def _dns_brute(self, domain: str) -> list:
        """Basic DNS brute force with common prefixes."""
        wordlist_path = self.cfg.get("wordlist")
        if wordlist_path:
            try:
                with open(wordlist_path) as f:
                    words = [l.strip() for l in f if l.strip()]
            except Exception:
                words = self._default_words()
        else:
            words = self._default_words()

        found = []
        def _check(word):
            sub = f"{word}.{domain}"
            try:
                socket.getaddrinfo(sub, None, timeout=2)
                return sub
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=50) as ex:
            for r in ex.map(_check, words):
                if r:
                    found.append(r)
        return found

    def _default_words(self) -> list:
        return [
            "www","mail","ftp","api","dev","staging","test","beta","admin",
            "portal","app","blog","cdn","vpn","remote","secure","login","dashboard",
            "static","media","assets","img","docs","help","support","shop","store",
            "m","mobile","new","old","pre","prod","production","qa","demo","int","ext",
            "ns1","ns2","smtp","pop","imap","webmail","autodiscover","autoconfig",
        ]

    def _resolve(self, subdomains: list, domain: str) -> list:
        alive = []
        def _check(sub):
            try:
                socket.setdefaulttimeout(3)
                ip = socket.gethostbyname(sub)
                return {"subdomain": sub, "ip": ip}
            except Exception:
                return None
        with ThreadPoolExecutor(max_workers=30) as ex:
            for res in ex.map(_check, subdomains):
                if res:
                    alive.append(res)
        return alive
