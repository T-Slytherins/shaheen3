#!/usr/bin/env python3
"""Shaheen 3 — REST API Server (Flask)"""

import json
import threading
from pathlib import Path
from core.logger import get_logger

log = get_logger("API")


def start_api(port: int = 5000):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        log.error("Flask not installed. Run: pip install flask")
        return

    from core.config import Config
    import argparse

    app = Flask("Shaheen3-API")
    scan_results = {}

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "tool":    "Shaheen 3",
            "version": "1.0",
            "author":  "Professor Snape",
            "endpoints": ["/scan", "/results", "/status", "/health"],
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/scan", methods=["POST"])
    def scan():
        data   = request.get_json(force=True)
        domain = data.get("domain")
        if not domain:
            return jsonify({"error": "domain required"}), 400

        modules = data.get("modules", "recon,scan,vuln,web")

        # Build minimal args namespace
        args = argparse.Namespace(
            domain=domain, list=None, output="output",
            full=False, modules=modules,
            no_passive=False, wordlist=None, depth=3,
            ports="1-65535", fast=False, udp=False,
            nuclei_severity="critical,high,medium",
            exploit_chain=False, waf_bypass=False,
            proxy=None, rate=150, timeout=10, threads=10,
            api=False, api_port=5000, schedule=None,
            report_title=None, no_report=False, screenshots=False,
            config=None, creds=None, silent=True,
        )

        def _run():
            from shaheen3 import Shaheen3
            e = Shaheen3(args)
            result = e.run(domain)
            scan_results[domain] = result

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return jsonify({"status": "started", "domain": domain})

    @app.route("/results", methods=["GET"])
    def results():
        domain = request.args.get("domain")
        if domain:
            return jsonify(scan_results.get(domain, {"error": "not found"}))
        return jsonify({d: list(v.keys()) for d, v in scan_results.items()})

    @app.route("/status", methods=["GET"])
    def status():
        return jsonify({
            "active_scans": len(scan_results),
            "domains":      list(scan_results.keys()),
        })

    log.info(f"[API] Shaheen 3 REST API starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
