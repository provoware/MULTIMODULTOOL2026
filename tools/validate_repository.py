#!/usr/bin/env python3
"""Repository-Vertrag für MULTIMODULTOOL2026 prüfen."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.manifest_validator import validate_manifest  # noqa: E402

REQUIRED_FILES = (
    ".github/workflows/repository-contract.yml",
    "AGENTS.md",
    "ANLEITUNG_TOOL.md",
    "CHANGELOG.md",
    "ENTWICKLERDOKU.md",
    "README.md",
    "SCHWACHSTELLEN.md",
    "TODO.md",
    "UPGRADE_POOL.md",
    "assets/ui-reference/multimodultool2026-ui-layout-reference-2026.webp",
    "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/GITHUB_ZUGRIFF.md",
    "docs/UI_BASISVORLAGE.md",
    "docs/XDG_PFADVERTRAG.md",
    "layout-manifest.json",
    "requirements.txt",
    "setup.sh",
    "start.sh",
    "src/__init__.py",
    "src/error_dialog.py",
    "src/error_events.py",
    "src/main.py",
    "src/manifest_validator.py",
    "src/settings_manager.py",
    "src/theme.qss",
    "src/xdg_paths.py",
    "standards/UI_LAYOUT_STANDARD_2026.md",
    "standards/settings-schema-v1.json",
    "tests/__init__.py",
    "tests/test_error_events.py",
    "tests/test_gui_offscreen.py",
    "tests/test_repository_contract.py",
    "tests/test_settings_failpoints.py",
    "tests/test_settings_manager.py",
    "tests/test_setup_assistant.py",
    "tests/test_xdg_paths.py",
    "tools/setup_assistant.py",
    "tools/validate_repository.py",
)

MAINTAINED_DOCS = (
    "CHANGELOG.md",
    "ANLEITUNG_TOOL.md",
    "TODO.md",
    "SCHWACHSTELLEN.md",
    "UPGRADE_POOL.md",
    "ENTWICKLERDOKU.md",
    "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/GITHUB_ZUGRIFF.md",
    "docs/XDG_PFADVERTRAG.md",
)

PYTHON_FILES = (
    "src/error_dialog.py",
    "src/error_events.py",
    "src/main.py",
    "src/manifest_validator.py",
    "src/settings_manager.py",
    "src/xdg_paths.py",
    "tests/test_error_events.py",
    "tests/test_gui_offscreen.py",
    "tests/test_repository_contract.py",
    "tests/test_settings_failpoints.py",
    "tests/test_settings_manager.py",
    "tests/test_setup_assistant.py",
    "tests/test_xdg_paths.py",
    "tools/setup_assistant.py",
    "tools/validate_repository.py",
)


def read_text(relative_path: str, errors: list[str]) -> str:
    try:
        return (ROOT / relative_path).read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{relative_path} kann nicht gelesen werden: {exc}")
        return ""


def check_required_files(errors: list[str]) -> None:
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            errors.append(f"Pflichtdatei fehlt: {relative_path}")


def check_manifest(errors: list[str]) -> None:
    result = validate_manifest(ROOT / "layout-manifest.json", ROOT)
    errors.extend(result.errors)
    if result.data is not None:
        policy = result.data.get("errorEventPolicy", {})
        for key, expected in {
            "requiredDialogFields": [
                "cause",
                "consequence",
                "dataState",
                "solution",
                "diagnosticId",
                "safeNextStep",
            ],
            "eventJournalMode": "0600",
            "privateDataMustBeRedacted": True,
            "unhandledExceptionsMustBeCaptured": True,
        }.items():
            if policy.get(key) != expected:
                errors.append(f"layout-manifest errorEventPolicy.{key} ist nicht verbindlich gesetzt.")


def parse_todo_counts(todo_text: str) -> tuple[int, int]:
    completed = len(re.findall(r"(?m)^\s*-\s*\[x\]\s+", todo_text, re.IGNORECASE))
    open_items = len(re.findall(r"(?m)^\s*-\s*\[\s\]\s+", todo_text))
    return completed, open_items


def check_progress_consistency(errors: list[str]) -> None:
    readme = read_text("README.md", errors)
    todo = read_text("TODO.md", errors)
    completed, open_items = parse_todo_counts(todo)
    total = completed + open_items
    expected = {
        "percent": round((completed / total) * 100) if total else 0,
        "completed": completed,
        "open": open_items,
        "total": total,
    }
    patterns = {
        "percent": r"Entwicklungsfortschritt:\s*(\d+)\s*%",
        "completed": r"Erledigte Punkte:\s*(\d+)",
        "open": r"Offene Punkte:\s*(\d+)",
        "total": r"Gesamtpunkte:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, readme)
        if not match:
            errors.append(f"README-Fortschrittswert fehlt: {key}")
        elif int(match.group(1)) != expected[key]:
            errors.append(
                f"README-{key} ist {match.group(1)}, aus TODO.md ergeben sich {expected[key]}."
            )
    for marker in ("**P0-004**", "**D-019**"):
        if not re.search(rf"- \[x\].*{re.escape(marker)}", todo):
            errors.append(f"TODO.md markiert {marker} nicht als erledigt.")


def check_agents_policy(errors: list[str]) -> None:
    agents = read_text("AGENTS.md", errors)
    for document in MAINTAINED_DOCS:
        if document not in agents:
            errors.append(f"AGENTS.md nennt die Pflegepflicht für {document} nicht.")
    for phrase in (
        "Entwicklungsfortschritt",
        "Erledigte Punkte",
        "Offene Punkte",
        "GitHub-Zugriffsvertrag",
        "Verbindlicher XDG-Pfadvertrag",
        "Verbindlicher Einstellungsvertrag",
        "Verbindlicher Fehler- und Ereignisvertrag",
    ):
        if phrase not in agents:
            errors.append(f"AGENTS.md enthält Pflichtaussage nicht: {phrase!r}")


def check_linux_scope(errors: list[str]) -> None:
    readme = read_text("README.md", errors)
    agents = read_text("AGENTS.md", errors)
    main_source = read_text("src/main.py", errors)
    start_source = read_text("start.sh", errors)
    for phrase in (
        "ausschließlich für Linux-Desktop-Systeme",
        "Kubuntu 22.04 LTS",
        "Kubuntu 24.04 LTS",
        "Windows, macOS, Android und iOS",
    ):
        if phrase not in readme:
            errors.append(f"README-Linuxvertrag fehlt: {phrase!r}")
    if "Verbindlicher Plattformvertrag" not in agents:
        errors.append("AGENTS.md enthält keinen verbindlichen Linux-Plattformvertrag.")
    if "is_supported_platform" not in main_source:
        errors.append("src/main.py enthält keinen Linux-Plattformblocker.")
    if "uname -s" not in start_source:
        errors.append("start.sh prüft das Linux-Betriebssystem nicht.")


def check_todo_quality(errors: list[str]) -> None:
    todo = read_text("TODO.md", errors)
    for heading in ("## P0", "## P1", "## P2", "## P3", "## P4"):
        if heading not in todo:
            errors.append(f"TODO-Prioritätsbereich fehlt: {heading}")
    ids = re.findall(r"\*\*([A-Z]\d?-\d{3})\*\*", todo)
    if len(ids) != len(set(ids)):
        errors.append("TODO-IDs sind nicht eindeutig.")
    for marker in ("Abnahmekriterium:", "Abhängigkeit:", "Risiko:"):
        if marker not in todo:
            errors.append(f"TODO-Qualitätsmerkmal fehlt: {marker}")
    if "ausschließlich an Linux-Desktop-Systeme" not in todo:
        errors.append("TODO.md ist nicht verbindlich auf Linux begrenzt.")


def check_setup_contract(errors: list[str]) -> None:
    setup_source = read_text("tools/setup_assistant.py", errors)
    setup_shell = read_text("setup.sh", errors)
    start_source = read_text("start.sh", errors)
    for phrase in ("--check-only", ".venv.setup-", "PySide6"):
        if phrase not in setup_source:
            errors.append(f"Einrichtungsassistent enthält Pflichtmerkmal nicht: {phrase}")
    if "kde" not in setup_source.lower():
        errors.append("Einrichtungsassistent enthält keine KDE-Sitzungsprüfung.")
    if "shell=True" in setup_source:
        errors.append("Einrichtungsassistent verwendet unsichere Shell-Ausführung.")
    if "setup.sh" not in start_source:
        errors.append("start.sh ruft den Einrichtungsassistenten nicht auf.")
    if "set -Eeuo pipefail" not in setup_shell:
        errors.append("setup.sh verwendet keinen strikten Shell-Modus.")


def check_xdg_contract(errors: list[str]) -> None:
    source = read_text("src/xdg_paths.py", errors)
    main_source = read_text("src/main.py", errors)
    contract = read_text("docs/XDG_PFADVERTRAG.md", errors)
    for phrase in (
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_STATE_HOME",
        "DIRECTORY_MODE = 0o700",
        "ensure_xdg_paths",
        "_write_probe",
    ):
        if phrase not in source:
            errors.append(f"XDG-Pfadschicht enthält Pflichtmerkmal nicht: {phrase}")
    for phrase in ("ensure_xdg_paths", "validate_xdg_paths", "--paths-only"):
        if phrase not in main_source:
            errors.append(f"src/main.py bindet XDG-Pflichtmerkmal nicht ein: {phrase}")
    for phrase in ("Programmverzeichnis", "Symlink", "0700", "--validate-only", "Nachvalidierung"):
        if phrase not in contract:
            errors.append(f"XDG-Pfadvertrag fehlt Pflichtaussage: {phrase!r}")


def check_settings_contract(errors: list[str]) -> None:
    source = read_text("src/settings_manager.py", errors)
    main_source = read_text("src/main.py", errors)
    contract = read_text("docs/EINSTELLUNGSVERTRAG.md", errors)
    schema = read_text("standards/settings-schema-v1.json", errors)
    for phrase in (
        "SCHEMA_VERSION = 1",
        "FILE_MODE = 0o600",
        "settings.last-valid.json",
        "os.replace",
        "os.fsync",
        "load_or_recover_settings",
        "inspect_settings",
    ):
        if phrase not in source:
            errors.append(f"Einstellungsschicht enthält Pflichtmerkmal nicht: {phrase}")
    for phrase in ("load_or_recover_settings", "inspect_settings", "--settings-only"):
        if phrase not in main_source:
            errors.append(f"src/main.py bindet Einstellungsmerkmal nicht ein: {phrase}")
    for phrase in ("0600", "fsync", "os.replace", "Rollback", "--settings-only"):
        if phrase not in contract:
            errors.append(f"Einstellungsvertrag fehlt Pflichtaussage: {phrase!r}")
    try:
        parsed = json.loads(schema)
    except json.JSONDecodeError as exc:
        errors.append(f"settings-schema-v1.json ist ungültig: {exc}")
    else:
        if parsed.get("properties", {}).get("schemaVersion", {}).get("const") != 1:
            errors.append("settings-schema-v1.json erzwingt schemaVersion 1 nicht.")


def check_error_event_contract(errors: list[str]) -> None:
    source = read_text("src/error_events.py", errors)
    dialog = read_text("src/error_dialog.py", errors)
    main_source = read_text("src/main.py", errors)
    contract = read_text("docs/FEHLER_UND_EREIGNISVERTRAG.md", errors)
    for phrase in (
        "class ErrorEvent",
        "class EventJournal",
        "class ErrorEventCenter",
        "class SafeOperationError",
        "EVENT_FILE_MODE = 0o600",
        "install_exception_hooks",
        "diagnostic_id",
        "cause",
        "consequence",
        "data_state",
        "solution",
        "next_step",
    ):
        if phrase not in source:
            errors.append(f"Fehler-/Ereignisschicht enthält Pflichtmerkmal nicht: {phrase}")
    for object_name in (
        "errorCause",
        "errorConsequence",
        "errorDataState",
        "errorSolution",
        "errorDiagnosticId",
        "errorNextStep",
    ):
        if object_name not in dialog:
            errors.append(f"Globaler Fehlerdialog enthält Pflichtfeld nicht: {object_name}")
    for phrase in (
        "SafeApplication",
        "cli_entrypoint",
        "event_from_settings_result",
        "qt-event-exception",
        "EventJournal",
    ):
        if phrase not in main_source:
            errors.append(f"src/main.py integriert die Fehlerarchitektur nicht vollständig: {phrase}")
    for phrase in (
        "Ursache",
        "Folge",
        "Datenstand",
        "Lösung",
        "Diagnosekennung",
        "Sicherer nächster Schritt",
        "events.jsonl",
        "0600",
        "threading.excepthook",
    ):
        if phrase not in contract:
            errors.append(f"Fehler-/Ereignisvertrag fehlt Pflichtaussage: {phrase!r}")


def check_failpoint_contract(errors: list[str]) -> None:
    source = read_text("src/settings_manager.py", errors)
    tests = read_text("tests/test_settings_failpoints.py", errors)
    expected = (
        "before_temp_write",
        "after_temp_write",
        "before_fsync",
        "after_fsync",
        "before_backup",
        "after_backup",
        "before_replace",
        "after_replace",
        "before_postvalidate",
        "after_postvalidate",
    )
    if "FAILPOINT_NAMES" not in source or "FailpointController" not in source:
        errors.append("Einstellungsschicht besitzt keine deklarierte Failpoint-Schnittstelle.")
    for name in expected:
        if name not in source:
            errors.append(f"Einstellungsschicht enthält Failpoint nicht: {name}")
        if name not in tests:
            errors.append(f"Failpoint-Testmatrix prüft Punkt nicht: {name}")
    for phrase in (
        "old_data",
        "new_data",
        "validate_settings",
        "glob(\"*.tmp\")",
    ):
        if phrase not in tests:
            errors.append(f"Failpoint-Testmatrix enthält Nachweismerkmal nicht: {phrase}")


def check_gui_contract(errors: list[str]) -> None:
    workflow = read_text(".github/workflows/repository-contract.yml", errors)
    test_source = read_text("tests/test_gui_offscreen.py", errors)
    for phrase in ("QT_QPA_PLATFORM: offscreen", "PySide6", "tests.test_gui_offscreen"):
        if phrase not in workflow:
            errors.append(f"GitHub-Workflow enthält GUI-Pflichtmerkmal nicht: {phrase}")
    for phrase in (
        "ZONE_OBJECT_NAMES",
        "workspaceScroll",
        "contextScroll",
        "lockedPrimaryAction",
        "globalErrorDialog",
        "errorDiagnosticId",
    ):
        if phrase not in test_source and phrase not in read_text("src/error_dialog.py", errors):
            errors.append(f"Offscreen-GUI-Vertrag enthält Pflichtmerkmal nicht: {phrase}")


def check_github_access_contract(errors: list[str]) -> None:
    access_doc = read_text("docs/GITHUB_ZUGRIFF.md", errors)
    for phrase in ("nicht im Repository gespeichert", "GitHub-App", "Admin-Rechte"):
        if phrase not in access_doc:
            errors.append(f"GitHub-Zugriffsdokument fehlt Pflichtaussage: {phrase!r}")
    if re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", access_doc):
        errors.append("GitHub-Zugriffsdokument enthält ein mögliches Token.")


def check_python_syntax(errors: list[str]) -> None:
    for relative_path in PYTHON_FILES:
        source = read_text(relative_path, errors)
        if source:
            try:
                compile(source, relative_path, "exec")
            except SyntaxError as exc:
                errors.append(f"Syntaxfehler in {relative_path}:{exc.lineno}: {exc.msg}")


def check_json(errors: list[str]) -> None:
    for relative_path in ("layout-manifest.json", "standards/settings-schema-v1.json"):
        try:
            json.loads(read_text(relative_path, errors))
        except json.JSONDecodeError as exc:
            errors.append(f"{relative_path} ist ungültig: {exc}")


def check_start_script(errors: list[str]) -> None:
    content = read_text("start.sh", errors)
    if "set -Eeuo pipefail" not in content:
        errors.append("start.sh verwendet keinen strikten Shell-Modus.")
    if "--validate-only" not in content:
        errors.append("start.sh validiert den Startvertrag nicht vor dem GUI-Start.")


def main() -> int:
    errors: list[str] = []
    checks: Iterable[tuple[str, Callable[[list[str]], None]]] = (
        ("Pflichtdateien", check_required_files),
        ("Linux-Plattformvertrag", check_linux_scope),
        ("Manifest", check_manifest),
        ("Fortschritt", check_progress_consistency),
        ("Dokumentationspflicht", check_agents_policy),
        ("TODO-Qualität", check_todo_quality),
        ("Einrichtungsassistent", check_setup_contract),
        ("XDG-Pfadvertrag", check_xdg_contract),
        ("Einstellungsvertrag", check_settings_contract),
        ("Fehler- und Ereignisvertrag", check_error_event_contract),
        ("Failpoint-Matrix", check_failpoint_contract),
        ("Offscreen-GUI-Vertrag", check_gui_contract),
        ("GitHub-Zugriffsvertrag", check_github_access_contract),
        ("Python-Syntax", check_python_syntax),
        ("JSON", check_json),
        ("Startroutine", check_start_script),
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
