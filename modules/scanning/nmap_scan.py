#!/usr/bin/env python3
"""Nmap port scanning — full ports, service detection, scripts"""

import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from core.logger import get_logger

log = get_logger("Nmap")


class NmapModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, targets: list, out_dir: Path) -> dict:
        log.info(f"[Nmap] Scanning {len(targets)} target(s)")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        all_results = {}
        for target in targets[:20]:  # cap to 20 hosts
            result = self._scan_host(target, out_dir)
            if result:
                all_results[target] = result

        return all_results

    def _scan_host(self, target: str, out_dir: Path) -> dict:
        # Build nmap command
        ports  = self.cfg.get("ports", "1-65535")
        fast   = self.cfg.get("fast",  False)

        if fast:
            port_arg = ["--top-ports", "1000"]
        else:
            port_arg = ["-p", ports]

        safe_name = target.replace(".", "_").replace("/", "_")
        xml_out   = out_dir / f"{safe_name}.xml"

        cmd = [
            "nmap",
            "-sV",           # service version detection
            "-sC",           # default scripts
            "--script", "vuln,auth,default",
            "-O",            # OS detection
            "--open",        # only open ports
            "-T4",           # aggressive timing
            "-oX", str(xml_out),
        ] + port_arg + [target]

        log.info(f"  [Nmap] {target} ...")
        try:
            subprocess.run(cmd, timeout=600, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=True)
            return self._parse_xml(xml_out)
        except subprocess.CalledProcessError:
            return self._parse_xml(xml_out)  # parse partial results
        except Exception as e:
            log.warning(f"  [Nmap] {target} error: {e}")
            return {"error": str(e)}

    def _parse_xml(self, xml_path: Path) -> dict:
        if not xml_path.exists():
            return {}
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            result = {"hosts": []}

            for host in root.findall("host"):
                host_data = {"ip": "", "hostname": "", "ports": [], "os": ""}

                # IP
                for addr in host.findall("address"):
                    if addr.get("addrtype") == "ipv4":
                        host_data["ip"] = addr.get("addr", "")

                # Hostname
                hostnames = host.find("hostnames")
                if hostnames is not None:
                    hn = hostnames.find("hostname")
                    if hn is not None:
                        host_data["hostname"] = hn.get("name", "")

                # Ports
                ports_el = host.find("ports")
                if ports_el is not None:
                    for port in ports_el.findall("port"):
                        state = port.find("state")
                        if state is None or state.get("state") != "open":
                            continue
                        service = port.find("service")
                        p = {
                            "port":     port.get("portid"),
                            "protocol": port.get("protocol"),
                            "service":  service.get("name", "") if service is not None else "",
                            "version":  service.get("version", "") if service is not None else "",
                            "product":  service.get("product", "") if service is not None else "",
                        }
                        # Script output
                        scripts = []
                        for scr in port.findall("script"):
                            scripts.append({"id": scr.get("id"), "output": scr.get("output", "")[:200]})
                        p["scripts"] = scripts
                        host_data["ports"].append(p)

                # OS
                osmatch = host.find("os/osmatch")
                if osmatch is not None:
                    host_data["os"] = osmatch.get("name", "")

                result["hosts"].append(host_data)

            return result
        except Exception as e:
            log.warning(f"  [Nmap] XML parse error: {e}")
            return {}
