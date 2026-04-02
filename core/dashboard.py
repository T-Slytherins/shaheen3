#!/usr/bin/env python3
"""
Real-time progress dashboard using Rich library.
Displays live scan progress, module status, and findings counter.
"""

import threading
import time
from datetime import datetime

try:
    from rich.console import Console
    from rich.table   import Table
    from rich.live    import Live
    from rich.panel   import Panel
    from rich.columns import Columns
    from rich.text    import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from core.logger import get_logger

log = get_logger("Dashboard")


class Dashboard:
    """
    Real-time scan dashboard.
    Usage:
        dash = Dashboard()
        with dash.live_context():
            dash.update_module("Whois", "running")
            dash.add_finding("critical", "SQL Injection on /login")
    """

    def __init__(self):
        self._modules  = {}
        self._findings = {"critical": [], "high": [], "medium": [], "low": [], "info": []}
        self._start    = time.time()
        self._lock     = threading.Lock()
        self._console  = Console() if RICH_AVAILABLE else None

    def update_module(self, name: str, status: str, detail: str = ""):
        with self._lock:
            icon = {"running": "⚡", "done": "✓", "error": "✗", "skipped": "–"}.get(status, "?")
            self._modules[name] = {"status": status, "icon": icon, "detail": detail}
        if not RICH_AVAILABLE:
            log.info(f"  [{icon}] {name}: {status} {detail}")

    def add_finding(self, severity: str, desc: str):
        with self._lock:
            self._findings.setdefault(severity.lower(), []).append(desc)

    def live_context(self):
        if not RICH_AVAILABLE:
            return _NoopContext()
        return Live(self._render(), console=self._console, refresh_per_second=4)

    def _render(self):
        elapsed = int(time.time() - self._start)

        # Module table
        tbl = Table(title="Module Status", border_style="dim", expand=True)
        tbl.add_column("Module", style="cyan")
        tbl.add_column("Status", justify="center")
        tbl.add_column("Detail", style="dim")
        for name, info in self._modules.items():
            colour = {"done": "green", "running": "yellow",
                      "error": "red", "skipped": "dim"}.get(info["status"], "white")
            tbl.add_row(name, f"[{colour}]{info['icon']} {info['status']}[/]",
                        info.get("detail", ""))

        # Findings summary
        sev_text = Text()
        colours  = {"critical":"red","high":"orange1","medium":"yellow","low":"green","info":"cyan"}
        for sev, items in self._findings.items():
            if items:
                sev_text.append(f"  {sev.upper()}: {len(items)}", style=colours.get(sev,"white"))
                sev_text.append("  ")

        panel = Panel(Columns([tbl, sev_text]), title=f"[bold cyan]SHAHEEN 3[/] — {elapsed}s elapsed")
        return panel

    def print_summary(self):
        if not RICH_AVAILABLE:
            return
        self._console.print(self._render())


class _NoopContext:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def update(self, *_, **__): pass
