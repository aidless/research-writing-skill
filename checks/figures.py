#!/usr/bin/env python3
"""Regenerate the fixture SVG and compare sha256. Does not render a PNG."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLOT = ROOT / "checks" / "figure" / "plot_series.py"
DATA = ROOT / "checks" / "figure" / "data.csv"
EXPECTED = ROOT / "checks" / "figure" / "expected.sha256"


def regenerated_sha256() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / "figure.svg"
        completed = subprocess.run(
            [sys.executable, str(PLOT), str(DATA), str(destination)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "plot_series failed")
        return hashlib.sha256(destination.read_bytes()).hexdigest()


def locked_sha256() -> str:
    return EXPECTED.read_text(encoding="utf-8").strip()
