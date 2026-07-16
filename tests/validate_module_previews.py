#!/usr/bin/env python3
"""Prueft kleine Modulvorschauen ohne Browserausfuehrung."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUICKTEXT = ROOT / "modules" / "schnell-text-speicher"
SYSTEMBUNDLE = ROOT / "modules" / "systemmodule-buendel"


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    preview = (QUICKTEXT / "preview.html").read_text(encoding="utf-8")
    quick_html = (QUICKTEXT / "module.html").read_text(encoding="utf-8")
    quick_css = (QUICKTEXT / "module.css").read_text(encoding="utf-8")
    system_html = (SYSTEMBUNDLE / "module.html").read_text(encoding="utf-8")
    system_css = (SYSTEMBUNDLE / "module.css").read_text(encoding="utf-8")

    require('href="module.css"' in preview, errors, "Quicktext-Vorschau bindet module.css nicht ein")
    require('fetch("module.html")' in preview, errors, "Quicktext-Vorschau laedt module.html nicht")
    require('id="quicktext-title"' in quick_html, errors, "Quicktext-Modul hat keinen Titelanker")
    require('.quicktext-module' in quick_css, errors, "Quicktext-CSS ist nicht gekapselt")
    require('aria-labelledby="systembundle-title"' in system_html, errors, "Systembundle-Modul hat keinen Titelanker")
    require('Single-File-App bleibt maßgeblich' in system_html, errors, "Systembundle-Rueckbaupfad fehlt")
    require('.systembundle-module' in system_css, errors, "Systembundle-CSS ist nicht gekapselt")

    if errors:
        print("FEHLER: Modulvorschau unvollstaendig")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: Modulvorschauen geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
