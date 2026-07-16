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

REQUIRED_CHECK_COMMANDS = (
    "python3 tests/validate_progress_consistency.py",
    "python3 tests/validate_module_manifests.py",
    "python3 tests/test_html_helpers.py",
    "python3 tests/validate_genres_module.py",
    "python3 tests/validate_module_previews.py",
    "python3 tests/scan_performance_hotspots.py",
    "python3 tests/validate_release_gate.py",
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


def main() -> int:
    try:
        readme_text = read_text(README)
        todo_text = read_text(TODO)
        status_text = read_text(RELEASE_STATUS)
        checklist_text = read_text(RELEASE_CHECKLIST)
        workflow_text = read_text(RELEASE_WORKFLOW)

        for phrase in REQUIRED_STATUS_PHRASES:
            require_contains(status_text, phrase, "Release-Status")

        for item in REQUIRED_TODO_ITEMS:
            require_contains(todo_text, item, "todo.txt")

        for command in REQUIRED_CHECK_COMMANDS:
            require_contains(status_text, command, "Release-Status")
            require_contains(workflow_text, command, "Release-Workflow")
            require_file_reference(command)

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
