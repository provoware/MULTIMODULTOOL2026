#!/usr/bin/env python3
"""Abhängigkeitsarmer Repository-Vertragsprüfer für MULTIMODULTOOL2026."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md", "AGENTS.md", "ANLEITUNG_TOOL.md", "CHANGELOG.md",
    "TODO.md", "SCHWACHSTELLEN.md", "UPGRADE_POOL.md", "ENTWICKLERDOKU.md",
    "layout-manifest.json", "src/main.py", "src/single_instance.py",
    "src/diagnostics_center.py", "src/error_events.py", "src/error_dialog.py",
    "tests/test_single_instance.py", "tests/test_diagnostics_center.py",
    "tests/test_gui_offscreen.py", "tests/test_settings_failpoints.py",
    "docs/XDG_PFADVERTRAG.md", "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md",
    ".github/workflows/repository-contract.yml",
)


def text(path: str, errors: list[str]) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: nicht als UTF-8 lesbar: {exc}")
        return ""


def check_required(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            errors.append(f"Pflichtdatei fehlt: {path}")


def check_python(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in {".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path.relative_to(ROOT)), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"Python-Prüfung fehlgeschlagen: {path.relative_to(ROOT)}: {exc}")


def check_manifest(errors: list[str]) -> None:
    try:
        manifest = json.loads(text("layout-manifest.json", errors))
    except json.JSONDecodeError as exc:
        errors.append(f"layout-manifest.json: ungültiges JSON: {exc}")
        return
    zones = manifest.get("zones", [])
    ids = [zone.get("id") for zone in zones if isinstance(zone, dict)]
    expected = [f"Z{index:02d}" for index in range(1, 10)]
    if ids != expected:
        errors.append(f"Layoutzonen sind inkonsistent: {ids!r}")
    single = manifest.get("singleInstancePolicy", {})
    if single.get("transport") != "unix-domain-socket":
        errors.append("Manifest: Unix-Domain-Socket-Vertrag fehlt.")
    if single.get("peerUidRequired") is not True:
        errors.append("Manifest: Peer-UID-Prüfung fehlt.")
    if single.get("allowedActions") != ["activate", "show-diagnostics"]:
        errors.append("Manifest: erlaubte Instanzaktionen sind inkonsistent.")
    diagnostics = manifest.get("diagnosticsPolicy", {})
    for key in ("readOnly", "copySanitizedSingleReport"):
        if diagnostics.get(key) is not True:
            errors.append(f"Manifest: Diagnosevertrag {key} fehlt.")
    for key in ("deleteAllowed", "uploadAllowed", "automaticExportAllowed"):
        if diagnostics.get(key) is not False:
            errors.append(f"Manifest: Diagnosevertrag muss {key}=false setzen.")
    for path in manifest.get("validation", {}).get("documentation", []):
        if not (ROOT / path).is_file():
            errors.append(f"Manifest-Dokument fehlt: {path}")


def checkbox_counts(todo: str) -> tuple[int, int]:
    done = len(re.findall(r"^- \[x\]", todo, flags=re.MULTILINE))
    open_count = len(re.findall(r"^- \[ \]", todo, flags=re.MULTILINE))
    return done, open_count


def check_progress(errors: list[str]) -> None:
    todo = text("TODO.md", errors)
    readme = text("README.md", errors)
    main_source = text("src/main.py", errors)
    done, open_count = checkbox_counts(todo)
    total = done + open_count
    percent = round(done / total * 100) if total else 0
    expected = {"done": 25, "open": 40, "total": 65, "percent": 38}
    actual = {"done": done, "open": open_count, "total": total, "percent": percent}
    if actual != expected:
        errors.append(f"TODO-Fortschritt inkonsistent: {actual!r}, erwartet {expected!r}")
    for marker in (
        f"Entwicklungsfortschritt: {percent} %",
        f"Erledigte Punkte: {done}",
        f"Offene Punkte: {open_count}",
        f"Gesamtpunkte: {total}",
    ):
        if marker not in readme:
            errors.append(f"README-Fortschritt fehlt: {marker}")
    for marker in (
        f"DEVELOPMENT_PROGRESS = {percent}",
        f"COMPLETED_POINTS = {done}",
        f"OPEN_POINTS = {open_count}",
    ):
        if marker not in main_source:
            errors.append(f"src/main.py-Fortschritt fehlt: {marker}")


def check_linux_and_instance_contract(errors: list[str]) -> None:
    main_source = text("src/main.py", errors)
    instance = text("src/single_instance.py", errors)
    diagnostics = text("src/diagnostics_center.py", errors)
    agents = text("AGENTS.md", errors)
    workflow = text(".github/workflows/repository-contract.yml", errors)
    for marker in (
        "SingleInstanceCoordinator", "resolve_runtime_root", "--show-diagnostics",
        "--diagnostic-id", "drain_messages", "requestActivate",
    ):
        if marker not in main_source:
            errors.append(f"Single-Instance-Integration fehlt in main.py: {marker}")
    for marker in (
        "socket.AF_UNIX", "socket.SO_PEERCRED", "XDG_RUNTIME_DIR",
        "activate", "show-diagnostics", "beschädigt",
    ):
        if marker not in instance:
            errors.append(f"Single-Instance-Vertrag fehlt: {marker}")
    for marker in (
        "O_RDONLY", "O_NOFOLLOW", "diagnosticsSeverityFilter",
        "diagnosticsIdFilter", "diagnosticsCopyButton",
    ):
        if marker not in diagnostics:
            errors.append(f"Diagnosevertrag fehlt: {marker}")
    for forbidden in (
        "diagnosticsDeleteButton", "diagnosticsUploadButton", "diagnosticsExportButton",
    ):
        if forbidden in diagnostics:
            errors.append(f"Verbotene Diagnoseaktion vorhanden: {forbidden}")
    for marker in ("Peer-UID", "Dateipfade", "Upload"):
        if marker.lower() not in agents.lower():
            errors.append(f"AGENTS-Vertrag fehlt: {marker}")
    for marker in (
        "tests.test_single_instance", "tests.test_diagnostics_center", "QT_QPA_PLATFORM",
    ):
        if marker not in workflow:
            errors.append(f"CI-Vertrag fehlt: {marker}")


def main() -> int:
    errors: list[str] = []
    for check in (
        check_required,
        check_python,
        check_manifest,
        check_progress,
        check_linux_and_instance_contract,
    ):
        check(errors)
    if errors:
        print("ROT: Repository-Vertrag ist nicht erfüllt.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("GRÜN: Repository-, Linux-, Single-Instance- und Diagnosevertrag sind konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
