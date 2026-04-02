#!/usr/bin/env python3
"""Shaheen 3 — Task Scheduler (daily / weekly)"""

import time
import threading
from datetime import datetime, timedelta
from core.logger import get_logger

log = get_logger("Scheduler")


class TaskScheduler:
    def __init__(self):
        self._tasks = []
        self._running = False

    def schedule(self, frequency: str, run_time: str, args):
        """Register a scan job. frequency: 'daily'|'weekly', run_time: 'HH:MM'"""
        self._tasks.append({
            "frequency": frequency,
            "run_time":  run_time,
            "args":      args,
            "last_run":  None,
        })
        log.info(f"[Scheduler] Registered {frequency} scan at {run_time}")

    def _next_run(self, task) -> datetime:
        now = datetime.now()
        h, m = map(int, task["run_time"].split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        if task["frequency"] == "weekly":
            target += timedelta(days=6)
        return target

    def run_forever(self):
        self._running = True
        log.info("[Scheduler] Running. Press Ctrl+C to stop.")
        try:
            while self._running:
                now = datetime.now()
                for task in self._tasks:
                    nxt = self._next_run(task)
                    if task["last_run"] is None or now >= nxt:
                        self._fire(task)
                        task["last_run"] = now
                time.sleep(30)
        except KeyboardInterrupt:
            log.info("[Scheduler] Stopped.")

    def _fire(self, task):
        from shaheen3 import Shaheen3
        log.info(f"[Scheduler] Firing scan: {task['args'].domain}")
        t = threading.Thread(target=Shaheen3(task["args"]).run,
                             args=(task["args"].domain,), daemon=True)
        t.start()
