#!/usr/bin/env python3
"""Prüft das lokale Release-Gate ohne eine Browser-Freigabe vorzutäuschen."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TODO = ROOT / "todo.txt"
RELEASE_STATUS = ROOT / "docs" / "RELEASE_STATUS_2026-07-16.md"
RELEASE_CHECKLIST = ROOT / "docs" / "RELEASE_CHECKLIST.md"
BROWSER_PROTOCOL = ROOT / "docs" / "BROWSER_RELEASE_PROTOCOL_2026-07-16.md"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release-gate.yml"

REQUIRED_STATUS_PHRASES = (
    "Release-Kandidat mit offener manueller Browserfreigabe",
    "Eine echte Chromium- und Firefox-Sichtprüfung ist in dieser Containerumgebung nicht belegbar",
    "Eine endgültige Freigabe darf erst markiert werden, wenn die Browserpunkte geprüft und dokumentiert sind",
)

REQUIRED_TODO_ITEMS = (
    "Echte Browser-Freigabe anhand von `docs/RELEASE_STATUS_2026-07-16.md` manuell prüfen",
    "Speicherprüfung zusätzlich in Chromium und Firefox ausführen",
)

REQUIRED_PROTOCOL_PHRASES = (
    "Dieses Protokoll ist die ausfüllbare Vorlage für die echte Freigabeprüfung",
    "In dieser Containerumgebung sind jedoch weder Chromium/Chrome noch Firefox noch `xdg-open` als startbarer Browser vorhanden",
    "| Chromium-Start | offen | Noch nicht geprüft. |",
    "| Firefox-Start | offen | Noch nicht geprüft. |",
    "| Speicherprüfung | offen | Noch nicht geprüft. |",
    "Die Freigabe bleibt offen, solange ein Prüfschritt den Status `offen` oder `fehlgeschlagen` hat.",
)

REQUIRED_CHECK_COMMANDS = (
    "python3 tests/validate_progress_consistency.py",
    "python3 tests/validate_module_manifests.py",
    "python3 tests/test_html_helpers.py",
    "python3 tests/validate_genres_module.py",
    "python3 tests/validate_module_previews.py",
    "python3 tests/validate_quicktext_snippets.py",
    "python3 tests/test_start_local.py",
    "python3 tests/scan_performance_hotspots.py",
    "python3 tests/validate_release_gate.py",
)

REQUIRED_COMPILE_COMMAND = (
    "python3 -m py_compile "
    "tests/validate_progress_consistency.py "
    "tests/validate_module_manifests.py "
    "tests/test_html_helpers.py "
    "tests/validate_genres_module.py "
    "tests/validate_module_previews.py "
    "tests/validate_quicktext_snippets.py "
    "tests/test_start_local.py "
    "tests/scan_performance_hotspots.py "
    "tests/validate_release_gate.py"
)

BROWSER_OPEN_PATTERN = re.compile(r"^- \[ \].*(Browser|Chromium|Firefox|Speicherprüfung)", re.MULTILINE)
README_PROGRESS_PATTERN = re.compile(r"Entwicklungsfortschritt: (\d+) %")
TODO_PROGRESS_PATTERN = re.compile(r"Fortschritt gesamt: (\d+) %")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"{path.relative_to(ROOT)} konnte nicht gelesen werden: {exc}") from exc


def require_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f"{label} enthält nicht den erwarteten Hinweis: {needle}")


def extract_progress(text: str, pattern: re.Pattern[str], label: str) -> int:
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"{label} enthält keine Fortschrittsangabe.")
    return int(match.group(1))


def require_matching_progress(readme_text: str, todo_text: str) -> None:
    readme_progress = extract_progress(readme_text, README_PROGRESS_PATTERN, "README.md")
    todo_progress = extract_progress(todo_text, TODO_PROGRESS_PATTERN, "todo.txt")
    if readme_progress != todo_progress:
        raise RuntimeError(
            "README.md und todo.txt nennen unterschiedliche Fortschrittswerte: "
            f"{readme_progress} % / {todo_progress} %."
        )


def require_file_reference(command: str) -> None:
    parts = command.split()
    if len(parts) < 2:
        return
    candidate = ROOT / parts[1]
    if not candidate.exists():
        raise RuntimeError(f"Release-Prüfbefehl verweist auf fehlende Datei: {parts[1]}")


def normalized_command(text: str) -> str:
    return " ".join(text.split())


def require_compile_command(text: str, label: str) -> None:
    if REQUIRED_COMPILE_COMMAND not in normalized_command(text):
        raise RuntimeError(f"{label} enthält nicht den vollständigen Syntaxprüfbefehl.")
    for file_name in REQUIRED_COMPILE_COMMAND.split()[3:]:
        if not (ROOT / file_name).is_file():
            raise RuntimeError(f"Syntaxprüfbefehl verweist auf fehlende Datei: {file_name}")


def main() -> int:
    try:
        readme_text = read_text(README)
        todo_text = read_text(TODO)
        status_text = read_text(RELEASE_STATUS)
        checklist_text = read_text(RELEASE_CHECKLIST)
        browser_protocol_text = read_text(BROWSER_PROTOCOL)
        workflow_text = read_text(RELEASE_WORKFLOW)

        for phrase in REQUIRED_STATUS_PHRASES:
            require_contains(status_text, phrase, "Release-Status")

        for item in REQUIRED_TODO_ITEMS:
            require_contains(todo_text, item, "todo.txt")

        for phrase in REQUIRED_PROTOCOL_PHRASES:
            require_contains(browser_protocol_text, phrase, "Browser-Freigabeprotokoll")

        require_contains(status_text, "docs/BROWSER_RELEASE_PROTOCOL_2026-07-16.md", "Release-Status")

        for command in REQUIRED_CHECK_COMMANDS:
            require_contains(status_text, command, "Release-Status")
            require_contains(workflow_text, command, "Release-Workflow")
            require_file_reference(command)

        require_compile_command(status_text, "Release-Status")
        require_compile_command(workflow_text, "Release-Workflow")
        require_matching_progress(readme_text, todo_text)
        require_contains(checklist_text, "Wenn einer dieser Punkte offen ist, wird keine Freigabe markiert", "Release-Checkliste")
        require_contains(status_text, ".github/workflows/release-gate.yml", "Release-Status")

        if not BROWSER_OPEN_PATTERN.search(todo_text):
            raise RuntimeError("todo.txt hält keine offene Browser- oder Speicherfreigabe mehr fest.")
    except RuntimeError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    print("OK: Release-Gate ist konsistent; Browser-Freigabe bleibt offen dokumentiert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
