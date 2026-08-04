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
    "docs/GITHUB_ZUGRIFF.md",
    "docs/UI_BASISVORLAGE.md",
    "docs/XDG_PFADVERTRAG.md",
    "layout-manifest.json",
    "requirements.txt",
    "setup.sh",
    "start.sh",
    "src/__init__.py",
    "src/main.py",
    "src/manifest_validator.py",
    "src/theme.qss",
    "src/xdg_paths.py",
    "standards/UI_LAYOUT_STANDARD_2026.md",
    "tests/__init__.py",
    "tests/test_repository_contract.py",
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
    "docs/GITHUB_ZUGRIFF.md",
    "docs/XDG_PFADVERTRAG.md",
)

PYTHON_FILES = (
    "src/main.py",
    "src/manifest_validator.py",
    "src/xdg_paths.py",
    "tests/test_repository_contract.py",
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
    errors.extend(validate_manifest(ROOT / "layout-manifest.json", ROOT).errors)


def parse_todo_counts(todo_text: str) -> tuple[int, int]:
    completed = len(re.findall(r"(?m)^\s*-\s*\[x\]\s+", todo_text, re.IGNORECASE))
    open_items = len(re.findall(r"(?m)^\s*-\s*\[\s\]\s+", todo_text))
    return completed, open_items


def check_progress_consistency(errors: list[str]) -> None:
    readme = read_text("README.md", errors)
    completed, open_items = parse_todo_counts(read_text("TODO.md", errors))
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
    for phrase in ("--check-only", ".venv.setup-", "PySide6", "KDE"):
        if phrase not in setup_source:
            errors.append(f"Einrichtungsassistent enthält Pflichtmerkmal nicht: {phrase}")
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
    for phrase in (
        "Programmverzeichnis",
        "Symlink",
        "0700",
        "--validate-only",
        "Nachvalidierung",
    ):
        if phrase not in contract:
            errors.append(f"XDG-Pfadvertrag fehlt Pflichtaussage: {phrase!r}")
    if "PROJECT_ROOT / \"logs\"" in main_source:
        errors.append("src/main.py enthält einen verbotenen Logpfad im Quellbaum.")
    if "PROJECT_ROOT / \"data\"" in main_source:
        errors.append("src/main.py enthält einen verbotenen Datenpfad im Quellbaum.")


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
                errors.append(
                    f"Syntaxfehler in {relative_path}:{exc.lineno}: {exc.msg}"
                )


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
        ("Einrichtungsassistent", check_setup_contract),
        ("XDG-Pfadvertrag", check_xdg_contract),
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
