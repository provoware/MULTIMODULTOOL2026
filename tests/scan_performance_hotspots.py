#!/usr/bin/env python3
"""Kleine Scan-Pruefung fuer bekannte Performance-Risiken der HTML-App."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dashboard-studio-ultimate-pro-v3.1.0.html"


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    errors: list[str] = []
    interval_count = source.count("setInterval(")
    if interval_count > 1:
        errors.append(f"Mehr als ein Dauertimer gefunden: {interval_count}")
    if re.search(r"setInterval\([^)]*saveState", source, re.DOTALL):
        errors.append("Dauertimer darf nicht direkt saveState aufrufen")
    if "function updateRunningTimers" not in source:
        errors.append("Timer-Anzeige ist nicht klar gekapselt")
    if "lastTimerSaveAt" not in source or "15000" not in source:
        errors.append("gedrosselte Timer-Speicherung fehlt")

    if errors:
        print("FEHLER: Performance-Hotspot-Scan fehlgeschlagen")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: Performance-Hotspot-Scan bestanden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
