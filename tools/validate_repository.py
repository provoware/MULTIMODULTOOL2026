#!/usr/bin/env python3
"""Dependency-light repository contract validator for MULTIMODULTOOL2026."""

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
    "src/run_control.py", "src/trash_contract_panel.py",
    "tests/test_single_instance.py", "tests/test_single_instance_stress.py",
    "tests/test_diagnostics_center.py", "tests/test_project_trash.py",
    "tests/test_undo_redo.py", "tests/test_transaction_overview.py",
    "tests/test_run_control.py", "tests/test_run_control_sigkill.py",
    "tests/helpers/run_control_worker.py", "tests/test_gui_offscreen.py",
    "tests/test_gui_trash_contract.py", "tests/test_settings_failpoints.py",
    "tests/test_release_builder.py", "tests/helpers/kubuntu_release_lifecycle.sh",
    "tools/build_deb_release.py", "release/release-manager.sh",
    "release/multimodultool2026-launcher.sh", "release/package-files.txt",
    "release/requirements-release.txt", "release/VERSION",
    "docs/XDG_PFADVERTRAG.md", "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md", "docs/PAPIERKORBVERTRAG.md",
    "docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md",
    "docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md", "docs/LINUX_RELEASEVERTRAG.md",
    ".github/workflows/repository-contract.yml", ".github/workflows/release-candidate.yml",
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


def check_manifest(errors: list[str]) -> None:
    try:
        manifest = json.loads(text("layout-manifest.json", errors))
    except json.JSONDecodeError as exc:
        errors.append(f"layout-manifest.json: ungültiges JSON: {exc}")
        return
    if manifest.get("schemaVersion") != "1.5.0":
        errors.append("Manifest: schemaVersion muss 1.5.0 sein.")
    zones = manifest.get("zones", [])
    expected = [f"Z{index:02d}" for index in range(1, 10)]
    if [zone.get("id") for zone in zones if isinstance(zone, dict)] != expected:
        errors.append("Manifest: neun Layoutzonen sind inkonsistent.")
    run = manifest.get("runControlPolicy", {})
    expected_run = {
        "runsPath": ".multimodultool2026/runs",
        "runIdPrefix": "MMTRUN-",
        "runDirectoryMode": "0700",
        "privateFileMode": "0600",
        "immutablePlanRequired": True,
        "atomicCheckpointRequired": True,
        "advisoryLock": "flock",
        "idempotentResumeRequired": True,
        "journalAndManifestReconciliationRequired": True,
        "duplicateOperationsForbidden": True,
        "maximumItems": 1000,
    }
    for key, expected_value in expected_run.items():
        if run.get(key) != expected_value:
            errors.append(f"Manifest: Wiederanlauf-Feld {key} ist inkonsistent.")
    required_stages = {
        "before-intent", "after-intent", "before-file-operation",
        "after-file-operation", "before-fsync", "after-fsync",
        "before-manifest-completion", "after-manifest-completion",
        "before-journal-completion", "after-journal-completion",
    }
    if set(run.get("sigkillStages", [])) != required_stages:
        errors.append("Manifest: SIGKILL-Stufen sind unvollständig.")
    release = manifest.get("releasePolicy", {})
    expected_release = {
        "packageFormat": "deb",
        "architecture": "amd64",
        "buildIdRequired": True,
        "reproducibleFileManifestRequired": True,
        "offlineWheelhouseRequired": True,
        "safeInstallUpgradeRollbackUninstallRequired": True,
        "kubuntuMatrix": ["22.04", "24.04"],
        "signatureDeferredTo": "P3-009",
    }
    for key, expected_value in expected_release.items():
        if release.get(key) != expected_value:
            errors.append(f"Manifest: Release-Feld {key} ist inkonsistent.")
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
    if total == 0:
        errors.append("TODO enthält keine auswertbaren Aufgaben-Checkboxen.")
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
            errors.append(f"GUI-Fortschritt fehlt: {marker}")


def check_run_contract(errors: list[str]) -> None:
    run = text("src/run_control.py", errors)
    panel = text("src/trash_contract_panel.py", errors)
    workflow = text(".github/workflows/repository-contract.yml", errors)
    for marker in (
        "MMTRUN-", "plan.json", "checkpoint.json", "cancel.request", "run.lock",
        "fcntl.flock", "os.replace", "resume_run", "request_cancel",
        "before-intent", "after-journal-completion", "_write_manifest_atomic",
        "UndoRedoJournal", "inspect_transaction", "PRIVATE_DIRECTORY_MODE", "PRIVATE_FILE_MODE",
    ):
        if marker not in run:
            errors.append(f"Abbruch-/Wiederanlaufvertrag fehlt: {marker}")
    for marker in ("runControlContract", "runControlRules", "SIGKILL", "keine Doppeloperation"):
        if marker.lower() not in panel.lower():
            errors.append(f"Wiederanlauf-UI-Vertrag fehlt: {marker}")
    for forbidden in ("runStartButton", "runCancelButton", "runResumeButton", "runRepairButton"):
        if forbidden in panel:
            errors.append(f"Unfreigegebene Laufaktion vorhanden: {forbidden}")
    for marker in (
        "tests.test_run_control", "tests.test_run_control_sigkill",
        "tests.test_gui_trash_contract", "QT_QPA_PLATFORM",
    ):
        if marker not in workflow:
            errors.append(f"CI-Wiederanlaufvertrag fehlt: {marker}")


def check_release_contract(errors: list[str]) -> None:
    builder = text("tools/build_deb_release.py", errors)
    manager = text("release/release-manager.sh", errors)
    launcher = text("release/multimodultool2026-launcher.sh", errors)
    workflow = text(".github/workflows/release-candidate.yml", errors)
    contract = text("docs/LINUX_RELEASEVERTRAG.md", errors)
    for marker in (
        "MMTBUILD-", "FILE_MANIFEST.sha256", "BUILD_INFO.json", "SOURCE_DATE_EPOCH",
        "dpkg-deb", "wheelhouse", "amd64", "sha256",
    ):
        if marker not in builder:
            errors.append(f"Releasebuilder-Vertrag fehlt: {marker}")
    for marker in (
        "verify", "install", "upgrade", "rollback", "uninstall", "--yes",
        "apt-get install", "--allow-downgrades", "purge-current-user-data",
    ):
        if marker not in manager:
            errors.append(f"Release-Manager-Vertrag fehlt: {marker}")
    for marker in ("--no-index", "--find-links", "MMT_BUILD_ID", "--verify-installation"):
        if marker not in launcher:
            errors.append(f"Offline-Launcher-Vertrag fehlt: {marker}")
    for marker in ("22.04", "24.04", "kubuntu_release_lifecycle.sh", "upload-artifact"):
        if marker not in workflow:
            errors.append(f"Release-CI-Vertrag fehlt: {marker}")
    for marker in ("Build-ID", "reproduzierbar", "Installation", "Upgrade", "Rollback", "Deinstallation", "Kubuntu 22.04", "24.04"):
        if marker not in contract:
            errors.append(f"Linux-Releasevertrag fehlt: {marker}")


def main() -> int:
    errors: list[str] = []
    for check in (
        check_required,
        check_python,
        check_manifest,
        check_progress,
        check_run_contract,
        check_release_contract,
    ):
        check(errors)
    if errors:
        print("ROT: Repository-Vertrag ist nicht erfüllt.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("GRÜN: Linux-, Transaktions-, Wiederanlauf- und Releasevertrag sind konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
