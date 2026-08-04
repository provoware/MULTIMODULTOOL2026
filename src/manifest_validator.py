"""Validierung des verbindlichen Linux- und Layout-Manifests.

Die Prüfung verwendet nur die Python-Standardbibliothek. Dadurch kann sie vor dem
Start der grafischen Oberfläche und in der CI ohne installierte GUI-Abhängigkeiten
ausgeführt werden.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


EXPECTED_PROJECT_NAME = "MULTIMODULTOOL2026"
EXPECTED_SCHEMA_VERSION = "1.1.0"
EXPECTED_ZONE_IDS = tuple(f"Z{index:02d}" for index in range(1, 10))
EXPECTED_OPERATING_SYSTEMS = ("linux",)
EXPECTED_DISTRIBUTIONS = ("Kubuntu 22.04 LTS", "Kubuntu 24.04 LTS")
EXPECTED_DISPLAY_SERVERS = ("X11", "Wayland")


@dataclass(frozen=True)
class ValidationResult:
    """Unveränderliches Ergebnis einer Manifestprüfung."""

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
        return
    if tuple(value) != expected:
        errors.append(f"{label} muss exakt {list(expected)!r} sein.")


def validate_manifest(manifest_path: Path, project_root: Path | None = None) -> ValidationResult:
    """Prüft Linux-Plattform, Struktur, Zonenvertrag, Referenzdatei und Iterationsregeln."""

    manifest_path = manifest_path.resolve()
    project_root = (project_root or manifest_path.parent).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_path.is_file():
        return ValidationResult((f"Manifest fehlt: {manifest_path}",), (), None)

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        parsed: Any = json.loads(raw)
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
    project = _require_mapping(data.get("project"), "project", errors)
    if project.get("name") != EXPECTED_PROJECT_NAME:
        errors.append(f"project.name muss {EXPECTED_PROJECT_NAME!r} sein.")

    platform_policy = _require_mapping(
        data.get("platformPolicy"), "platformPolicy", errors
    )
    _require_exact_list(
        platform_policy.get("supportedOperatingSystems"),
        EXPECTED_OPERATING_SYSTEMS,
        "platformPolicy.supportedOperatingSystems",
        errors,
    )
    _require_exact_list(
        platform_policy.get("primaryDistributions"),
        EXPECTED_DISTRIBUTIONS,
        "platformPolicy.primaryDistributions",
        errors,
    )
    _require_exact_list(
        platform_policy.get("displayServers"),
        EXPECTED_DISPLAY_SERVERS,
        "platformPolicy.displayServers",
        errors,
    )
    if platform_policy.get("desktopEnvironments") != ["KDE Plasma"]:
        errors.append("platformPolicy.desktopEnvironments muss ['KDE Plasma'] sein.")
    if platform_policy.get("architectures") != ["x86_64"]:
        errors.append("platformPolicy.architectures muss ['x86_64'] sein.")
    if platform_policy.get("unsupportedPlatformsMustBeBlocked") is not True:
        errors.append("Nicht-Linux-Systeme müssen beim Start blockiert werden.")
    if platform_policy.get("browserOrPwaTarget") is not False:
        errors.append("Browser- oder PWA-Ausgabe muss deaktiviert sein.")
    if platform_policy.get("crossPlatformCompatibilityIsGoal") is not False:
        errors.append("Plattformübergreifende Kompatibilität darf kein Projektziel sein.")

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
        if not isinstance(zone_id, str):
            errors.append(f"Zone {index}: id fehlt oder ist kein Text.")
        else:
            zone_ids.append(zone_id)
        if not isinstance(zone_key, str) or not zone_key.strip():
            errors.append(f"Zone {index}: key fehlt oder ist leer.")
        else:
            zone_keys.append(zone_key)
        if not isinstance(zone_order, int):
            errors.append(f"Zone {index}: order muss eine Ganzzahl sein.")
        else:
            zone_orders.append(zone_order)
        if zone.get("required") is not True:
            errors.append(f"Zone {zone_id or index}: required muss true sein.")

    if tuple(zone_ids) != EXPECTED_ZONE_IDS:
        errors.append(
            "Zonenreihenfolge muss exakt " + ", ".join(EXPECTED_ZONE_IDS) + " sein."
        )
    if len(set(zone_ids)) != len(zone_ids):
        errors.append("Zonen-IDs müssen eindeutig sein.")
    if len(set(zone_keys)) != len(zone_keys):
        errors.append("Zonen-Schlüssel müssen eindeutig sein.")
    if zone_orders != list(range(1, 10)):
        errors.append("Zonen-order muss lückenlos von 1 bis 9 laufen.")

    validation = _require_mapping(data.get("validation"), "validation", errors)
    if validation.get("requiredZoneCount") != 9:
        errors.append("validation.requiredZoneCount muss 9 sein.")
    if validation.get("requiredZoneOrder") != list(EXPECTED_ZONE_IDS):
        errors.append("validation.requiredZoneOrder stimmt nicht mit dem Zonenvertrag überein.")

    policy = _require_mapping(data.get("iterationPolicy"), "iterationPolicy", errors)
    required_policy = {
        "githubRepositoryMustBeUpdated": True,
        "targetBranch": "main",
        "completionRequiresCommitSha": True,
        "completionRequiresValidationReport": True,
        "localOnlyCompletionAllowed": False,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            errors.append(f"iterationPolicy.{key} muss {expected!r} sein.")

    preservation = _require_mapping(
        data.get("preservationPolicy"), "preservationPolicy", errors
    )
    if preservation.get("explicitUserApprovalRequiredForStructuralDeviation") is not True:
        errors.append(
            "Strukturelle Layoutabweichungen müssen eine ausdrückliche Nutzerfreigabe verlangen."
        )

    if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        warnings.append(
            f"Unbekannte schemaVersion; Validator wurde für {EXPECTED_SCHEMA_VERSION} entwickelt."
        )

    return ValidationResult(tuple(errors), tuple(warnings), data)


def format_validation_result(result: ValidationResult) -> str:
    """Erzeugt eine verständliche Mehrzeilenausgabe für Konsole und Dialog."""

    lines = [result.summary()]
    lines.extend(f"FEHLER: {item}" for item in result.errors)
    lines.extend(f"WARNUNG: {item}" for item in result.warnings)
    return "\n".join(lines)
