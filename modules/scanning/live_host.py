#!/usr/bin/env python3
"""Live host detection — ICMP ping + TCP connect with threading"""

import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.logger import get_logger

log = get_logger("LiveHost")


class LiveHostModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, hosts: list) -> dict:
        log.info(f"[LiveHost] Checking {len(hosts)} hosts for liveness")
        alive  = []
        dead   = []

        with ThreadPoolExecutor(max_workers=self.cfg.get("threads", 20)) as ex:
            futures = {ex.submit(self._check, h): h for h in hosts}
            for fut in as_completed(futures):
                host = futures[fut]
                try:
                    if fut.result():
                        alive.append(host)
                    else:
                        dead.append(host)
                except Exception:
                    dead.append(host)

        log.info(f"  [LiveHost] {len(alive)} alive, {len(dead)} unreachable")
        return {"alive": alive, "dead": dead, "total": len(hosts)}

    def _check(self, host: str) -> bool:
        # Strip scheme
        host = host.replace("https://", "").replace("http://", "").split("/")[0]

        # ICMP ping (fast)
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", host],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=3
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        # TCP connect on common ports
        for port in (80, 443, 8080, 8443):
            try:
                with socket.create_connection((host, port), timeout=2):
                    return True
            except Exception:
                pass

        return False
