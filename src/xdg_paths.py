"""Sichere XDG-Pfadverwaltung für MULTIMODULTOOL2026 unter Linux."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import stat
import tempfile
from typing import Mapping


APP_ID = "multimodultool2026"
DIRECTORY_MODE = 0o700


@dataclass(frozen=True)
class XDGPaths:
    """Alle vom Programm verwendeten Linux-Benutzerpfade."""

    config: Path
    data: Path
    cache: Path
    state: Path
    logs: Path
    backups: Path

    def items(self) -> tuple[tuple[str, Path], ...]:
        return (
            ("Konfiguration", self.config),
            ("Nutzerdaten", self.data),
            ("Cache", self.cache),
            ("Status", self.state),
            ("Protokolle", self.logs),
            ("Sicherungen", self.backups),
        )


@dataclass
class PathValidationResult:
    """Ergebnis der XDG-Vor- oder Nachvalidierung."""

    paths: XDGPaths | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created: list[Path] = field(default_factory=list)
    checked: list[Path] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors and self.paths is not None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _absolute_base(
    env_name: str,
    fallback: Path,
    environment: Mapping[str, str],
    errors: list[str],
) -> Path:
    raw = environment.get(env_name)
    candidate = Path(raw).expanduser() if raw else fallback
    if not candidate.is_absolute():
        errors.append(
            f"{env_name} muss ein absoluter Linux-Pfad sein; erhalten: {candidate}"
        )
    return candidate


def resolve_xdg_paths(
    *,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    app_id: str = APP_ID,
) -> PathValidationResult:
    """XDG-Ziele berechnen, ohne Verzeichnisse anzulegen."""

    env = dict(os.environ if environment is None else environment)
    errors: list[str] = []
    user_home = (home or Path.home()).expanduser()
    if not user_home.is_absolute():
        errors.append(f"Benutzerverzeichnis ist nicht absolut: {user_home}")

    config_base = _absolute_base(
        "XDG_CONFIG_HOME", user_home / ".config", env, errors
    )
    data_base = _absolute_base(
        "XDG_DATA_HOME", user_home / ".local" / "share", env, errors
    )
    cache_base = _absolute_base(
        "XDG_CACHE_HOME", user_home / ".cache", env, errors
    )
    state_base = _absolute_base(
        "XDG_STATE_HOME", user_home / ".local" / "state", env, errors
    )

    paths = XDGPaths(
        config=config_base / app_id,
        data=data_base / app_id,
        cache=cache_base / app_id,
        state=state_base / app_id,
        logs=state_base / app_id / "logs",
        backups=data_base / app_id / "backups",
    )
    return PathValidationResult(paths=paths, errors=errors)


def _target_boundaries(paths: XDGPaths) -> tuple[tuple[str, Path, Path], ...]:
    return (
        ("Konfiguration", paths.config, paths.config.parent),
        ("Nutzerdaten", paths.data, paths.data.parent),
        ("Cache", paths.cache, paths.cache.parent),
        ("Status", paths.state, paths.state.parent),
        ("Protokolle", paths.logs, paths.state),
        ("Sicherungen", paths.backups, paths.data),
    )


def _existing_component_is_symlink(target: Path, boundary: Path) -> Path | None:
    """Ersten Symlink innerhalb des App-spezifischen Bereichs liefern."""

    current = target
    chain: list[Path] = []
    while current != boundary and current.parent != current:
        chain.append(current)
        current = current.parent

    for candidate in reversed(chain):
        try:
            if candidate.is_symlink():
                return candidate
        except OSError:
            return candidate
    return None


def validate_xdg_paths(
    paths: XDGPaths,
    *,
    project_root: Path,
    require_existing: bool = False,
    require_writable: bool = False,
) -> PathValidationResult:
    """Pfadgrenzen, Symlinks, Typen, Rechte und Quellbaumtrennung prüfen."""

    result = PathValidationResult(paths=paths)
    project = project_root.expanduser().resolve(strict=False)
    seen: set[Path] = set()

    for label, target, boundary in _target_boundaries(paths):
        target_abs = target.expanduser()
        boundary_abs = boundary.expanduser()
        if not target_abs.is_absolute():
            result.errors.append(f"{label}: Ziel ist nicht absolut: {target_abs}")
            continue

        resolved_boundary = boundary_abs.resolve(strict=False)
        resolved_target = target_abs.resolve(strict=False)
        if not _is_relative_to(resolved_target, resolved_boundary):
            result.errors.append(
                f"{label}: Ziel verlässt die erlaubte XDG-Grenze: {target_abs}"
            )
        if _is_relative_to(resolved_target, project):
            result.errors.append(
                f"{label}: Ziel liegt unzulässig im Programmverzeichnis: {target_abs}"
            )

        symlink = _existing_component_is_symlink(target_abs, boundary_abs)
        if symlink is not None:
            result.errors.append(
                f"{label}: Symbolischer Link im App-Pfad blockiert: {symlink}"
            )

        try:
            exists = target_abs.exists()
        except OSError as exc:
            result.errors.append(f"{label}: Pfad kann nicht geprüft werden: {exc}")
            continue

        if require_existing and not exists:
            result.errors.append(f"{label}: Verzeichnis fehlt nach der Anlage: {target_abs}")
        if exists:
            try:
                mode = target_abs.lstat().st_mode
            except OSError as exc:
                result.errors.append(f"{label}: Metadaten nicht lesbar: {exc}")
                continue
            if stat.S_ISLNK(mode):
                result.errors.append(f"{label}: Ziel darf kein Symlink sein: {target_abs}")
            elif not stat.S_ISDIR(mode):
                result.errors.append(f"{label}: Ziel ist kein Verzeichnis: {target_abs}")
            else:
                result.checked.append(target_abs)
                if require_writable and not os.access(
                    target_abs, os.W_OK | os.X_OK
                ):
                    result.errors.append(
                        f"{label}: Verzeichnis ist nicht beschreibbar: {target_abs}"
                    )

        if resolved_target in seen and label not in {"Protokolle", "Sicherungen"}:
            result.errors.append(f"{label}: XDG-Ziel ist doppelt belegt: {target_abs}")
        seen.add(resolved_target)

    return result


def _write_probe(path: Path) -> None:
    descriptor, probe_name = tempfile.mkstemp(prefix=".mmtool-write-test-", dir=path)
    probe = Path(probe_name)
    try:
        os.write(descriptor, b"ok")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
        probe.unlink(missing_ok=True)


def ensure_xdg_paths(
    paths: XDGPaths,
    *,
    project_root: Path,
) -> PathValidationResult:
    """XDG-Verzeichnisse sicher anlegen und anschließend erneut validieren."""

    preflight = validate_xdg_paths(paths, project_root=project_root)
    if not preflight.is_valid:
        return preflight

    result = PathValidationResult(paths=paths)
    ordered = sorted((path for _, path in paths.items()), key=lambda item: len(item.parts))
    for target in ordered:
        existed = target.exists()
        try:
            target.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
            if target.is_symlink():
                result.errors.append(f"Symlink nach Anlage erkannt: {target}")
                continue
            os.chmod(target, DIRECTORY_MODE)
            if not existed:
                result.created.append(target)
        except OSError as exc:
            result.errors.append(
                f"Verzeichnis konnte nicht sicher angelegt werden: {target}: {exc}"
            )

    if result.errors:
        return result

    postflight = validate_xdg_paths(
        paths,
        project_root=project_root,
        require_existing=True,
        require_writable=True,
    )
    result.errors.extend(postflight.errors)
    result.warnings.extend(postflight.warnings)
    result.checked.extend(postflight.checked)
    if result.errors:
        return result

    for label, target in paths.items():
        try:
            _write_probe(target)
        except OSError as exc:
            result.errors.append(
                f"{label}: Schreibprüfung fehlgeschlagen; Testdatei wurde entfernt: {exc}"
            )
    return result


def format_path_report(
    result: PathValidationResult,
    *,
    include_paths: bool = True,
    prepared: bool = True,
) -> str:
    """Laiengerechten Ampelbericht erzeugen."""

    if result.paths is None:
        return "ROT: XDG-Pfade konnten nicht berechnet werden."
    success_text = (
        "GRÜN: XDG-Pfade sind getrennt, beschreibbar und sicher vorbereitet."
        if prepared
        else "GRÜN: XDG-Pfadplan ist getrennt und innerhalb sicherer Grenzen."
    )
    lines = [
        success_text if result.is_valid else "ROT: XDG-Pfadprüfung blockiert den Start."
    ]
    if include_paths:
        lines.extend(f"- {label}: {path}" for label, path in result.paths.items())
    lines.extend(f"- GELB: {warning}" for warning in result.warnings)
    lines.extend(f"- ROT: {error}" for error in result.errors)
    if result.created:
        lines.append(f"- Neu angelegte Verzeichnisse: {len(result.created)}")
    return "\n".join(lines)
