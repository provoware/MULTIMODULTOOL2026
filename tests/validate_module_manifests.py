#!/usr/bin/env python3
"""Prueft Modulmanifeste mit den wichtigsten Projektregeln."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "modules"
EXAMPLE_MANIFEST = ROOT / "manifests" / "MULTIMODULTOOL2026_03_ExampleModule.manifest.json"

REQUIRED_KEYS = {
    "id",
    "name",
    "version",
    "type",
    "description",
    "entry",
    "permissions",
    "storage",
    "validation",
}
ALLOWED_TYPES = {
    "overview",
    "calendar",
    "notes",
    "tasks",
    "projectboard",
    "stats",
    "quicktext",
    "editor",
    "code",
    "settings",
    "timer",
    "bookmarks",
    "activity",
    "modulebuilder",
    "custom",
}
ALLOWED_PERMISSIONS = {"local-storage", "file-export", "file-import", "timer", "none"}
ALLOWED_STORAGE_SCOPES = {"module", "workspace", "none"}
ENTRY_VALUES = {
    "html": {"module.html", None},
    "css": {"module.css", None},
    "js": {"module.js", None},
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
EXT_PATTERN = re.compile(r"^\.[a-z0-9]+$")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"ungueltiges JSON bei Zeile {exc.lineno}, Spalte {exc.colno}") from exc


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_manifest(path: Path) -> list[str]:
    data = load_json(path)
    errors: list[str] = []

    require(set(data) == REQUIRED_KEYS, errors, "Pflichtfelder stimmen nicht exakt")
    require(isinstance(data.get("id"), str) and ID_PATTERN.fullmatch(data["id"]), errors, "id ist keine kleine Bindestrich-ID")
    require(isinstance(data.get("name"), str) and 3 <= len(data["name"]) <= 42, errors, "name hat ungueltige Laenge")
    require(isinstance(data.get("version"), str) and VERSION_PATTERN.fullmatch(data["version"]), errors, "version folgt nicht x.y.z")
    require(data.get("type") in ALLOWED_TYPES, errors, "type ist nicht erlaubt")
    require(isinstance(data.get("description"), str) and 10 <= len(data["description"]) <= 240, errors, "description hat ungueltige Laenge")

    entry = data.get("entry")
    require(isinstance(entry, dict) and set(entry) == set(ENTRY_VALUES), errors, "entry muss html, css und js enthalten")
    if isinstance(entry, dict):
        for key, allowed in ENTRY_VALUES.items():
            require(entry.get(key) in allowed, errors, f"entry.{key} ist ungueltig")

    permissions = data.get("permissions")
    require(isinstance(permissions, list) and len(permissions) >= 1, errors, "permissions braucht mindestens einen Eintrag")
    if isinstance(permissions, list):
        require(len(permissions) == len(set(permissions)), errors, "permissions enthaelt Duplikate")
        require(all(item in ALLOWED_PERMISSIONS for item in permissions), errors, "permissions enthaelt unerlaubte Werte")

    storage = data.get("storage")
    require(isinstance(storage, dict) and set(storage) == {"scope", "backupRequired"}, errors, "storage ist unvollstaendig")
    if isinstance(storage, dict):
        require(storage.get("scope") in ALLOWED_STORAGE_SCOPES, errors, "storage.scope ist ungueltig")
        require(isinstance(storage.get("backupRequired"), bool), errors, "storage.backupRequired muss boolean sein")

    validation = data.get("validation")
    require(isinstance(validation, dict) and set(validation) == {"maxInputBytes", "allowedFileExtensions"}, errors, "validation ist unvollstaendig")
    if isinstance(validation, dict):
        max_bytes = validation.get("maxInputBytes")
        require(isinstance(max_bytes, int) and 0 <= max_bytes <= 8_000_000, errors, "validation.maxInputBytes ist ausserhalb des Limits")
        extensions = validation.get("allowedFileExtensions")
        require(isinstance(extensions, list), errors, "validation.allowedFileExtensions muss eine Liste sein")
        if isinstance(extensions, list):
            require(len(extensions) == len(set(extensions)), errors, "validation.allowedFileExtensions enthaelt Duplikate")
            require(all(isinstance(item, str) and EXT_PATTERN.fullmatch(item) for item in extensions), errors, "validation.allowedFileExtensions enthaelt ungueltige Werte")

    return errors


def manifest_paths() -> list[Path]:
    module_manifests = sorted(MODULE_ROOT.glob("*/module.manifest.json"))
    return [EXAMPLE_MANIFEST, *module_manifests]


def main() -> int:
    failures = []
    for path in manifest_paths():
        try:
            errors = validate_manifest(path)
        except ValueError as exc:
            errors = [str(exc)]
        if errors:
            failures.append((path, errors))

    if failures:
        for path, errors in failures:
            rel_path = path.relative_to(ROOT)
            print(f"FEHLER: {rel_path}")
            for error in errors:
                print(f"- {error}")
        return 1

    print(f"OK: {len(manifest_paths())} Modulmanifeste geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
