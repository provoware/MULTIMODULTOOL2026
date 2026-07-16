#!/usr/bin/env python3
"""One-time repository patch for manifest, import and accessibility hardening."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dashboard-studio-ultimate-pro-v3.1.0.html"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count