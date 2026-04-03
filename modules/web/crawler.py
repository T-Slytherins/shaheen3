#!/usr/bin/env python3
"""Web crawler — Katana + custom Python crawler + JS URL extraction"""

import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from core.logger import get_logger

log = get_logger("Crawler")

HREF_RE = re.compile(r'href=["\']([^"\'<>]+)["\']', re.IGNORECASE)
SRC_RE  = re.compile(r'src=["\']([^"\'<>]+)["\']',  re.IGNORECASE)
ACT_RE  = re.compile(r'action=["\']([^"\'<>]+)["\']', re.IGNORECASE)
MET_RE  = re.compile(r'method=["\']([^"\'<>]+)["\']', re.IGNORECASE)
INP_RE  = re.compile(r'<input[^>]+name=["\']([^"\'<>]+)["\']', re.IGNORECASE)
FORM_RE = re.compile(r'<form[^>]*>(.*?)</form>', re.DOTALL | re.IGNORECASE)


class CrawlerModule:
    def __init__(self, cfg):
        self.cfg      = cfg
        self._js_urls = []

    def run(self, targets: list, out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        for url in targets[:10]:
            log.info(f"  [Crawler] Crawling {url}")
            katana_urls = self._katana(url, out_dir)
            python_urls = self._python_crawl(url)
            combined    = list(set(katana_urls + python_urls))
            js_urls     = [u for u in combined if u.endswith(".js")]
            self._js_urls.extend(js_urls)
            results[url] = {
                "total":  len(combined),
                "js":     js_urls,
                "urls":   combined[:500],
                "forms":  self._extract_forms(url),
                "apis":   [u for u in combined
                           if "/api/" in u or "/v1/" in u or "/v2/" in u],
            }

        return results

    def get_js_urls(self) -> list:
        return list(set(self._js_urls))

    def _katana(self, url: str, out_dir: Path) -> list:
        depth = self.cfg.get("depth", 3)
        domain = urlparse(url).netloc
        out_f  = out_dir / f"{domain}.txt"
        cmd = [
            "katana", "-u", url,
            "-d", str(depth),
            "-silent",
            "-o", str(out_f),
            "-timeout", str(self.cfg.get("timeout", 10)),
        ]
        try:
            subprocess.run(cmd, timeout=180, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if out_f.exists():
                with open(out_f) as f:
                    return [ln.strip() for ln in f if ln.strip()]
        except Exception as e:
            log.debug(f"  [Katana] error: {e}")
        return []

    def _python_crawl(self, start_url: str, max_pages: int = 100) -> list:
        visited = set()
        queue   = [start_url]
        domain  = urlparse(start_url).netloc
        found   = []
        session = requests.Session()
        session.headers["User-Agent"] = self.cfg.get(
            "user_agent", "Mozilla/5.0 (X11; Linux x86_64) Shaheen3/1.0"
        )

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                r = session.get(
                    url,
                    timeout=self.cfg.get("timeout", 10),
                    verify=False,
                    allow_redirects=True,
                )
                found.append(url)
                for href in HREF_RE.findall(r.text) + SRC_RE.findall(r.text):
                    full = urljoin(url, href)
                    if urlparse(full).netloc == domain and full not in visited:
                        queue.append(full)
            except Exception:
                pass
        return found

    def _extract_forms(self, url: str) -> list:
        try:
            r     = requests.get(url, timeout=self.cfg.get("timeout", 10), verify=False)
            forms = FORM_RE.findall(r.text)
            result = []
            for form_body in forms:
                action = ACT_RE.search(form_body)
                method = MET_RE.search(form_body)
                inputs = INP_RE.findall(form_body)
                result.append({
                    "action": action.group(1) if action else "",
                    "method": method.group(1) if method else "get",
                    "inputs": inputs,
                })
            return result
        except Exception:
            return []
