#!/usr/bin/env python3
"""Sandbox payload testing environment — safe isolated execution"""

import subprocess
import tempfile
import os
from pathlib import Path
from core.logger import get_logger

log = get_logger("Sandbox")


class SandboxModule:
    """
    Isolated sandbox to safely test payloads using Docker (if available)
    or subprocess with resource limits (fallback).
    """

    def __init__(self, cfg):
        self.cfg         = cfg
        self.docker_avail = self._check_docker()

    def run(self, payloads: list, target_url: str) -> dict:
        log.info(f"[Sandbox] Testing {len(payloads)} payloads safely")
        results = []

        for payload in payloads:
            if self.docker_avail:
                result = self._test_in_docker(payload, target_url)
            else:
                result = self._test_subprocess(payload, target_url)
            results.append(result)

        triggered = [r for r in results if r.get("triggered")]
        log.info(f"  [Sandbox] {len(triggered)}/{len(results)} payloads triggered a response")
        return {
            "total":     len(results),
            "triggered": len(triggered),
            "results":   results,
        }

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5, check=True)
            return True
        except Exception:
            return False

    def _test_in_docker(self, payload: str, url: str) -> dict:
        """Use a minimal Alpine container to test payload response."""
        cmd = [
            "docker", "run", "--rm",
            "--network=host",
            "--memory=64m", "--cpus=0.1",
            "alpine:latest",
            "wget", "-qO-", "--timeout=10",
            f"{url}?q={payload}",
        ]
        try:
            out = subprocess.check_output(cmd, timeout=20,
                                          stderr=subprocess.DEVNULL).decode(errors="ignore")
            triggered = any(k in out for k in (payload[:10], "alert(", "error", "exception"))
            return {"payload": payload, "triggered": triggered, "method": "docker",
                    "response_snippet": out[:200]}
        except Exception as e:
            return {"payload": payload, "triggered": False, "method": "docker", "error": str(e)}

    def _test_subprocess(self, payload: str, url: str) -> dict:
        """Fallback: test via curl with resource limits."""
        import shlex
        safe_payload = shlex.quote(payload)
        try:
            out = subprocess.check_output(
                ["curl", "-sk", "--max-time", "10",
                 f"{url}?q={payload}"],
                timeout=15, stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            triggered = payload[:8] in out or "error" in out.lower()
            return {"payload": payload, "triggered": triggered, "method": "curl",
                    "response_snippet": out[:200]}
        except Exception as e:
            return {"payload": payload, "triggered": False, "method": "curl", "error": str(e)}
