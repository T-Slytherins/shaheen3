#!/usr/bin/env python3
"""Shaheen 3 — Centralised Logging"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

FMT = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
DATE_FMT = "%H:%M:%S"


def get_logger(name: str = "Shaheen3") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    # Console handler — INFO+
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(f"\033[96m{FMT}\033[0m", DATE_FMT))
    logger.addHandler(ch)

    # File handler — DEBUG+
    fh = logging.FileHandler(LOG_DIR / "shaheen3.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FMT, DATE_FMT))
    logger.addHandler(fh)

    return logger
