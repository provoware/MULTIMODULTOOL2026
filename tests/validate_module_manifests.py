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
APP_MANIFEST = ROOT / "manifests" / "MULTIMODULTOOL2026_02_AppManifest.json"

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
    "mother",
    "registry",
    "debugging",
    "custom",
}
ALLOWED_PERMISSIONS = {"local-storage", "file-export", "file-import", "timer", "none"}
ALLOWED_STORAGE_SCOPES = {"module", "workspace", "none"}
ENTRY_VALUES = {
    "html": {"module.html", None},
    "css": {"module.css", None},
    "js": {"module.js", None},
}
ENTRY_FILENAMES = {"module.html", "module.css", "module.js"}
INTERNAL_JS_ENTRY = "module.js"
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


def validate_entry_file(key: str, entry_file: object, module_dir: Path | None, errors: list[str]) -> None:
    require(entry_file in ENTRY_VALUES[key], errors, f"entry.{key} ist ungueltig")
    if not isinstance(entry_file, str):
        return
    require(entry_file in ENTRY_FILENAMES and "/" not in entry_file and "\\" not in entry_file, errors, f"entry.{key} darf nur eine erlaubte Moduldatei sein")
    if key == "js":
        require(entry_file == INTERNAL_JS_ENTRY, errors, "entry.js darf nur auf interne module.js zeigen")
    if module_dir is not None:
        require((module_dir / entry_file).is_file(), errors, f"entry.{key} verweist auf fehlende Datei")


def validate_manifest(path: Path, module_dir: Path | None = None) -> list[str]:
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
        for key in ENTRY_VALUES:
            validate_entry_file(key, entry.get(key), module_dir, errors)

    if module_dir is not None:
        require(data.get("id") == module_dir.name, errors, "id passt nicht zum Modulordner")

    permissions = data.get("permissions")
    require(isinstance(permissions, list) and len(permissions) >= 1, errors, "permissions braucht mindestens einen Eintrag")
    if isinstance(permissions, list):
        require(len(permissions) == len(set(permissions)), errors, "permissions enthaelt Duplikate")
        require(all(item in ALLOWED_PERMISSIONS for item in permissions), errors, "permissions enthaelt unerlaubte Werte")

    storage = data.get("storage")
    require(isinstance(storage, dict) and set(storage) == {"scope", "backupRequired"}, errors, "storage ist unvollstaendig")
    if isinstance(storage, dict):
        scope = storage.get("scope")
        require(scope in ALLOWED_STORAGE_SCOPES, errors, "storage.scope ist ungueltig")
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


def manifest_paths() -> list[tuple[Path, Path | None]]:
    module_manifests = [(path, path.parent) for path in sorted(MODULE_ROOT.glob("*/module.manifest.json"))]
    return [(EXAMPLE_MANIFEST, None), *module_manifests]


def validate_registered_modules() -> list[str]:
    data = load_json(APP_MANIFEST)
    registered = data.get("registeredModules")
    default_paths = data.get("defaultModuleManifests")
    errors: list[str] = []

    require(isinstance(default_paths, list), errors, "defaultModuleManifests muss eine Liste sein")
    require(isinstance(registered, list) and registered, errors, "registeredModules braucht mindestens ein Modul")
    if not isinstance(default_paths, list) or not isinstance(registered, list):
        return errors

    registry_by_manifest: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for item in registered:
        if not isinstance(item, dict):
            errors.append("registeredModules enthaelt einen ungueltigen Eintrag")
            continue
        module_id = item.get("id")
        version = item.get("version")
        manifest = item.get("manifest")
        require(isinstance(module_id, str) and ID_PATTERN.fullmatch(module_id), errors, "registeredModules.id ist keine kleine Bindestrich-ID")
        require(isinstance(version, str) and VERSION_PATTERN.fullmatch(version), errors, "registeredModules.version folgt nicht x.y.z")
        require(isinstance(manifest, str) and manifest.endswith("/module.manifest.json"), errors, "registeredModules.manifest verweist nicht auf ein Modulmanifest")
        if isinstance(module_id, str):
            require(module_id not in seen_ids, errors, f"registeredModules enthaelt die id doppelt: {module_id}")
            seen_ids.add(module_id)
        if isinstance(manifest, str):
            require(manifest not in registry_by_manifest, errors, f"registeredModules enthaelt den Manifestpfad doppelt: {manifest}")
            registry_by_manifest[manifest] = item

    require(set(default_paths) == set(registry_by_manifest), errors, "registeredModules muss dieselben Modulpfade wie defaultModuleManifests enthalten")
    for manifest in default_paths:
        item = registry_by_manifest.get(manifest)
        manifest_path = (APP_MANIFEST.parent / manifest).resolve()
        if item is None or not manifest_path.is_file():
            continue
        module_data = load_json(manifest_path)
        require(item.get("id") == module_data.get("id"), errors, f"registeredModules.id passt nicht zu {manifest}")
        require(item.get("version") == module_data.get("version"), errors, f"registeredModules.version passt nicht zu {manifest}")

    return errors


def main() -> int:
    failures = []
    for path, module_dir in manifest_paths():
        try:
            errors = validate_manifest(path, module_dir)
        except ValueError as exc:
            errors = [str(exc)]
        if errors:
            failures.append((path, errors))

    try:
        registry_errors = validate_registered_modules()
    except ValueError as exc:
        registry_errors = [str(exc)]
    if registry_errors:
        failures.append((APP_MANIFEST, registry_errors))

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
