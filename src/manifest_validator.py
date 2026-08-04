"""Validierung des verbindlichen Linux-, Layout- und Sicherheitsmanifests.

Die Prüfung verwendet nur die Python-Standardbibliothek. Dadurch kann sie vor dem
Start der grafischen Oberfläche und in der CI ohne GUI-Abhängigkeiten laufen.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

EXPECTED_PROJECT_NAME = "MULTIMODULTOOL2026"
EXPECTED_SCHEMA_VERSION = "1.4.0"
EXPECTED_ZONE_IDS = tuple(f"Z{index:02d}" for index in range(1, 10))
EXPECTED_OPERATING_SYSTEMS = ("linux",)
EXPECTED_DISTRIBUTIONS = ("Kubuntu 22.04 LTS", "Kubuntu 24.04 LTS")
EXPECTED_DISPLAY_SERVERS = ("X11", "Wayland")


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    data: dict[str, Any] | None = None

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.is_valid:
            suffix = f", {len(self.warnings)} Warnung(en)" if self.warnings else ""
            return f"Linux- und Layoutvertrag gültig: 9 Pflichtzonen erkannt{suffix}."
        return f"Manifest ungültig: {len(self.errors)} Fehler."


def _require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} muss ein JSON-Objekt sein.")
        return {}
    return value


def _require_exact_list(
    value: Any,
    expected: tuple[str, ...],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append(f"{label} muss eine Liste sein.")
    elif tuple(value) != expected:
        errors.append(f"{label} muss exakt {list(expected)!r} sein.")


def _require_equal(
    mapping: dict[str, Any],
    expected: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    for key, value in expected.items():
        if mapping.get(key) != value:
            errors.append(f"{label}.{key} muss {value!r} sein.")


def validate_manifest(
    manifest_path: Path,
    project_root: Path | None = None,
) -> ValidationResult:
    manifest_path = manifest_path.resolve()
    project_root = (project_root or manifest_path.parent).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_path.is_file():
        return ValidationResult((f"Manifest fehlt: {manifest_path}",), (), None)
    try:
        parsed: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return ValidationResult(("Manifest ist nicht als UTF-8 lesbar.",), (), None)
    except json.JSONDecodeError as exc:
        return ValidationResult(
            (f"Ungültiges JSON in Zeile {exc.lineno}, Spalte {exc.colno}: {exc.msg}",),
            (),
            None,
        )
    except OSError as exc:
        return ValidationResult((f"Manifest konnte nicht gelesen werden: {exc}",), (), None)

    data = _require_mapping(parsed, "Wurzelelement", errors)
    if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        errors.append(f"schemaVersion muss {EXPECTED_SCHEMA_VERSION!r} sein.")

    project = _require_mapping(data.get("project"), "project", errors)
    if project.get("name") != EXPECTED_PROJECT_NAME:
        errors.append(f"project.name muss {EXPECTED_PROJECT_NAME!r} sein.")

    platform = _require_mapping(data.get("platformPolicy"), "platformPolicy", errors)
    _require_exact_list(
        platform.get("supportedOperatingSystems"),
        EXPECTED_OPERATING_SYSTEMS,
        "platformPolicy.supportedOperatingSystems",
        errors,
    )
    _require_exact_list(
        platform.get("primaryDistributions"),
        EXPECTED_DISTRIBUTIONS,
        "platformPolicy.primaryDistributions",
        errors,
    )
    _require_exact_list(
        platform.get("displayServers"),
        EXPECTED_DISPLAY_SERVERS,
        "platformPolicy.displayServers",
        errors,
    )
    _require_equal(
        platform,
        {
            "desktopEnvironments": ["KDE Plasma"],
            "architectures": ["x86_64"],
            "unsupportedPlatformsMustBeBlocked": True,
            "browserOrPwaTarget": False,
            "crossPlatformCompatibilityIsGoal": False,
        },
        "platformPolicy",
        errors,
    )

    reference = _require_mapping(data.get("referenceAsset"), "referenceAsset", errors)
    reference_path = reference.get("path")
    if not isinstance(reference_path, str) or not reference_path.strip():
        errors.append("referenceAsset.path muss einen nicht leeren Pfad enthalten.")
    else:
        resolved_reference = (project_root / reference_path).resolve()
        try:
            resolved_reference.relative_to(project_root)
        except ValueError:
            errors.append("referenceAsset.path darf das Projektverzeichnis nicht verlassen.")
        else:
            if not resolved_reference.is_file():
                errors.append(f"Referenzdatei fehlt: {reference_path}")

    zones = data.get("zones")
    if not isinstance(zones, list):
        errors.append("zones muss eine Liste sein.")
        zones = []
    if len(zones) != len(EXPECTED_ZONE_IDS):
        errors.append(f"Es werden exakt 9 Zonen erwartet, gefunden: {len(zones)}.")
    zone_ids: list[str] = []
    zone_keys: list[str] = []
    zone_orders: list[int] = []
    for index, raw_zone in enumerate(zones, start=1):
        zone = _require_mapping(raw_zone, f"zones[{index - 1}]", errors)
        zone_id = zone.get("id")
        zone_key = zone.get("key")
        zone_order = zone.get("order")
        if isinstance(zone_id, str):
            zone_ids.append(zone_id)
        else:
            errors.append(f"Zone {index}: id fehlt oder ist kein Text.")
        if isinstance(zone_key, str) and zone_key.strip():
            zone_keys.append(zone_key)
        else:
            errors.append(f"Zone {index}: key fehlt oder ist leer.")
        if isinstance(zone_order, int) and not isinstance(zone_order, bool):
            zone_orders.append(zone_order)
        else:
            errors.append(f"Zone {index}: order muss eine Ganzzahl sein.")
        if zone.get("required") is not True:
            errors.append(f"Zone {zone_id or index}: required muss true sein.")
    if tuple(zone_ids) != EXPECTED_ZONE_IDS:
        errors.append("Zonenreihenfolge muss exakt " + ", ".join(EXPECTED_ZONE_IDS) + " sein.")
    if len(set(zone_ids)) != len(zone_ids):
        errors.append("Zonen-IDs müssen eindeutig sein.")
    if len(set(zone_keys)) != len(zone_keys):
        errors.append("Zonen-Schlüssel müssen eindeutig sein.")
    if zone_orders != list(range(1, 10)):
        errors.append("Zonen-order muss lückenlos von 1 bis 9 laufen.")

    trash = _require_mapping(data.get("projectTrashPolicy"), "projectTrashPolicy", errors)
    _require_equal(
        trash,
        {
            "projectRelative": True,
            "controlDirectory": ".multimodultool2026/trash/transactions",
            "manifestSchemaVersion": 1,
            "privateDirectoryMode": "0700",
            "privateManifestMode": "0600",
            "previewMustBeReadOnly": True,
            "atomicPrimitive": "os.replace",
            "sameFilesystemRequired": True,
            "copyThenDeleteForbidden": True,
            "permanentDeleteAvailable": False,
            "restoreConflictMustBlock": True,
            "damagedManifestMustRemainUnchanged": True,
        },
        "projectTrashPolicy",
        errors,
    )

    undo = _require_mapping(data.get("undoRedoPolicy"), "undoRedoPolicy", errors)
    _require_equal(
        undo,
        {
            "projectRelative": True,
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

    overview = _require_mapping(
        data.get("transactionOverviewPolicy"),
        "transactionOverviewPolicy",
        errors,
    )
    _require_equal(
        overview,
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

    validation = _require_mapping(data.get("validation"), "validation", errors)
    _require_equal(
        validation,
        {
            "requiredZoneCount": 9,
            "requiredZoneOrder": list(EXPECTED_ZONE_IDS),
        },
        "validation",
        errors,
    )
    for documentation_path in validation.get("documentation", []):
        if not isinstance(documentation_path, str) or not (project_root / documentation_path).is_file():
            errors.append(f"Pflichtdokument fehlt: {documentation_path!r}")

    iteration = _require_mapping(data.get("iterationPolicy"), "iterationPolicy", errors)
    _require_equal(
        iteration,
        {
            "githubRepositoryMustBeUpdated": True,
            "targetBranch": "main",
            "completionRequiresCommitSha": True,
            "completionRequiresValidationReport": True,
            "localOnlyCompletionAllowed": False,
        },
        "iterationPolicy",
        errors,
    )

    preservation = _require_mapping(data.get("preservationPolicy"), "preservationPolicy", errors)
    if preservation.get("explicitUserApprovalRequiredForStructuralDeviation") is not True:
        errors.append("Strukturelle Layoutabweichungen müssen Nutzerfreigabe verlangen.")

    return ValidationResult(tuple(errors), tuple(warnings), data)


def format_validation_result(result: ValidationResult) -> str:
    lines = [result.summary()]
    lines.extend(f"FEHLER: {item}" for item in result.errors)
    lines.extend(f"WARNUNG: {item}" for item in result.warnings)
    return "\n".join(lines)
