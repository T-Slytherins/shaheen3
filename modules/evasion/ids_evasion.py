#!/usr/bin/env python3
"""Dynamic IDS/IPS evasion — fragmentation, timing, decoys"""

import time
import random
import requests
from core.logger import get_logger

log = get_logger("IDSEvasion")


class IDSEvasionModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def get_evasive_session(self) -> requests.Session:
        """Returns a requests.Session pre-configured for IDS evasion."""
        session = requests.Session()
        session.headers.update(self._random_headers())
        if self.cfg.get("proxy"):
            p = self.cfg.get("proxy")
            session.proxies = {"http": p, "https": p}
        return session

    def adaptive_delay(self, min_ms: int = 100, max_ms: int = 2000):
        """Random delay to evade rate-based IDS signatures."""
        delay = random.randint(min_ms, max_ms) / 1000.0
        time.sleep(delay)

    def chunk_request(self, session: requests.Session, url: str,
                      data: dict, chunk_size: int = 3) -> requests.Response:
        """Send request data in small chunks to bypass content-based IDS."""
        items  = list(data.items())
        chunks = [dict(items[i:i+chunk_size]) for i in range(0, len(items), chunk_size)]
        response = None
        for chunk in chunks:
            response = session.get(url, params=chunk,
                                   timeout=self.cfg.get("timeout", 10), verify=False)
            self.adaptive_delay(50, 300)
        return response

    def rotate_user_agents(self) -> list:
        """Returns a pool of diverse user agents."""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605",
            "Googlebot/2.1 (+http://www.google.com/bot.html)",
            "curl/7.68.0",
            "python-requests/2.31.0",
        ]

    def _random_headers(self) -> dict:
        return {
            "User-Agent":       random.choice(self.rotate_user_agents()),
            "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language":  "en-US,en;q=0.9",
            "Accept-Encoding":  "gzip, deflate, br",
            "Connection":       "keep-alive",
            "Cache-Control":    "no-cache",
            "X-Forwarded-For":  f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "X-Real-IP":        f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
        }
