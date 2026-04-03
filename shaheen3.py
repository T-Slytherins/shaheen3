#!/usr/bin/env python3
"""
Shaheen 3 — Main Entry Point
Crafted by Professor Snape
"""

import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from core.banner    import print_banner
from core.config    import Config
from core.logger    import get_logger
from core.scheduler import TaskScheduler

from modules.recon.whois_lookup     import WhoisModule
from modules.recon.subdomain_enum   import SubdomainModule
from modules.recon.dns_enum         import DNSModule
from modules.recon.certificate_scan import CertModule
from modules.recon.email_harvest    import EmailModule
from modules.recon.breach_data      import BreachModule

from modules.scanning.nmap_scan  import NmapModule
from modules.scanning.http_probe import HTTPProbeModule

from modules.vuln.nuclei_scan    import NucleiModule
from modules.web.crawler         import CrawlerModule
from modules.web.screenshot      import ScreenshotModule
from modules.evasion.waf_bypass  import WAFBypassModule
from modules.exploit.chain       import ExploitChainModule

from reports.html_report import HTMLReportGenerator

log = get_logger("Shaheen3")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shaheen3",
        description="Shaheen 3 — Elite Penetration Testing & OSINT Suite by Professor Snape",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 shaheen3.py -d example.com
  python3 shaheen3.py -d example.com --full --threads 20
  python3 shaheen3.py -d example.com --modules recon,scan,vuln
  python3 shaheen3.py -d example.com --proxy http://127.0.0.1:8080
  python3 shaheen3.py --api
  python3 shaheen3.py --schedule daily 09:00
        """,
    )

    p.add_argument("-d", "--domain",  help="Target domain (e.g. example.com)")
    p.add_argument("-l", "--list",    help="File with list of domains (one per line)")
    p.add_argument("-o", "--output",  default="output", help="Output directory [default: output]")

    p.add_argument("--full",    action="store_true", help="Run ALL modules")
    p.add_argument("--modules", default="recon,scan,vuln,web",
                   help="Comma-separated modules: recon,scan,vuln,web,exploit,evasion")

    p.add_argument("--no-passive", action="store_true", help="Skip passive DNS/cert lookups")
    p.add_argument("--wordlist",   default=None,        help="Custom subdomain wordlist path")
    p.add_argument("--depth",      type=int, default=3, help="Crawler depth [default: 3]")

    p.add_argument("--ports",  default="1-65535",  help="Port range [default: 1-65535]")
    p.add_argument("--fast",   action="store_true", help="Fast scan (top 1000 ports only)")
    p.add_argument("--udp",    action="store_true", help="Include UDP scanning")

    p.add_argument("--nuclei-severity", default="critical,high,medium",
                   help="Nuclei severity filter [default: critical,high,medium]")
    p.add_argument("--exploit-chain", action="store_true", help="Run automated exploit chaining")
    p.add_argument("--waf-bypass",    action="store_true", help="Enable WAF evasion techniques")

    p.add_argument("--proxy",   default=None, help="HTTP proxy (e.g. http://127.0.0.1:8080)")
    p.add_argument("--rate",    type=int, default=150, help="Requests/second [default: 150]")
    p.add_argument("--timeout", type=int, default=10,  help="Timeout in seconds [default: 10]")

    p.add_argument("--threads", type=int, default=10, help="Parallel threads [default: 10]")

    p.add_argument("--api",      action="store_true", help="Launch REST API server")
    p.add_argument("--api-port", type=int, default=5000, help="API port [default: 5000]")
    p.add_argument("--schedule", nargs=2, metavar=("FREQ","TIME"),
                   help="Schedule scan: FREQ=(daily|weekly) TIME=HH:MM")

    p.add_argument("--report-title", default=None, help="Custom HTML report title")
    p.add_argument("--no-report",    action="store_true", help="Skip HTML report generation")
    p.add_argument("--screenshots",  action="store_true", help="Capture full-page screenshots")

    p.add_argument("--config",  default=None, help="Path to custom config file (JSON)")
    p.add_argument("--creds",   default=None, help="Path to credentials JSON file")
    p.add_argument("--silent",  action="store_true", help="Suppress banner output")
    p.add_argument("--version", action="version", version="Shaheen 3 v1.0 — by Professor Snape")

    return p


class Shaheen3:
    def __init__(self, args: argparse.Namespace):
        self.args    = args
        self.cfg     = Config(args)
        self.results = {}
        self.start_t = time.time()
        self.out_dir = Path(args.output)
        self._make_dirs()

    def _make_dirs(self):
        for sub in ("reports","screenshots","crawl","dns","emails","nmap","vuln","logs"):
            (self.out_dir / sub).mkdir(parents=True, exist_ok=True)

    def _active_modules(self) -> set:
        if self.args.full:
            return {"recon","scan","vuln","web","exploit","evasion"}
        return set(self.args.modules.split(","))

    def run(self, domain: str):
        mods = self._active_modules()
        log.info(f"[TARGET] {domain}  |  Modules: {', '.join(sorted(mods))}")

        if "recon" in mods:
            log.info("━━━━━  PHASE 1 : RECONNAISSANCE  ━━━━━")
            self.results["recon"] = self._phase_recon(domain)

        if "scan" in mods:
            log.info("━━━━━  PHASE 2 : PORT & SERVICE SCAN  ━━━━━")
            subs = self.results.get("recon", {}).get("subdomains", {}).get("all", [domain])
            self.results["scan"] = self._phase_scan(domain, subs)

        if "vuln" in mods:
            log.info("━━━━━  PHASE 3 : VULNERABILITY SCAN  ━━━━━")
            live = self.results.get("scan", {}).get("live_hosts", [f"https://{domain}"])
            self.results["vuln"] = self._phase_vuln(domain, live)

        if "web" in mods:
            log.info("━━━━━  PHASE 4 : WEB CRAWL  ━━━━━")
            live = self.results.get("scan", {}).get("live_hosts", [f"https://{domain}"])
            self.results["web"] = self._phase_web(domain, live)

        if "evasion" in mods or getattr(self.args, "waf_bypass", False):
            log.info("━━━━━  PHASE 5 : WAF / IDS EVASION  ━━━━━")
            self.results["evasion"] = WAFBypassModule(self.cfg).run(domain)

        if "exploit" in mods or getattr(self.args, "exploit_chain", False):
            log.info("━━━━━  PHASE 6 : EXPLOIT CHAINING  ━━━━━")
            self.results["exploit"] = ExploitChainModule(self.cfg).run(domain, self.results)

        elapsed = time.time() - self.start_t
        self.results["meta"] = {
            "domain":    domain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed":   f"{elapsed:.1f}s",
            "modules":   list(mods),
        }

        self._save_json(domain)

        if not self.args.no_report:
            title = self.args.report_title or f"Shaheen 3 Report — {domain}"
            rpt   = HTMLReportGenerator(self.cfg, self.out_dir / "reports")
            path  = rpt.generate(domain, self.results, title=title)
            log.info(f"[REPORT] {path}")

        log.info(f"[DONE] Scan completed in {elapsed:.1f}s")
        return self.results

    def _phase_recon(self, domain: str) -> dict:
        results = {}
        tasks = {
            "whois":    (WhoisModule(self.cfg).run,     domain),
            "subdomains":(SubdomainModule(self.cfg).run, domain),
            "dns":      (DNSModule(self.cfg).run,       domain),
            "certs":    (CertModule(self.cfg).run,      domain),
            "emails":   (EmailModule(self.cfg).run,     domain),
            "breaches": (BreachModule(self.cfg).run,    domain),
        }
        with ThreadPoolExecutor(max_workers=self.args.threads) as ex:
            futures = {ex.submit(fn, arg): name for name, (fn, arg) in tasks.items()}
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    results[name] = fut.result()
                    log.info(f"  [OK] {name}")
                except Exception as e:
                    log.warning(f"  [!!] {name} failed: {e}")
                    results[name] = {}
        return results

    def _phase_scan(self, domain: str, subdomains: list) -> dict:
        nmap  = NmapModule(self.cfg)
        probe = HTTPProbeModule(self.cfg)
        return {
            "nmap":       nmap.run(subdomains, self.out_dir / "nmap"),
            "live_hosts": probe.run(subdomains),
            "http_info":  probe.get_http_info(),
        }

    def _phase_vuln(self, domain: str, live_hosts: list) -> dict:
        return NucleiModule(self.cfg).run(live_hosts, self.out_dir / "vuln")

    def _phase_web(self, domain: str, live_hosts: list) -> dict:
        crawler    = CrawlerModule(self.cfg)
        screenshot = ScreenshotModule(self.cfg)
        return {
            "crawl":       crawler.run(live_hosts, self.out_dir / "crawl"),
            "js_urls":     crawler.get_js_urls(),
            "screenshots": screenshot.run(live_hosts, self.out_dir / "screenshots"),
        }

    def _save_json(self, domain: str):
        safe = domain.replace(".", "_")
        ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out  = self.out_dir / f"shaheen3_{safe}_{ts}.json"
        with open(out, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        log.info(f"[JSON] {out}")


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if not args.silent:
        print_banner()

    if args.api:
        from core.api import start_api
        start_api(port=args.api_port)
        return

    if args.schedule:
        freq, t = args.schedule
        sched   = TaskScheduler()
        sched.schedule(freq, t, args)
        sched.run_forever()
        return

    if not args.domain and not args.list:
        parser.error("Provide a target: -d <domain> or -l <file>")

    domains = []
    if args.domain:
        domains.append(args.domain.strip().lower().replace("https://","").replace("http://",""))
    if args.list:
        with open(args.list) as f:
            domains += [ln.strip() for ln in f if ln.strip()]

    engine = Shaheen3(args)
    for domain in domains:
        log.info(f"[*] Starting scan: {domain}")
        engine.run(domain)


if __name__ == "__main__":
    main()
