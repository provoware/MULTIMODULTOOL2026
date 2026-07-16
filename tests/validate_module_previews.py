#!/usr/bin/env python3
"""Prueft kleine Modulvorschauen ohne Browserausfuehrung."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUICKTEXT = ROOT / "modules" / "schnell-text-speicher"
SYSTEMBUNDLE = ROOT / "modules" / "systemmodule-buendel"


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def read_entry(module_dir: Path) -> dict[str, str | None]:
    manifest = json.loads((module_dir / "module.manifest.json").read_text(encoding="utf-8"))
    return manifest.get("entry", {})


def main() -> int:
    errors: list[str] = []
    quick_entry = read_entry(QUICKTEXT)
    preview = (QUICKTEXT / "preview.html").read_text(encoding="utf-8")
    quick_html = (QUICKTEXT / "module.html").read_text(encoding="utf-8")
    quick_css = (QUICKTEXT / "module.css").read_text(encoding="utf-8")
    system_html = (SYSTEMBUNDLE / "module.html").read_text(encoding="utf-8")
    system_css = (SYSTEMBUNDLE / "module.css").read_text(encoding="utf-8")

    expected_html = quick_entry.get("html")
    expected_css = quick_entry.get("css")
    require(expected_html == "module.html", errors, "Quicktext-Manifest nennt nicht module.html")
    require(expected_css == "module.css", errors, "Quicktext-Manifest nennt nicht module.css")
    require(f'href="{expected_css}"' in preview, errors, "Quicktext-Vorschau bindet Manifest-CSS nicht ein")
    require(f'fetch("{expected_html}")' in preview, errors, "Quicktext-Vorschau laedt Manifest-HTML nicht")
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
