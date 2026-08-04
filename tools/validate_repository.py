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
    "docs/UI_BASISVORLAGE.md",
    "layout-manifest.json",
    "requirements.txt",
    "src/__init__.py",
    "src/main.py",
    "src/manifest_validator.py",
    "src/theme.qss",
    "standards/UI_LAYOUT_STANDARD_2026.md",
    "start.sh",
    "tests/__init__.py",
    "tests/test_repository_contract.py",
    "tools/validate_repository.py",
)

MAINTAINED_DOCS = (
    "CHANGELOG.md",
    "ANLEITUNG_TOOL.md",
    "TODO.md",
    "SCHWACHSTELLEN.md",
    "UPGRADE_POOL.md",
    "ENTWICKLERDOKU.md",
)


def read_text(relative_path: str, errors: list[str]) -> str:
    path = ROOT / relative_path
    try:
        return path.read_text(encoding="utf-8")
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


def parse_todo_counts(todo_text: str) -> tuple[int, int]:
    completed = len(re.findall(r"(?m)^\s*-\s*\[x\]\s+", todo_text, re.IGNORECASE))
    open_items = len(re.findall(r"(?m)^\s*-\s*\[\s\]\s+", todo_text))
    return completed, open_items


def check_progress_consistency(errors: list[str]) -> None:
    readme = read_text("README.md", errors)
    todo = read_text("TODO.md", errors)
    completed, open_items = parse_todo_counts(todo)
    total = completed + open_items
    expected_percent = round((completed / total) * 100) if total else 0

    patterns = {
        "percent": r"Entwicklungsfortschritt:\s*(\d+)\s*%",
        "completed": r"Erledigte Punkte:\s*(\d+)",
        "open": r"Offene Punkte:\s*(\d+)",
        "total": r"Gesamtpunkte:\s*(\d+)",
    }
    extracted: dict[str, int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, readme)
        if not match:
            errors.append(f"README-Fortschrittswert fehlt: {key}")
        else:
            extracted[key] = int(match.group(1))

    expected = {
        "percent": expected_percent,
        "completed": completed,
        "open": open_items,
        "total": total,
    }
    for key, value in expected.items():
        if key in extracted and extracted[key] != value:
            errors.append(
                f"README-{key} ist {extracted[key]}, aus TODO.md ergeben sich {value}."
            )


def check_agents_policy(errors: list[str]) -> None:
    agents = read_text("AGENTS.md", errors)
    for document in MAINTAINED_DOCS:
        if document not in agents:
            errors.append(f"AGENTS.md nennt die Pflegepflicht für {document} nicht.")
    for phrase in ("Entwicklungsfortschritt", "Erledigte Punkte", "Offene Punkte"):
        if phrase not in agents:
            errors.append(f"AGENTS.md enthält die Fortschrittspflicht {phrase!r} nicht.")


def check_linux_scope(errors: list[str]) -> None:
    readme = read_text("README.md", errors)
    agents = read_text("AGENTS.md", errors)
    main_source = read_text("src/main.py", errors)
    start_source = read_text("start.sh", errors)

    required_readme_phrases = (
        "ausschließlich für Linux-Desktop-Systeme",
        "Kubuntu 22.04 LTS",
        "Kubuntu 24.04 LTS",
        "Windows, macOS, Android und iOS",
    )
    for phrase in required_readme_phrases:
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
    required_sections = ("## P0", "## P1", "## P2", "## P3", "## P4")
    for heading in required_sections:
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


def check_python_syntax(errors: list[str]) -> None:
    for relative_path in (
        "src/main.py",
        "src/manifest_validator.py",
        "tests/test_repository_contract.py",
        "tools/validate_repository.py",
    ):
        source = read_text(relative_path, errors)
        if not source:
            continue
        try:
            compile(source, relative_path, "exec")
        except SyntaxError as exc:
            errors.append(f"Syntaxfehler in {relative_path}:{exc.lineno}: {exc.msg}")


def check_json(errors: list[str]) -> None:
    try:
        json.loads(read_text("layout-manifest.json", errors))
    except json.JSONDecodeError as exc:
        errors.append(f"layout-manifest.json ist ungültig: {exc}")


def check_start_script(errors: list[str]) -> None:
    content = read_text("start.sh", errors)
    if "set -Eeuo pipefail" not in content:
        errors.append("start.sh verwendet keinen strikten Shell-Modus.")
    if "--validate-only" not in content:
        errors.append("start.sh validiert das Manifest nicht vor dem GUI-Start.")


def main() -> int:
    errors: list[str] = []
    checks: Iterable[tuple[str, Callable[[list[str]], None]]] = (
        ("Pflichtdateien", check_required_files),
        ("Linux-Plattformvertrag", check_linux_scope),
        ("Manifest", check_manifest),
        ("Fortschritt", check_progress_consistency),
        ("Dokumentationspflicht", check_agents_policy),
        ("TODO-Qualität", check_todo_quality),
        ("Python-Syntax", check_python_syntax),
        ("JSON", check_json),
        ("Startroutine", check_start_script),
    )

    for name, check in checks:
        before = len(errors)
        check(errors)
        state = "GRÜN" if len(errors) == before else "ROT"
        print(f"{state}: {name}")

    if errors:
        print("\nRepository-Vertrag verletzt:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nGRÜN: Linux-Repository-Vertrag vollständig erfüllt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
