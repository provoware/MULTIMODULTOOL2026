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
    "src/project_trash.py", "src/undo_redo.py", "src/transaction_overview.py",
    "src/trash_contract_panel.py", "tests/test_single_instance.py",
    "tests/test_single_instance_stress.py", "tests/test_diagnostics_center.py",
    "tests/test_project_trash.py", "tests/test_undo_redo.py",
    "tests/test_transaction_overview.py", "tests/test_gui_offscreen.py",
    "tests/test_gui_trash_contract.py", "tests/test_settings_failpoints.py",
    "docs/XDG_PFADVERTRAG.md", "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md",
    "docs/PAPIERKORBVERTRAG.md", "docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md",
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
            compile(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT)), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"Python-Prüfung fehlgeschlagen: {path.relative_to(ROOT)}: {exc}")


def _check_mapping(
    mapping: object,
    expected: dict[str, object],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(mapping, dict):
        errors.append(f"Manifest: {label} fehlt oder ist kein Objekt.")
        return
    for key, expected_value in expected.items():
        if mapping.get(key) != expected_value:
            errors.append(f"Manifest: {label}.{key} ist inkonsistent.")


def check_manifest(errors: list[str]) -> None:
    try:
        manifest = json.loads(text("layout-manifest.json", errors))
    except json.JSONDecodeError as exc:
        errors.append(f"layout-manifest.json: ungültiges JSON: {exc}")
        return
    if manifest.get("schemaVersion") != "1.4.0":
        errors.append("Manifest: schemaVersion muss 1.4.0 sein.")
    zones = manifest.get("zones", [])
    expected_zones = [f"Z{index:02d}" for index in range(1, 10)]
    if [zone.get("id") for zone in zones if isinstance(zone, dict)] != expected_zones:
        errors.append("Manifest: neun Layoutzonen sind inkonsistent.")
    _check_mapping(
        manifest.get("singleInstancePolicy"),
        {
            "transport": "unix-domain-socket",
            "peerUidRequired": True,
            "parallelSecondaryStressCount": 20,
            "activationAtMostOnceRequired": True,
            "cleanupAfterPrimaryExitRequired": True,
        },
        "singleInstancePolicy",
        errors,
    )
    _check_mapping(
        manifest.get("projectTrashPolicy"),
        {
            "projectRelative": True,
            "privateDirectoryMode": "0700",
            "privateManifestMode": "0600",
            "previewMustBeReadOnly": True,
            "atomicPrimitive": "os.replace",
            "sameFilesystemRequired": True,
            "copyThenDeleteForbidden": True,
            "permanentDeleteAvailable": False,
            "sourceFingerprintRequired": True,
            "restoreConflictMustBlock": True,
            "damagedManifestMustRemainUnchanged": True,
            "centralErrorContractRequired": True,
        },
        "projectTrashPolicy",
        errors,
    )
    _check_mapping(
        manifest.get("undoRedoPolicy"),
        {
            "journalPath": ".multimodultool2026/history/actions.jsonl",
            "journalSchemaVersion": 1,
            "historyDirectoryMode": "0700",
            "journalMode": "0600",
            "appendOnly": True,
            "hashChain": "sha256",
            "uniqueActionIdsRequired": True,
            "uniqueTransactionIdsRequired": True,
            "intentAndCompletionEventsRequired": True,
            "undoOrder": "reverse",
            "redoOrder": "forward",
            "idempotentPerAction": True,
            "conflictMustBlock": True,
            "absolutePathsForbidden": True,
            "minimumSequentialRoundTripActions": 10,
        },
        "undoRedoPolicy",
        errors,
    )
    _check_mapping(
        manifest.get("transactionOverviewPolicy"),
        {
            "readOnly": True,
            "visibleStates": ["prepared", "trashed", "restored", "damaged"],
            "repairAllowed": False,
            "restoreAllowed": False,
            "deleteAllowed": False,
            "uploadAllowed": False,
            "automaticExportAllowed": False,
            "maximumRecords": 1000,
            "manifestBytesMustRemainUnchanged": True,
        },
        "transactionOverviewPolicy",
        errors,
    )
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
    expected = {"done": 29, "open": 38, "total": 67, "percent": 43}
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


def check_runtime_contract(errors: list[str]) -> None:
    main_source = text("src/main.py", errors)
    instance = text("src/single_instance.py", errors)
    trash = text("src/project_trash.py", errors)
    history = text("src/undo_redo.py", errors)
    overview = text("src/transaction_overview.py", errors)
    panel = text("src/trash_contract_panel.py", errors)
    workflow = text(".github/workflows/repository-contract.yml", errors)

    for marker in ("SingleInstanceCoordinator", "resolve_runtime_root", "drain_messages"):
        if marker not in main_source:
            errors.append(f"Single-Instance-Integration fehlt: {marker}")
    for marker in ("socket.AF_UNIX", "socket.SO_PEERCRED", "activate", "show-diagnostics"):
        if marker not in instance:
            errors.append(f"Single-Instance-Vertrag fehlt: {marker}")
    for marker in (
        "MMTTRASH-", "manifest.json", "preview_trash_move", "execute_trash_move",
        "restore_transaction", "os.replace", "SafeOperationError", "0o700", "0o600",
    ):
        if marker not in trash:
            errors.append(f"Papierkorbvertrag fehlt: {marker}")
    for marker in (
        "O_APPEND", "O_NOFOLLOW", "fcntl.flock", "eventHash", "previousHash",
        "undo-intent", "redo-intent", "undo_last", "redo_next", "reconcile",
        "restore_transaction", "preview_trash_move", "MMTACTION-",
    ):
        if marker not in history:
            errors.append(f"Undo-/Redo-Vertrag fehlt: {marker}")
    for marker in (
        "prepared", "trashed", "restored", "damaged", "maximum_records",
        "inspect_transaction", "read_transaction_overview",
    ):
        if marker not in overview:
            errors.append(f"Transaktionsübersicht fehlt: {marker}")
    for marker in (
        "transactionOverview", "transactionStateFilter", "transactionList",
        "transactionDetail", "transactionReadOnlyNotice",
    ):
        if marker not in panel:
            errors.append(f"Transaktions-UI-Vertrag fehlt: {marker}")
    for forbidden in (
        "permanentDeleteButton", "emptyTrashButton", "transactionRestoreButton",
        "transactionRepairButton", "transactionDeleteButton", "transactionUploadButton",
        "transactionExportButton",
    ):
        if forbidden in panel:
            errors.append(f"Verbotene Transaktionsfunktion vorhanden: {forbidden}")
    for marker in (
        "tests.test_project_trash", "tests.test_undo_redo",
        "tests.test_transaction_overview", "tests.test_single_instance_stress",
        "tests.test_gui_trash_contract", "QT_QPA_PLATFORM",
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
        check_runtime_contract,
    ):
        check(errors)
    if errors:
        print("ROT: Repository-Vertrag ist nicht erfüllt.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("GRÜN: Linux-, Papierkorb-, Undo-/Redo-, Instanz- und Diagnosevertrag sind konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
