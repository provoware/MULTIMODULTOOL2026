#!/usr/bin/env python3
"""Verbindlichen Linux-, XDG-, Einstellungs- und GUI-Vertrag prüfen."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.manifest_validator import validate_manifest  # noqa: E402
from src.settings_manager import default_settings, validate_settings  # noqa: E402

REQUIRED_FILES = (
    ".github/workflows/repository-contract.yml",
    "AGENTS.md", "ANLEITUNG_TOOL.md", "CHANGELOG.md", "ENTWICKLERDOKU.md",
    "README.md", "SCHWACHSTELLEN.md", "TODO.md", "UPGRADE_POOL.md",
    "assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp",
    "docs/EINSTELLUNGSVERTRAG.md", "docs/GITHUB_ZUGRIFF.md",
    "docs/UI_BASISVORLAGE.md", "docs/XDG_PFADVERTRAG.md",
    "layout-manifest.json", "requirements.txt", "setup.sh", "start.sh",
    "src/__init__.py", "src/main.py", "src/manifest_validator.py",
    "src/settings_manager.py", "src/theme.qss", "src/xdg_paths.py",
    "standards/UI_LAYOUT_STANDARD_2026.md", "standards/settings-schema-v1.json",
    "tests/__init__.py", "tests/test_gui_offscreen.py",
    "tests/test_repository_contract.py", "tests/test_settings_manager.py",
    "tests/test_setup_assistant.py", "tests/test_xdg_paths.py",
    "tools/setup_assistant.py", "tools/validate_repository.py",
)
PYTHON_FILES = tuple(path for path in REQUIRED_FILES if path.endswith(".py"))
MAINTAINED_DOCS = (
    "CHANGELOG.md", "ANLEITUNG_TOOL.md", "TODO.md", "SCHWACHSTELLEN.md",
    "UPGRADE_POOL.md", "ENTWICKLERDOKU.md", "docs/GITHUB_ZUGRIFF.md",
    "docs/XDG_PFADVERTRAG.md", "docs/EINSTELLUNGSVERTRAG.md",
)


def text(path: str, errors: list[str]) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{path} nicht lesbar: {exc}")
        return ""


def require_phrases(source: str, phrases: tuple[str, ...], label: str, errors: list[str]) -> None:
    for phrase in phrases:
        if phrase not in source:
            errors.append(f"{label} fehlt: {phrase!r}")


def check_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            errors.append(f"Pflichtdatei fehlt: {path}")


def check_manifest(errors: list[str]) -> None:
    errors.extend(validate_manifest(ROOT / "layout-manifest.json", ROOT).errors)


def check_progress(errors: list[str]) -> None:
    todo, readme = text("TODO.md", errors), text("README.md", errors)
    done = len(re.findall(r"(?m)^\s*-\s*\[x\]\s+", todo, re.I))
    open_count = len(re.findall(r"(?m)^\s*-\s*\[\s\]\s+", todo))
    total = done + open_count
    expected = {
        "Entwicklungsfortschritt": round(done / total * 100) if total else 0,
        "Erledigte Punkte": done,
        "Offene Punkte": open_count,
        "Gesamtpunkte": total,
    }
    for label, value in expected.items():
        match = re.search(rf"{re.escape(label)}:\s*(\d+)", readme)
        if not match or int(match.group(1)) != value:
            errors.append(f"README-{label} muss {value} sein.")


def check_docs(errors: list[str]) -> None:
    agents = text("AGENTS.md", errors)
    for path in MAINTAINED_DOCS:
        if path not in agents:
            errors.append(f"AGENTS.md nennt Pflegepflicht nicht: {path}")
    require_phrases(
        agents,
        ("Verbindlicher Plattformvertrag", "Verbindlicher XDG-Pfadvertrag",
         "Verbindlicher Einstellungsvertrag", "GitHub-Zugriffsvertrag",
         "Entwicklungsfortschritt", "Erledigte Punkte", "Offene Punkte"),
        "AGENTS.md", errors,
    )


def check_todo(errors: list[str]) -> None:
    todo = text("TODO.md", errors)
    require_phrases(todo, ("## P0", "## P1", "## P2", "## P3", "## P4",
                           "Abnahmekriterium:", "Abhängigkeit:", "Risiko:",
                           "- [x] **P0-003**", "Offscreen-GUI-Smoke-Test"),
                    "TODO.md", errors)
    ids = re.findall(r"\*\*([A-Z]\d?-\d{3})\*\*", todo)
    if len(ids) != len(set(ids)):
        errors.append("TODO-IDs sind nicht eindeutig.")


def check_platform_setup_xdg(errors: list[str]) -> None:
    readme = text("README.md", errors)
    main = text("src/main.py", errors)
    setup = text("tools/setup_assistant.py", errors)
    xdg = text("src/xdg_paths.py", errors)
    start = text("start.sh", errors)
    require_phrases(readme, ("ausschließlich für Linux-Desktop-Systeme", "Kubuntu 22.04 LTS", "Kubuntu 24.04 LTS"), "README", errors)
    require_phrases(main, ("is_supported_platform", "ensure_xdg_paths", "validate_xdg_paths", "--paths-only"), "src/main.py", errors)
    require_phrases(setup, ("--check-only", ".venv.setup-", "PySide6"), "Setup", errors)
    if "kde" not in setup.lower():
        errors.append("Setup enthält keine KDE-Prüfung.")
    if "shell=True" in setup:
        errors.append("Setup verwendet shell=True.")
    require_phrases(xdg, ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME", "DIRECTORY_MODE = 0o700", "_write_probe"), "XDG", errors)
    require_phrases(start, ("set -Eeuo pipefail", "--validate-only", "uname -s"), "start.sh", errors)


def check_settings(errors: list[str]) -> None:
    source = text("src/settings_manager.py", errors)
    main = text("src/main.py", errors)
    contract = text("docs/EINSTELLUNGSVERTRAG.md", errors)
    schema_text = text("standards/settings-schema-v1.json", errors)
    require_phrases(source, ("SCHEMA_VERSION = 1", "settings.last-valid.json", "validate_settings",
                             "inspect_settings", "load_or_recover_settings", "os.replace",
                             "os.fsync", "FILE_MODE = 0o600", "corrupt-"), "Einstellungsmodul", errors)
    require_phrases(main, ("inspect_settings", "load_or_recover_settings", "--settings-only", "format_settings_report"), "src/main.py", errors)
    require_phrases(contract, ("Vorvalidierung", "atomar", "0600", "letzte gültige Sicherung", "Rollback", "beschädigt", "--validate-only"), "Einstellungsvertrag", errors)
    try:
        schema = json.loads(schema_text)
    except json.JSONDecodeError as exc:
        errors.append(f"settings-schema-v1.json ungültig: {exc}")
    else:
        if schema.get("additionalProperties") is not False:
            errors.append("Schema muss unbekannte Wurzelfelder verbieten.")
        if schema.get("properties", {}).get("schemaVersion", {}).get("const") != 1:
            errors.append("Schema muss Version 1 erzwingen.")
    try:
        manifest = json.loads(text("layout-manifest.json", errors))
    except json.JSONDecodeError:
        manifest = {}
    expected = {
        "schemaVersion": 1,
        "schemaPath": "standards/settings-schema-v1.json",
        "activeFile": "settings.json",
        "lastValidBackupFile": "settings.last-valid.json",
        "fileMode": "0600",
        "transactionalWriteRequired": True,
        "automaticRollbackRequired": True,
        "readOnlyValidationMustNotWrite": True,
    }
    for key, value in expected.items():
        if manifest.get("settingsPolicy", {}).get(key) != value:
            errors.append(f"settingsPolicy.{key} muss {value!r} sein.")
    defaults = validate_settings(default_settings())
    errors.extend(f"Standardeinstellung ungültig: {item}" for item in defaults.errors)


def check_gui(errors: list[str]) -> None:
    workflow = text(".github/workflows/repository-contract.yml", errors)
    main = text("src/main.py", errors)
    smoke = text("tests/test_gui_offscreen.py", errors)
    require_phrases(workflow, ("pip install -r requirements.txt", "QT_QPA_PLATFORM: offscreen", "test_gui_offscreen"), "CI", errors)
    require_phrases(main, ("ZONE_OBJECT_NAMES", "summaryCards", "primaryActionTiles", "workspaceScroll", "contextScroll", "lockedPrimaryAction"), "GUI", errors)
    require_phrases(smoke, ("QT_QPA_PLATFORM", "all_nine_layout_zones", "workspace_and_context_remain_scrollable", "unreleased_actions_are_disabled", "does_not_touch_user_data_paths"), "GUI-Smoke", errors)


def check_github(errors: list[str]) -> None:
    access = text("docs/GITHUB_ZUGRIFF.md", errors)
    require_phrases(access, ("nicht im Repository gespeichert", "GitHub-App", "Admin-Rechte"), "GitHub-Zugriff", errors)
    if re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", access):
        errors.append("Mögliches GitHub-Token gefunden.")


def check_formats(errors: list[str]) -> None:
    for path in PYTHON_FILES:
        source = text(path, errors)
        if source:
            try:
                compile(source, path, "exec")
            except SyntaxError as exc:
                errors.append(f"Syntaxfehler in {path}:{exc.lineno}: {exc.msg}")
    for path in ("layout-manifest.json", "standards/settings-schema-v1.json"):
        try:
            json.loads(text(path, errors))
        except json.JSONDecodeError as exc:
            errors.append(f"{path} ungültig: {exc}")


def main() -> int:
    errors: list[str] = []
    checks: tuple[tuple[str, Callable[[list[str]], None]], ...] = (
        ("Pflichtdateien", check_files), ("Manifest", check_manifest),
        ("Fortschritt", check_progress), ("Dokumentation", check_docs),
        ("TODO", check_todo), ("Linux/Setup/XDG", check_platform_setup_xdg),
        ("Einstellungen", check_settings), ("Offscreen-GUI", check_gui),
        ("GitHub-Zugriff", check_github), ("Syntax/JSON", check_formats),
    )
    for name, check in checks:
        before = len(errors)
        check(errors)
        print(f"{'GRÜN' if len(errors) == before else 'ROT'}: {name}")
    if errors:
        print("\nRepository-Vertrag verletzt:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nGRÜN: Linux-Repository-Vertrag vollständig erfüllt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
