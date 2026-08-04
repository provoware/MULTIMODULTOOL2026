"""Versionierte, transaktionale Einstellungen für MULTIMODULTOOL2026."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Callable, Mapping

SCHEMA_VERSION = 1
SETTINGS_FILE_NAME = "settings.json"
BACKUP_FILE_NAME = "settings.last-valid.json"
FILE_MODE = 0o600

FAILPOINT_NAMES = (
    "before_temp_write",
    "after_temp_write",
    "before_fsync",
    "after_fsync",
    "before_backup",
    "after_backup",
    "before_replace",
    "after_replace",
    "before_postvalidate",
    "after_postvalidate",
)
FailpointHook = Callable[[str], None]

DEFAULT_SETTINGS: dict[str, Any] = {
    "schemaVersion": SCHEMA_VERSION,
    "ui": {"theme": "dark", "fontScalePercent": 100, "showTooltips": True},
    "safety": {"defaultDryRun": True, "confirmDestructiveActions": True},
    "workflow": {"startArea": "start", "showAdvancedOptions": False},
}

_ALLOWED_ROOT_KEYS = frozenset(DEFAULT_SETTINGS)
_ALLOWED_UI_KEYS = frozenset(DEFAULT_SETTINGS["ui"])
_ALLOWED_SAFETY_KEYS = frozenset(DEFAULT_SETTINGS["safety"])
_ALLOWED_WORKFLOW_KEYS = frozenset(DEFAULT_SETTINGS["workflow"])


class InjectedFailpoint(RuntimeError):
    def __init__(self, name: str) -> None:
        super().__init__(f"simulierter Failpoint: {name}")
        self.name = name


class FailpointController:
    def __init__(self, active_name: str) -> None:
        if active_name not in FAILPOINT_NAMES:
            raise ValueError(f"Unbekannter Failpoint: {active_name}")
        self.active_name = active_name
        self.hits: list[str] = []

    def __call__(self, name: str) -> None:
        self.hits.append(name)
        if name == self.active_name:
            raise InjectedFailpoint(name)


@dataclass(frozen=True)
class SettingsPaths:
    directory: Path
    active: Path
    backup: Path


@dataclass
class SettingsValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    data: dict[str, Any] | None = None


@dataclass
class SettingsLoadResult:
    settings: dict[str, Any]
    source: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recovered: bool = False
    created: bool = False
    quarantined: Path | None = None
    failpoint: str | None = None

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _hit(failpoint: FailpointHook | None, name: str) -> None:
    if failpoint is not None:
        failpoint(name)


def default_settings() -> dict[str, Any]:
    return deepcopy(DEFAULT_SETTINGS)


def settings_paths(config_directory: Path) -> SettingsPaths:
    directory = config_directory.expanduser()
    return SettingsPaths(directory, directory / SETTINGS_FILE_NAME, directory / BACKUP_FILE_NAME)


def _reject_unknown_keys(value: Mapping[str, Any], allowed: frozenset[str], label: str, errors: list[str]) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"{label}: unbekannte Felder: {', '.join(unknown)}")


def _require_object(value: Any, label: str, errors: list[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} muss ein JSON-Objekt sein.")
        return {}
    return value


def _require_bool(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, bool):
        errors.append(f"{label} muss true oder false sein.")


def validate_settings(value: Any) -> SettingsValidationResult:
    errors: list[str] = []
    root = _require_object(value, "Wurzelelement", errors)
    if root:
        _reject_unknown_keys(root, _ALLOWED_ROOT_KEYS, "Wurzelelement", errors)
    version = root.get("schemaVersion")
    if not isinstance(version, int) or isinstance(version, bool):
        errors.append("schemaVersion muss eine Ganzzahl sein.")
    elif version != SCHEMA_VERSION:
        errors.append(f"schemaVersion {version!r} wird nicht unterstützt; erwartet wird {SCHEMA_VERSION}.")
    ui = _require_object(root.get("ui"), "ui", errors)
    if ui:
        _reject_unknown_keys(ui, _ALLOWED_UI_KEYS, "ui", errors)
    if ui.get("theme") != "dark":
        errors.append("ui.theme muss im aktuellen Entwicklungsstand 'dark' sein.")
    scale = ui.get("fontScalePercent")
    if not isinstance(scale, int) or isinstance(scale, bool):
        errors.append("ui.fontScalePercent muss eine Ganzzahl sein.")
    elif not 80 <= scale <= 200:
        errors.append("ui.fontScalePercent muss zwischen 80 und 200 liegen.")
    _require_bool(ui.get("showTooltips"), "ui.showTooltips", errors)
    safety = _require_object(root.get("safety"), "safety", errors)
    if safety:
        _reject_unknown_keys(safety, _ALLOWED_SAFETY_KEYS, "safety", errors)
    _require_bool(safety.get("defaultDryRun"), "safety.defaultDryRun", errors)
    if safety.get("defaultDryRun") is not True:
        errors.append("safety.defaultDryRun muss im aktuellen Entwicklungsstand true bleiben.")
    _require_bool(safety.get("confirmDestructiveActions"), "safety.confirmDestructiveActions", errors)
    if safety.get("confirmDestructiveActions") is not True:
        errors.append("safety.confirmDestructiveActions muss im aktuellen Entwicklungsstand true bleiben.")
    workflow = _require_object(root.get("workflow"), "workflow", errors)
    if workflow:
        _reject_unknown_keys(workflow, _ALLOWED_WORKFLOW_KEYS, "workflow", errors)
    if workflow.get("startArea") not in {"start", "analyze", "organize", "reports"}:
        errors.append("workflow.startArea muss 'start', 'analyze', 'organize' oder 'reports' sein.")
    _require_bool(workflow.get("showAdvancedOptions"), "workflow.showAdvancedOptions", errors)
    normalized = deepcopy(dict(root)) if not errors else None
    return SettingsValidationResult(not errors, errors, normalized)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_settings_paths(paths: SettingsPaths) -> list[str]:
    errors: list[str] = []
    directory = paths.directory.expanduser()
    if not directory.is_absolute():
        return [f"Konfigurationsverzeichnis ist nicht absolut: {directory}"]
    if directory.is_symlink():
        return [f"Konfigurationsverzeichnis darf kein Symlink sein: {directory}"]
    if directory.exists() and not directory.is_dir():
        return [f"Konfigurationsziel ist kein Verzeichnis: {directory}"]
    resolved_directory = directory.resolve(strict=False)
    for label, path in (("Einstellungen", paths.active), ("Sicherung", paths.backup)):
        candidate = path.expanduser()
        if not candidate.is_absolute():
            errors.append(f"{label}: Dateipfad ist nicht absolut: {candidate}")
            continue
        if not _is_within(candidate.resolve(strict=False), resolved_directory):
            errors.append(f"{label}: Dateipfad verlässt das Konfigurationsverzeichnis.")
        if candidate.is_symlink():
            errors.append(f"{label}: Symbolischer Link ist nicht zulässig: {candidate}")
        if candidate.exists():
            try:
                mode = candidate.lstat().st_mode
            except OSError as exc:
                errors.append(f"{label}: Metadaten nicht lesbar: {exc}")
                continue
            if not stat.S_ISREG(mode):
                errors.append(f"{label}: Ziel ist keine reguläre Datei: {candidate}")
            elif stat.S_IMODE(mode) & 0o077:
                errors.append(f"{label}: Dateirechte sind zu offen; erforderlich ist 0600: {candidate}")
    return errors


def _read_json_file(path: Path) -> SettingsValidationResult:
    if path.is_symlink():
        return SettingsValidationResult(False, [f"Symbolischer Link ist nicht zulässig: {path}"])
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return SettingsValidationResult(False, [f"Datei fehlt: {path.name}"])
    except (OSError, UnicodeError) as exc:
        return SettingsValidationResult(False, [f"{path.name} ist nicht lesbar: {exc}"])
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return SettingsValidationResult(False, [f"{path.name}: ungültiges JSON in Zeile {exc.lineno}: {exc.msg}"])
    return validate_settings(parsed)


def read_settings(config_directory: Path) -> SettingsValidationResult:
    paths = settings_paths(config_directory)
    errors = validate_settings_paths(paths)
    return SettingsValidationResult(False, errors) if errors else _read_json_file(paths.active)


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_json_temp(directory: Path, prefix: str, data: Mapping[str, Any], *, failpoint: FailpointHook | None = None, apply_transaction_failpoints: bool = False) -> Path:
    if apply_transaction_failpoints:
        _hit(failpoint, "before_temp_write")
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=directory)
    path = Path(name)
    try:
        os.fchmod(descriptor, FILE_MODE)
        payload = (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("Temporäre Einstellungsdatei konnte nicht vollständig geschrieben werden.")
            remaining = remaining[written:]
        if apply_transaction_failpoints:
            _hit(failpoint, "after_temp_write")
            _hit(failpoint, "before_fsync")
        os.fsync(descriptor)
        if apply_transaction_failpoints:
            _hit(failpoint, "after_fsync")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally:
        os.close(descriptor)
    return path


def _replace_from_data(destination: Path, data: Mapping[str, Any], *, failpoint: FailpointHook | None = None, apply_transaction_failpoints: bool = False) -> None:
    temporary = _write_json_temp(destination.parent, f".{destination.name}.", data, failpoint=failpoint, apply_transaction_failpoints=apply_transaction_failpoints)
    try:
        validation = _read_json_file(temporary)
        if not validation.is_valid:
            raise ValueError("Temporäre Einstellungsdatei ist ungültig: " + "; ".join(validation.errors))
        if apply_transaction_failpoints:
            _hit(failpoint, "before_replace")
        os.replace(temporary, destination)
        os.chmod(destination, FILE_MODE)
        _fsync_directory(destination.parent)
        if apply_transaction_failpoints:
            _hit(failpoint, "after_replace")
    finally:
        temporary.unlink(missing_ok=True)


def write_settings(config_directory: Path, data: Mapping[str, Any], *, failpoint: FailpointHook | None = None) -> SettingsLoadResult:
    validation = validate_settings(data)
    if not validation.is_valid or validation.data is None:
        return SettingsLoadResult(default_settings(), "blocked", errors=validation.errors)
    paths = settings_paths(config_directory)
    errors = validate_settings_paths(paths)
    if errors:
        return SettingsLoadResult(default_settings(), "blocked", errors=errors)
    try:
        paths.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if paths.directory.is_symlink() or not paths.directory.is_dir():
            raise OSError("Konfigurationsziel ist kein sicheres Verzeichnis.")
        os.chmod(paths.directory, 0o700)
    except OSError as exc:
        return SettingsLoadResult(default_settings(), "blocked", errors=[f"Konfigurationsverzeichnis kann nicht vorbereitet werden: {exc}"])
    errors = validate_settings_paths(paths)
    if errors:
        return SettingsLoadResult(default_settings(), "blocked", errors=errors)
    current = _read_json_file(paths.active) if paths.active.exists() else None
    try:
        if current is not None and current.is_valid and current.data is not None:
            _hit(failpoint, "before_backup")
            _replace_from_data(paths.backup, current.data)
            _hit(failpoint, "after_backup")
        _replace_from_data(paths.active, validation.data, failpoint=failpoint, apply_transaction_failpoints=True)
        _hit(failpoint, "before_postvalidate")
        post = _read_json_file(paths.active)
        _hit(failpoint, "after_postvalidate")
        if not post.is_valid or post.data is None:
            if paths.backup.exists():
                backup = _read_json_file(paths.backup)
                if backup.is_valid and backup.data is not None:
                    _replace_from_data(paths.active, backup.data)
            else:
                paths.active.unlink(missing_ok=True)
                _fsync_directory(paths.directory)
            raise ValueError("Nachvalidierung der aktiven Einstellungen fehlgeschlagen; Rückfall wurde ausgeführt.")
    except (OSError, ValueError, InjectedFailpoint) as exc:
        return SettingsLoadResult(default_settings(), "blocked", errors=[f"Transaktionales Speichern fehlgeschlagen: {exc}"], failpoint=exc.name if isinstance(exc, InjectedFailpoint) else None)
    return SettingsLoadResult(validation.data, "active", created=current is None)


def _quarantine_corrupt_file(path: Path) -> Path | None:
    if not path.exists() or path.is_symlink():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    quarantine = path.with_name(f"{path.stem}.corrupt-{stamp}{path.suffix}")
    try:
        os.replace(path, quarantine)
        _fsync_directory(path.parent)
        return quarantine
    except OSError:
        return None


def inspect_settings(config_directory: Path) -> SettingsLoadResult:
    paths = settings_paths(config_directory)
    errors = validate_settings_paths(paths)
    if errors:
        return SettingsLoadResult(default_settings(), "blocked", errors=errors)
    if not paths.active.exists():
        return SettingsLoadResult(default_settings(), "defaults-preview", warnings=["Noch keine Einstellungsdatei vorhanden; beim normalen Start werden sichere Standardwerte atomar angelegt."])
    active = _read_json_file(paths.active)
    if active.is_valid and active.data is not None:
        return SettingsLoadResult(active.data, "active")
    warnings = list(active.errors)
    backup = _read_json_file(paths.backup) if paths.backup.exists() else None
    if backup is not None and backup.is_valid and backup.data is not None:
        return SettingsLoadResult(backup.data, "backup-preview", warnings=warnings + ["Die aktive Datei ist beschädigt; beim normalen Start würde die letzte gültige Sicherung wiederhergestellt."], recovered=True)
    if backup is not None:
        warnings.extend(backup.errors)
    warnings.append("Keine gültige Sicherung vorhanden; beim normalen Start würden sichere Standardwerte wiederhergestellt.")
    return SettingsLoadResult(default_settings(), "defaults-preview", warnings=warnings, recovered=True)


def load_or_recover_settings(config_directory: Path) -> SettingsLoadResult:
    paths = settings_paths(config_directory)
    errors = validate_settings_paths(paths)
    if errors:
        return SettingsLoadResult(default_settings(), "blocked", errors=errors)
    if not paths.active.exists():
        created = write_settings(paths.directory, default_settings())
        if created.is_valid:
            created.source = "defaults"
            created.created = True
        return created
    active = _read_json_file(paths.active)
    if active.is_valid and active.data is not None:
        return SettingsLoadResult(active.data, "active")
    active_errors = list(active.errors)
    quarantine = _quarantine_corrupt_file(paths.active)
    backup = _read_json_file(paths.backup) if paths.backup.exists() else None
    if backup is not None and backup.is_valid and backup.data is not None:
        try:
            _replace_from_data(paths.active, backup.data)
        except (OSError, ValueError) as exc:
            return SettingsLoadResult(default_settings(), "blocked", errors=active_errors + [f"Rollback aus Sicherung fehlgeschlagen: {exc}"], quarantined=quarantine)
        return SettingsLoadResult(backup.data, "backup", warnings=active_errors, recovered=True, quarantined=quarantine)
    fallback = write_settings(paths.directory, default_settings())
    if fallback.is_valid:
        fallback.source = "defaults"
        fallback.recovered = True
        fallback.warnings.extend(active_errors)
        if backup is not None:
            fallback.warnings.extend(backup.errors)
        fallback.quarantined = quarantine
    return fallback


def format_settings_report(result: SettingsLoadResult) -> str:
    if not result.is_valid:
        lines = ["ROT: Einstellungen konnten nicht sicher geladen werden."]
    elif result.recovered:
        lines = ["GELB: Einstellungen wurden automatisch sicher wiederhergestellt."]
    elif result.created:
        lines = ["GRÜN: Sichere Standardeinstellungen wurden erstmals angelegt."]
    else:
        lines = ["GRÜN: Versionierte Einstellungen sind gültig."]
    source_labels = {"active": "aktive Datei", "backup": "letzte gültige Sicherung", "defaults": "sichere Standardwerte", "defaults-preview": "sichere Standardwerte (nur Prüfung)", "backup-preview": "letzte gültige Sicherung (nur Prüfung)", "blocked": "blockiert"}
    lines.append(f"- Quelle: {source_labels.get(result.source, result.source)}")
    if result.failpoint:
        lines.append(f"- Testunterbrechung: {result.failpoint}")
    lines.extend(f"- GELB: {warning}" for warning in result.warnings)
    lines.extend(f"- ROT: {error}" for error in result.errors)
    return "\n".join(lines)
