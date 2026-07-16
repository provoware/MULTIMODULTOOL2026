#!/usr/bin/env python3
"""Prüft, ob README.md und todo.txt denselben Entwicklungsfortschritt nennen."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TODO = ROOT / "todo.txt"

README_PATTERN = re.compile(r"Entwicklungsfortschritt:\s*(\d{1,3})\s*%")
TODO_PATTERN = re.compile(r"Fortschritt gesamt:\s*(\d{1,3})\s*%")


def read_progress(path: Path, pattern: re.Pattern[str], label: str) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"{label} konnte nicht gelesen werden: {exc}") from exc

    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"{label} enthält keine erkennbare Fortschrittsangabe.")

    value = int(match.group(1))
    if not 0 <= value <= 100:
        raise RuntimeError(f"{label} enthält einen ungültigen Prozentwert: {value} %.")

    return value


def main() -> int:
    try:
        readme_progress = read_progress(README, README_PATTERN, "README.md")
        todo_progress = read_progress(TODO, TODO_PATTERN, "todo.txt")
    except RuntimeError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1

    if readme_progress != todo_progress:
        print(
            "FEHLER: Fortschrittsangaben widersprechen sich: "
            f"README.md={readme_progress} %, todo.txt={todo_progress} %.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: Fortschrittsangaben stimmen überein ({readme_progress} %).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
