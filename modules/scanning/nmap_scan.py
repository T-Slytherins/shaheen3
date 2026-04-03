#!/usr/bin/env python3
"""
Nmap port scanning — parallel execution, smart per-host timeout,
service detection, script scanning, XML parsing.
"""

import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from core.logger import get_logger

log = get_logger("Nmap")

# Per-host scan timeout (seconds). Full 65535-port scan needs time,
# but we cap it so one unresponsive host can't stall the whole phase.
HOST_TIMEOUT = 300   # 5 min per host
MAX_HOSTS    = 20    # scan at most 20 hosts to stay practical


class NmapModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, targets: list, out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Deduplicate and cap target list
        unique_targets = list(dict.fromkeys(targets))[:MAX_HOSTS]
        log.info(f"[Nmap] Scanning {len(unique_targets)} host(s) in parallel "
                 f"(max {self.cfg.get('threads', 5)} concurrent)")

        all_results = {}
        # Use fewer threads here — nmap is already I/O heavy
        workers = min(self.cfg.get("threads", 5), 5)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {
                ex.submit(self._scan_host, t, out_dir): t
                for t in unique_targets
            }
            for fut in as_completed(futures):
                target = futures[fut]
                try:
                    result = fut.result()
                    if result:
                        all_results[target] = result
                except Exception as e:
                    log.warning(f"  [Nmap] {target} unexpected error: {e}")

        return all_results

    def _scan_host(self, target: str, out_dir: Path) -> dict:
        fast  = self.cfg.get("fast", False)
        ports = self.cfg.get("ports", "1-65535")

        if fast:
            port_arg = ["--top-ports", "1000"]
        else:
            port_arg = ["-p", ports]

        safe_name = (target.replace(".", "_")
                           .replace("/", "_")
                           .replace(":", "_"))
        xml_out = out_dir / f"{safe_name}.xml"

        cmd = [
            "nmap",
            "-sV",                          # service version detection
            "-sC",                          # default scripts
            "--script", "vuln,auth,default",
            "-O",                           # OS detection
            "--open",                       # only open ports
            "-T4",                          # aggressive timing
            "--host-timeout", f"{HOST_TIMEOUT}s",  # per-host cap
            "--max-retries", "1",           # don't retry — speed
            "-oX", str(xml_out),
        ] + port_arg + [target]

        log.info(f"  [Nmap] {target} ...")
        try:
            subprocess.run(
                cmd,
                timeout=HOST_TIMEOUT + 10,   # slightly above nmap's own cap
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,                 # parse partial results on timeout
            )
        except subprocess.TimeoutExpired:
            log.warning(f"  [Nmap] {target} — host timeout, using partial results")
        except FileNotFoundError:
            log.error("  [Nmap] 'nmap' not found — install with: sudo apt install nmap")
            return {"error": "nmap not installed"}
        except Exception as e:
            log.warning(f"  [Nmap] {target} error: {e}")

        return self._parse_xml(xml_out)

    # ── XML parser ────────────────────────────────────────────────
    def _parse_xml(self, xml_path: Path) -> dict:
        if not xml_path.exists():
            return {}
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            result = {"hosts": []}

            for host in root.findall("host"):
                host_data = {"ip": "", "hostname": "", "ports": [], "os": ""}

                for addr in host.findall("address"):
                    if addr.get("addrtype") == "ipv4":
                        host_data["ip"] = addr.get("addr", "")

                hostnames = host.find("hostnames")
                if hostnames is not None:
                    hn = hostnames.find("hostname")
                    if hn is not None:
                        host_data["hostname"] = hn.get("name", "")

                ports_el = host.find("ports")
                if ports_el is not None:
                    for port in ports_el.findall("port"):
                        state = port.find("state")
                        if state is None or state.get("state") != "open":
                            continue
                        svc = port.find("service")
                        p = {
                            "port":     port.get("portid"),
                            "protocol": port.get("protocol"),
                            "service":  svc.get("name", "")    if svc is not None else "",
                            "version":  svc.get("version", "") if svc is not None else "",
                            "product":  svc.get("product", "") if svc is not None else "",
                        }
                        scripts = []
                        for scr in port.findall("script"):
                            scripts.append({
                                "id":     scr.get("id"),
                                "output": scr.get("output", "")[:300],
                            })
                        p["scripts"] = scripts
                        host_data["ports"].append(p)

                osmatch = host.find("os/osmatch")
                if osmatch is not None:
                    host_data["os"] = osmatch.get("name", "")

                result["hosts"].append(host_data)

            return result
        except ET.ParseError:
            return {}          # partial / empty XML — graceful degradation
        except Exception as e:
            log.debug(f"  [Nmap] XML parse error: {e}")
            return {}
