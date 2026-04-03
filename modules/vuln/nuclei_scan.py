#!/usr/bin/env python3
"""Nuclei vulnerability scanning with custom templates"""

import subprocess
import json
from pathlib import Path
from core.logger import get_logger

log = get_logger("Nuclei")

SEVERITIES = ["critical", "high", "medium", "low", "info"]


class NucleiModule:
    def __init__(self, cfg):
        self.cfg = cfg

    def run(self, targets: list, out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not targets:
            return {}

        # Write targets file
        targets_file = out_dir / "targets.txt"
        with open(targets_file, "w") as f:
            f.write("\n".join(targets))

        results = {}

        # Run with built-in templates
        builtin = self._run_nuclei(targets_file, out_dir, template_path=None)
        results["builtin"] = builtin

        # Run with custom templates
        custom_tpl = Path("nuclei_templates")
        if custom_tpl.exists() and any(custom_tpl.glob("*.yaml")):
            custom = self._run_nuclei(targets_file, out_dir, template_path=str(custom_tpl))
            results["custom"] = custom
        else:
            results["custom"] = []

        # Aggregate
        all_findings = builtin + results["custom"]
        results["summary"]   = self._summarize(all_findings)
        results["all"]       = all_findings
        results["risk_score"] = self._risk_score(all_findings)

        log.info(f"  [Nuclei] {len(all_findings)} findings | Risk Score: {results['risk_score']}")
        return results

    def _run_nuclei(self, targets_file: Path, out_dir: Path,
                    template_path: str = None) -> list:
        severity = self.cfg.get("nuclei_severity", "critical,high,medium")
        json_out  = out_dir / ("custom_results.json" if template_path else "results.json")

        cmd = [
            "nuclei",
            "-l",  str(targets_file),
            "-severity", severity,
            "-json",
            "-o",  str(json_out),
            "-silent",
            "-rate-limit", str(self.cfg.get("rate", 150)),
            "-timeout",    str(self.cfg.get("timeout", 10)),
        ]

        if template_path:
            cmd += ["-t", template_path]
        # Without -t, nuclei uses its auto-updated default templates

        if self.cfg.get("proxy"):
            cmd += ["-proxy", self.cfg.get("proxy")]

        try:
            subprocess.run(cmd, timeout=600, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            log.warning("  [Nuclei] 'nuclei' not found — install: go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")
        except Exception as e:
            log.warning(f"  [Nuclei] run error: {e}")

        return self._parse_json(json_out)

    def _parse_json(self, path: Path) -> list:
        findings = []
        if not path.exists():
            return findings
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        findings.append({
                            "template":    entry.get("template-id", ""),
                            "name":        entry.get("info", {}).get("name", ""),
                            "severity":    entry.get("info", {}).get("severity", "info"),
                            "host":        entry.get("host", ""),
                            "matched":     entry.get("matched-at", ""),
                            "description": entry.get("info", {}).get("description", ""),
                            "reference":   entry.get("info", {}).get("reference", []),
                            "tags":        entry.get("info", {}).get("tags", []),
                            "cvss_score":  entry.get("info", {}).get("classification", {}).get("cvss-score", 0),
                            "cve":         entry.get("info", {}).get("classification", {}).get("cve-id", []),
                        })
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.debug(f"  [Nuclei] parse error: {e}")
        return findings

    def _summarize(self, findings: list) -> dict:
        summary = {sev: 0 for sev in SEVERITIES}
        for f in findings:
            sev = f.get("severity", "info").lower()
            summary[sev] = summary.get(sev, 0) + 1
        return summary

    def _risk_score(self, findings: list) -> int:
        weights = {"critical": 10, "high": 7, "medium": 4, "low": 1, "info": 0}
        score = sum(weights.get(f.get("severity", "info").lower(), 0) for f in findings)
        return min(score, 100)
