#!/usr/bin/env python3
"""Dependency-light repository contract validator for MULTIMODULTOOL2026."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md", "AGENTS.md", "ANLEITUNG_TOOL.md", "CHANGELOG.md",
    "TODO.md", "SCHWACHSTELLEN.md", "UPGRADE_POOL.md", "ENTWICKLERDOKU.md",
    "layout-manifest.json", "src/main.py", "src/help_dialog.py",
    "src/single_instance.py", "src/diagnostics_center.py", "src/error_events.py",
    "src/error_dialog.py", "src/project_trash.py", "src/undo_redo.py",
    "src/transaction_overview.py", "src/run_control.py", "src/trash_contract_panel.py",
    "tests/test_single_instance.py", "tests/test_single_instance_stress.py",
    "tests/test_diagnostics_center.py", "tests/test_project_trash.py",
    "tests/test_undo_redo.py", "tests/test_transaction_overview.py",
    "tests/test_run_control.py", "tests/test_run_control_sigkill.py",
    "tests/helpers/run_control_worker.py", "tests/test_gui_offscreen.py",
    "tests/test_gui_trash_contract.py", "tests/test_settings_failpoints.py",
    "tests/test_release_builder.py", "tests/test_finalize_release_artifacts.py",
    "tests/helpers/kubuntu_release_lifecycle.sh", "tools/build_deb_release.py",
    "tools/finalize_release_artifacts.py", "release/release-manager.sh",
    "release/multimodultool2026-launcher.sh", "release/package-files.txt",
    "release/requirements-release.txt", "release/release-status.json", "release/VERSION",
    "docs/XDG_PFADVERTRAG.md", "docs/EINSTELLUNGSVERTRAG.md",
    "docs/FEHLER_UND_EREIGNISVERTRAG.md",
    "docs/SINGLE_INSTANCE_UND_DIAGNOSEVERTRAG.md", "docs/PAPIERKORBVERTRAG.md",
    "docs/UNDO_REDO_UND_TRANSAKTIONSVERTRAG.md",
    "docs/ABBRUCH_UND_WIEDERANLAUFVERTRAG.md", "docs/LINUX_RELEASEVERTRAG.md",
    ".github/workflows/repository-contract.yml", ".github/workflows/release-candidate.yml",
)
RESIDUE_SUFFIXES = (".bak", ".old", ".orig", ".rej", ".tmp", ".swp", ".pyc")


def text(path: str, errors: list[str]) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: nicht als UTF-8 lesbar: {exc}")
        return ""


def json_object(path: str, errors: list[str]) -> dict[str, object]:
    try:
        payload = json.loads(text(path, errors))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: ungültiges JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{path}: JSON-Wurzel muss ein Objekt sein.")
        return {}
    return payload


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


def tracked_files() -> tuple[Path, ...]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
    except OSError:
        return ()
    if completed.returncode != 0:
        return ()
    return tuple(
        Path(os.fsdecode(raw))
        for raw in completed.stdout.split(b"\0")
        if raw
    )


def check_repository_hygiene(errors: list[str]) -> None:
    for relative in tracked_files():
        name = relative.name
        lowered = name.lower()
        if name.endswith("~") or lowered.endswith(RESIDUE_SUFFIXES):
            errors.append(f"Überrestdatei ist versioniert: {relative.as_posix()}")
        if "__pycache__" in relative.parts or lowered.endswith(".pyc"):
            errors.append(f"Python-Laufzeitrest ist versioniert: {relative.as_posix()}")
        if "_save_" in name:
            errors.append(
                f"Quellbaumdatei trägt verbotenen Releasezusatz _save_: {relative.as_posix()}"
            )


def check_manifest(errors: list[str]) -> None:
    manifest = json_object("layout-manifest.json", errors)
    if not manifest:
        return
    if manifest.get("schemaVersion") != "1.5.0":
        errors.append("Manifest: schemaVersion muss 1.5.0 sein.")
    zones = manifest.get("zones", [])
    expected = [f"Z{index:02d}" for index in range(1, 10)]
    if not isinstance(zones, list) or [
        zone.get("id") for zone in zones if isinstance(zone, dict)
    ] != expected:
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
    if not isinstance(run, dict):
        errors.append("Manifest: runControlPolicy fehlt.")
        run = {}
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
        "packageName": "multimodultool2026",
        "architecture": "amd64",
        "buildIdPrefix": "MMTBUILD-",
        "reproducibleBuildRequired": True,
        "offlineFirstStartRequired": True,
        "upgradeRequired": True,
        "rollbackRequired": True,
        "completeUninstallRequired": True,
        "kubuntuMatrix": ["22.04", "24.04"],
        "signatureDeferredTo": "P3-009",
    }
    if not isinstance(release, dict):
        errors.append("Manifest: releasePolicy fehlt.")
        release = {}
    for key, expected_value in expected_release.items():
        if release.get(key) != expected_value:
            errors.append(f"Manifest: Release-Feld {key} ist inkonsistent.")
    validation = manifest.get("validation", {})
    documentation = validation.get("documentation", []) if isinstance(validation, dict) else []
    for path in documentation:
        if not isinstance(path, str) or not (ROOT / path).is_file():
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


def check_help_contract(errors: list[str]) -> None:
    main_source = text("src/main.py", errors)
    help_source = text("src/help_dialog.py", errors)
    gui_test = text("tests/test_gui_offscreen.py", errors)
    for marker in (
        "build_help_dialog", "helpNavigation", "WA_AlwaysShowToolTips",
        "setAccessibleDescription", "window.helpDialog",
    ):
        if marker not in main_source:
            errors.append(f"Hilfe-/Tooltip-Vertrag fehlt in src/main.py: {marker}")
    for marker in (
        "HELP_SECTIONS", "Sicherer Einstieg", "Gesperrte Bereiche",
        "Abbruch und Fortsetzung", "Release-Dateien", "helpDialogCloseButton",
    ):
        if marker not in help_source:
            errors.append(f"Kontext-Hilfe fehlt: {marker}")
    for marker in (
        "test_help_button_opens_read_only_contextual_help",
        "test_unreleased_actions_are_disabled_and_explain_their_blocker",
        "test_progress_widgets_use_the_authoritative_constants",
    ):
        if marker not in gui_test:
            errors.append(f"GUI-Hilferegression fehlt: {marker}")


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


def check_release_status(errors: list[str]) -> None:
    policy = json_object("release/release-status.json", errors)
    readme = text("README.md", errors)
    finalizer = text("tools/finalize_release_artifacts.py", errors)
    test_source = text("tests/test_finalize_release_artifacts.py", errors)
    if policy.get("releaseSuffix") != "_save_":
        errors.append("Release-Status: releaseSuffix muss _save_ sein.")
    if policy.get("sourceRenameForbidden") is not True:
        errors.append("Release-Status: Quellumbenennung muss verboten sein.")
    if policy.get("suffixAppliedAfterGreenLifecycleMatrix") is not True:
        errors.append("Release-Status: _save_ darf erst nach grüner Matrix entstehen.")
    ready = policy.get("readyArtifacts", [])
    if not isinstance(ready, list) or len(ready) != 6:
        errors.append("Release-Status: exakt sechs fertige Artefaktklassen sind erforderlich.")
    else:
        for entry in ready:
            if not isinstance(entry, dict) or "_save_" not in str(entry.get("outputPattern", "")):
                errors.append("Release-Status: fertiges Ausgabemuster ohne _save_.")
    if not isinstance(policy.get("unfinished"), list) or not policy.get("unfinished"):
        errors.append("Release-Status: unfertige Bereiche fehlen.")
    for marker in (
        "| Fertige Dateien nach grüner Kubuntu-Matrix | Unfertig oder nicht freigegeben |",
        "multimodultool2026_<version>_amd64_save_.deb",
        "RELEASE_STATUS_save_.json",
        "Quelldateien werden nicht umbenannt",
    ):
        if marker not in readme:
            errors.append(f"README-Releaseübersicht fehlt: {marker}")
    for marker in (
        "SAVE_SUFFIX = \"_save_\"", "replace_directory_atomically",
        "read_sidecar", "sourceRenameForbidden", "ready-after-green-kubuntu-matrix",
    ):
        if marker not in finalizer:
            errors.append(f"Release-Finalizer-Vertrag fehlt: {marker}")
    for marker in (
        "test_every_final_file_contains_save_suffix_and_hashes_remain_valid",
        "test_existing_generated_output_is_replaced_without_stale_files",
        "test_symlinked_required_artifact_is_blocked",
    ):
        if marker not in test_source:
            errors.append(f"Release-Finalizer-Regression fehlt: {marker}")


def check_release_contract(errors: list[str]) -> None:
    builder = text("tools/build_deb_release.py", errors)
    manager = text("release/release-manager.sh", errors)
    launcher = text("release/multimodultool2026-launcher.sh", errors)
    workflow = text(".github/workflows/release-candidate.yml", errors)
    lifecycle = text("tests/helpers/kubuntu_release_lifecycle.sh", errors)
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
    for marker in (
        "22.04", "24.04", "kubuntu_release_lifecycle.sh", "if: always()",
        "outer-exit-code", "finalize_release_artifacts.py",
        "multimodultool2026-release-save", "tests.test_finalize_release_artifacts",
    ):
        if marker not in workflow:
            errors.append(f"Release-CI-Vertrag fehlt: {marker}")
    for marker in (
        'dpkg-query -W -f="\\${Status}\\n"', "inner-exit-code",
        "original-exit-code", "phase completed", "recover-damaged-runtime",
    ):
        if marker not in lifecycle:
            errors.append(f"Kubuntu-Evidenzvertrag fehlt: {marker}")
    for marker in (
        "Build-ID", "reproduzierbar", "Installation", "Upgrade", "Rollback",
        "Deinstallation", "Kubuntu 22.04", "24.04", "if: always()", "_save_",
    ):
        if marker not in contract:
            errors.append(f"Linux-Releasevertrag fehlt: {marker}")


def main() -> int:
    errors: list[str] = []
    for check in (
        check_required,
        check_python,
        check_repository_hygiene,
        check_manifest,
        check_progress,
        check_help_contract,
        check_run_contract,
        check_release_status,
        check_release_contract,
    ):
        check(errors)
    if errors:
        print("ROT: Repository-Vertrag ist nicht erfüllt.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "GRÜN: Linux-, Hilfe-, Hygiene-, Transaktions-, Wiederanlauf- und Releasevertrag sind konsistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
