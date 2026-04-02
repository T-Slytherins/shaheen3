#!/usr/bin/env python3
"""Full-page screenshot capture via Aquatone / Gowitness / chromium"""

import subprocess
import os
from pathlib import Path
from core.logger import get_logger

log = get_logger("Screenshot")


class ScreenshotModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, targets: list, out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        for url in targets[:20]:
            path = self._capture(url, out_dir)
            if path:
                results[url] = str(path)
                log.info(f"  [Screenshot] {url} -> {path}")

        return results

    def _capture(self, url: str, out_dir: Path):
        # Try Gowitness first
        fname = url.replace("://", "_").replace("/", "_").replace(":", "_") + ".png"
        out   = out_dir / fname

        # gowitness
        if self._try_gowitness(url, out):
            return out

        # Aquatone (single URL mode)
        if self._try_aquatone(url, out_dir):
            return out_dir

        # Chromium headless fallback
        if self._try_chromium(url, out):
            return out

        return None

    def _try_gowitness(self, url: str, out: Path) -> bool:
        try:
            subprocess.run(
                ["gowitness", "single", "--url", url, "--screenshot-path", str(out)],
                timeout=30, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return out.exists()
        except Exception:
            return False

    def _try_aquatone(self, url: str, out_dir: Path) -> bool:
        try:
            urls_file = out_dir / "urls.txt"
            with open(urls_file, "w") as f:
                f.write(url + "\n")
            subprocess.run(
                ["aquatone", "-out", str(out_dir)],
                stdin=open(urls_file),
                timeout=60, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def _try_chromium(self, url: str, out: Path) -> bool:
        for browser in ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable"):
            try:
                subprocess.run([
                    browser,
                    "--headless", "--no-sandbox",
                    "--disable-gpu",
                    f"--screenshot={out}",
                    "--window-size=1920,1080",
                    url
                ], timeout=30, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if out.exists():
                    return True
            except Exception:
                continue
        return False
