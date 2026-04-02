#!/usr/bin/env python3
"""Shaheen 3 — Central Configuration Manager"""

import json
import os
from pathlib import Path


class Config:
    """Holds all runtime configuration derived from CLI args + optional JSON file."""

    DEFAULTS = {
        "timeout":           10,
        "threads":           10,
        "rate":              150,
        "depth":             3,
        "ports":             "1-65535",
        "nuclei_severity":   "critical,high,medium",
        "proxy":             None,
        "user_agent":        "Mozilla/5.0 (X11; Linux x86_64) Shaheen3/1.0",
        "dns_resolvers":     ["8.8.8.8", "1.1.1.1", "9.9.9.9"],
        "nuclei_templates":  "nuclei_templates",
        "wordlist":          None,
        "screenshots":       False,
        "waf_bypass":        False,
    }

    def __init__(self, args=None):
        self._data = dict(self.DEFAULTS)
        if args:
            self._load_args(args)
        if args and getattr(args, "config", None):
            self._load_file(args.config)
        if args and getattr(args, "creds", None):
            self._load_creds(args.creds)

    # ── loaders ───────────────────────────────────────────────────
    def _load_args(self, args):
        mapping = {
            "timeout":         "timeout",
            "threads":         "threads",
            "rate":            "rate",
            "depth":           "depth",
            "ports":           "ports",
            "nuclei_severity": "nuclei_severity",
            "proxy":           "proxy",
            "wordlist":        "wordlist",
            "screenshots":     "screenshots",
            "waf_bypass":      "waf_bypass",
        }
        for attr, key in mapping.items():
            val = getattr(args, attr, None)
            if val is not None:
                self._data[key] = val

    def _load_file(self, path: str):
        with open(path) as f:
            overrides = json.load(f)
        self._data.update(overrides)

    def _load_creds(self, path: str):
        with open(path) as f:
            self._data["credentials"] = json.load(f)

    # ── accessor ──────────────────────────────────────────────────
    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError(key)
        return self._data.get(key)

    def as_dict(self) -> dict:
        return dict(self._data)
