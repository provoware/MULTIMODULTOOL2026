#!/usr/bin/env python3
"""Gezielte Struktur- und Datenprüfung für das Provoware GenreTool Pro."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "provoware-genretool-pro"
APP_MANIFEST = ROOT / "manifests" / "MULTIMODULTOOL2026_02_AppManifest.json"
EXPECTED_CATEGORIES = ("genres", "moods", "styles", "effects", "themes", "special")
EXPECTED_TOTAL = 1800


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    manifest = json.loads((MODULE / "module.manifest.json").read_text(encoding="utf-8"))
    database = json.loads((MODULE / "genres_db.json").read_text(encoding="utf-8"))
    app = json.loads(APP_MANIFEST.read_text(encoding="utf-8"))
    html = (MODULE / "module.html").read_text(encoding="utf-8")
    script = (MODULE / "module.js").read_text(encoding="utf-8")

    if manifest["id"] != "provoware-genretool-pro":
        fail("Manifest-ID ist falsch")
    for entry in manifest["entry"].values():
        if entry and not (MODULE / entry).is_file():
            fail(f"Manifest-Einstieg fehlt: {entry}")

    registered = "../modules/provoware-genretool-pro/module.manifest.json"
    if registered not in app.get("defaultModuleManifests", []):
        fail("GenreTool ist nicht im App-Manifest registriert")

    data = database.get("data", {})
    if tuple(data) != EXPECTED_CATEGORIES:
        fail("Datenbankkategorien oder Reihenfolge stimmen nicht")

    all_terms: list[str] = []
    for category in EXPECTED_CATEGORIES:
        values = data.get(category)
        if not isinstance(values, list) or len(values) != 300:
            fail(f"Kategorie {category} enthält nicht exakt 300 Einträge")
        all_terms.extend(values)

    normalized = [" ".join(value.strip().split()).casefold() for value in all_terms]
    if len(all_terms) != EXPECTED_TOTAL:
        fail("Gesamtzahl ist nicht 1.800")
    if len(set(normalized)) != EXPECTED_TOTAL:
        fail("Datenbank enthält normalisierte Dubletten")
    if database.get("counts", {}).get("total") != EXPECTED_TOTAL:
        fail("counts.total stimmt nicht")

    required_ids = (
        "genretool-entry-form", "genretool-list", "genretool-results",
        "genretool-history", "genretool-import", "genretool-reset",
    )
    for element_id in required_ids:
        if f'id="{element_id}"' not in html:
            fail(f"Pflichtelement fehlt: {element_id}")

    for marker in ("genres_db.json", "loadSeedIfEmpty", "localStorage", "importText"):
        if marker not in script:
            fail(f"Modullogik enthält Pflichtmarker nicht: {marker}")

    print("OK: GenreTool-Manifest, Registrierung, Oberfläche und 1.800 eindeutige Startdaten geprüft.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"FEHLER: {exc}")
        sys.exit(1)
