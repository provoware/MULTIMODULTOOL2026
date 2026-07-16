#!/usr/bin/env python3
"""Gezielte Struktur-, Syntax- und Datenprüfung für das Provoware GenreTool Pro."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "provoware-genretool-pro"
LEGACY_ROOT_DATABASE = ROOT / "genres_db.json"
APP_MANIFEST = ROOT / "manifests" / "MULTIMODULTOOL2026_02_AppManifest.json"
EXPECTED_CATEGORIES = ("genres", "moods", "styles", "effects", "themes", "special")
EXPECTED_TOTAL = 1800


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    if LEGACY_ROOT_DATABASE.exists():
        fail("Veraltete Root-Kopie genres_db.json gefunden; Startdaten müssen nur im GenreTool-Modul liegen")

    manifest = json.loads((MODULE / "module.manifest.json").read_text(encoding="utf-8"))
    database = json.loads((MODULE / "genres_db.json").read_text(encoding="utf-8"))
    app = json.loads(APP_MANIFEST.read_text(encoding="utf-8"))
    html = (MODULE / "module.html").read_text(encoding="utf-8")
    script_path = MODULE / "module.js"
    script = script_path.read_text(encoding="utf-8")

    if manifest["id"] != "provoware-genretool-pro":
        fail("Manifest-ID ist falsch")
    if manifest.get("version") != "2.0.0":
        fail("Manifest-Version muss 2.0.0 sein")
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
        if not all(isinstance(value, str) and value.strip() for value in values):
            fail(f"Kategorie {category} enthält leere oder ungültige Werte")
        all_terms.extend(values)

    normalized = [" ".join(value.strip().split()).casefold() for value in all_terms]
    if len(all_terms) != EXPECTED_TOTAL:
        fail("Gesamtzahl ist nicht 1.800")
    if len(set(normalized)) != EXPECTED_TOTAL:
        fail("Datenbank enthält normalisierte Dubletten")
    counts = database.get("counts", {})
    if counts.get("total") != EXPECTED_TOTAL:
        fail("counts.total stimmt nicht")
    for category in EXPECTED_CATEGORIES:
        if counts.get(category) != 300:
            fail(f"counts.{category} stimmt nicht")

    required_roles = (
        "status", "entry-form", "entry-category", "entry-terms", "count",
        "search", "filter-category", "sort", "list", "page-info",
        "category-mixer", "result-count", "avoid-recent", "favorites-first",
        "auto-copy", "stats", "results", "import", "history", "edit-dialog",
        "edit-form", "edit-category", "edit-term",
    )
    for role in required_roles:
        if f'data-role="{role}"' not in html:
            fail(f"Pflichtrolle fehlt: {role}")

    required_actions = (
        "validate", "page-prev", "page-next", "generate", "copy-all",
        "undo", "redo", "export", "backup", "reset",
        "edit-cancel",
    )
    for action in required_actions:
        if f'data-action="{action}"' not in html:
            fail(f"Pflichtaktion fehlt: {action}")

    if script.strip() == "PLACEHOLDER":
        fail("module.js ist weiterhin ein Platzhalter")

    required_markers = (
        'const STORAGE_KEY = "multimodultool2026.provoware-genretool-pro.v2"',
        "loadSeedIfEmpty", "fetchSeed", "normalizeState", "validateDatabase",
        "parseImport", "addTermsFromRows", "renderArchive", "renderStats", "renderResults",
        "renderHistory", "statsByCategory", "snapshot", "restoreSnapshot", "navigator.clipboard",
    )
    for marker in required_markers:
        if marker not in script:
            fail(f"Modullogik enthält Pflichtmarker nicht: {marker}")

    syntax = subprocess.run(
        ["node", "--check", str(script_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        fail("JavaScript-Syntaxprüfung fehlgeschlagen: " + (syntax.stderr.strip() or syntax.stdout.strip()))

    print("OK: GenreTool 2.0 – Manifest, Registrierung, UI, JavaScript und 1.800 eindeutige Startdaten geprüft.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"FEHLER: {exc}")
        sys.exit(1)
