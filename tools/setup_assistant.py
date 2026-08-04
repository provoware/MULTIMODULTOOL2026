#!/usr/bin/env python3
"""Geführter Linux-Einrichtungsassistent für MULTIMODULTOOL2026."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Mapping, Sequence


MIN_PYTHON = (3, 10)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
VENV_PATH = PROJECT_ROOT / ".venv"


@dataclass(frozen=True)
class CheckResult:
    key: str
    label: str
    state: str
    detail: str
    blocking: bool = False


def state_prefix(state: str) -> str:
    return {"green": "GRÜN", "yellow": "GELB", "red": "ROT"}.get(state, state.upper())


def parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def is_debian_family(os_release: Mapping[str, str]) -> bool:
    values = f"{os_release.get('ID', '')} {os_release.get('ID_LIKE', '')}".lower()
    return any(name in values.split() for name in ("ubuntu", "debian"))


def detect_session(environ: Mapping[str, str]) -> tuple[str, str, bool]:
    desktop = (
        environ.get("XDG_CURRENT_DESKTOP")
        or environ.get("DESKTOP_SESSION")
        or environ.get("GDMSESSION")
        or "unbekannt"
    )
    session_type = environ.get("XDG_SESSION_TYPE", "unbekannt").lower()
    is_kde = any(marker in desktop.lower() for marker in ("kde", "plasma"))
    return desktop, session_type, is_kde


def has_display(environ: Mapping[str, str]) -> bool:
    return bool(environ.get("DISPLAY") or environ.get("WAYLAND_DISPLAY"))


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=False,
    )


def python_version_ok(version_info: Sequence[int] | None = None) -> bool:
    version = tuple(version_info or sys.version_info[:3])
    return version >= MIN_PYTHON


def check_project_writable(project_root: Path) -> tuple[bool, str]:
    if not project_root.is_dir():
        return False, "Projektordner existiert nicht."
    probe_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".setup-write-test-",
            dir=project_root,
            delete=False,
        ) as handle:
            handle.write(b"ok")
            probe_path = Path(handle.name)
        probe_path.unlink()
        return True, "Temporäre Schreibprobe erfolgreich und wieder entfernt."
    except OSError as exc:
        if probe_path is not None:
            try:
                probe_path.unlink(missing_ok=True)
            except OSError:
                pass
        return False, f"Schreibprobe fehlgeschlagen: {exc}"


def venv_python(venv_path: Path = VENV_PATH) -> Path:
    return venv_path / "bin" / "python"


def can_import_module(python_executable: Path | str, module: str) -> bool:
    process = run_command(
        [str(python_executable), "-c", f"import {module}"],
        capture=True,
    )
    return process.returncode == 0


def venv_module_available(python_executable: Path | str = sys.executable) -> bool:
    process = run_command(
        [str(python_executable), "-c", "import venv"],
        capture=True,
    )
    return process.returncode == 0


def collect_checks(
    project_root: Path = PROJECT_ROOT,
    environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    python_executable: Path | str = sys.executable,
) -> list[CheckResult]:
    env = environ or os.environ
    system_name = (platform_name or sys.platform).lower()
    desktop, session_type, is_kde = detect_session(env)
    checks: list[CheckResult] = []

    linux_ok = system_name.startswith("linux")
    checks.append(
        CheckResult(
            "platform",
            "Betriebssystem",
            "green" if linux_ok else "red",
            f"{platform.system()} / {system_name}" if linux_ok else f"Nicht unterstützt: {system_name}",
            blocking=not linux_ok,
        )
    )

    checks.append(
        CheckResult(
            "python",
            "Python",
            "green" if python_version_ok() else "red",
            platform.python_version(),
            blocking=not python_version_ok(),
        )
    )

    venv_ok = venv_module_available(python_executable)
    checks.append(
        CheckResult(
            "venv-module",
            "Python-venv",
            "green" if venv_ok else "red",
            "Modul verfügbar" if venv_ok else "python3-venv fehlt",
            blocking=False,
        )
    )

    writable, write_detail = check_project_writable(project_root)
    checks.append(
        CheckResult(
            "write-access",
            "Schreibrecht Projektordner",
            "green" if writable else "red",
            write_detail,
            blocking=not writable,
        )
    )

    session_supported = session_type in {"x11", "wayland"}
    session_state = "green" if is_kde and session_supported else "yellow"
    checks.append(
        CheckResult(
            "session",
            "Desktop-Sitzung",
            session_state,
            f"{desktop} / {session_type}",
            blocking=False,
        )
    )

    local_python = venv_python(project_root / ".venv")
    local_python_ok = local_python.is_file() and os.access(local_python, os.X_OK)
    checks.append(
        CheckResult(
            "local-venv",
            "Lokale Python-Umgebung",
            "green" if local_python_ok else "yellow",
            str(local_python) if local_python_ok else ".venv ist noch nicht einsatzbereit",
            blocking=False,
        )
    )

    pyside_ok = local_python_ok and can_import_module(local_python, "PySide6")
    checks.append(
        CheckResult(
            "pyside6",
            "PySide6",
            "green" if pyside_ok else "yellow",
            "Import erfolgreich" if pyside_ok else "noch nicht in .venv installiert",
            blocking=False,
        )
    )
    return checks


def print_report(checks: Sequence[CheckResult]) -> None:
    print("\nMULTIMODULTOOL2026 – Linux-Einrichtungsprüfung")
    print("=" * 56)
    for check in checks:
        print(f"{state_prefix(check.state)}: {check.label} – {check.detail}")


def blocking_errors(checks: Sequence[CheckResult]) -> list[CheckResult]:
    return [check for check in checks if check.blocking and check.state == "red"]


def environment_ready(checks: Sequence[CheckResult]) -> bool:
    states = {check.key: check.state for check in checks}
    return states.get("local-venv") == "green" and states.get("pyside6") == "green"


def confirm(
    title: str,
    message: str,
    *,
    assume_yes: bool = False,
    use_gui: bool = True,
    environ: Mapping[str, str] | None = None,
    input_function: Callable[[str], str] = input,
) -> bool:
    if assume_yes:
        return True

    env = environ or os.environ
    if use_gui and has_display(env) and command_exists("kdialog"):
        result = run_command(["kdialog", "--title", title, "--yesno", message])
        return result.returncode == 0

    print(f"\n{title}\n{message}")
    answer = input_function("Fortfahren? [j/N]: ").strip().lower()
    return answer in {"j", "ja", "y", "yes"}


def install_system_venv_packages(
    *,
    assume_yes: bool,
    use_gui: bool,
    environ: Mapping[str, str],
) -> bool:
    os_release = parse_os_release()
    if not is_debian_family(os_release) or not command_exists("apt-get"):
        print(
            "ROT: python3-venv fehlt und kann auf dieser Distribution nicht automatisch "
            "eingerichtet werden.\nInstalliere das passende venv- und pip-Paket deiner Distribution."
        )
        return False

    message = (
        "Für die lokale Python-Umgebung fehlen Systempakete.\n\n"
        "Ausgeführt werden:\n"
        "sudo apt-get update\n"
        "sudo apt-get install -y python3-venv python3-pip\n\n"
        "Es werden ausschließlich diese Linux-Systempakete installiert."
    )
    if not confirm(
        "Systempakete einrichten",
        message,
        assume_yes=assume_yes,
        use_gui=use_gui,
        environ=environ,
    ):
        print("GELB: Systempaket-Einrichtung abgebrochen. Es wurden keine Projektdateien geändert.")
        return False

    for command in (
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "python3-venv", "python3-pip"],
    ):
        print("+", " ".join(command))
        if run_command(command).returncode != 0:
            print("ROT: Systempaket-Einrichtung fehlgeschlagen.")
            return False
    return venv_module_available(sys.executable)


def validate_setup_target(project_root: Path) -> tuple[bool, str]:
    venv_path = project_root / ".venv"
    requirements = project_root / "requirements.txt"
    if project_root.resolve() != PROJECT_ROOT.resolve():
        return False, "Abweichender Projektordner ist aus Sicherheitsgründen nicht zugelassen."
    if venv_path.is_symlink():
        return False, ".venv ist ein symbolischer Link. Einrichtung wird blockiert."
    if not requirements.is_file():
        return False, "requirements.txt fehlt."
    try:
        requirements.resolve().relative_to(project_root.resolve())
    except ValueError:
        return False, "requirements.txt liegt außerhalb des Projekts."
    return True, "Zielpfade geprüft."


def create_atomic_environment(project_root: Path = PROJECT_ROOT) -> tuple[bool, str]:
    valid, detail = validate_setup_target(project_root)
    if not valid:
        return False, detail

    existing = project_root / ".venv"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    temporary = project_root / f".venv.setup-{os.getpid()}-{stamp}"
    backup = project_root / f".venv.backup-{os.getpid()}-{stamp}"

    for path in (temporary, backup):
        if path.exists() or path.is_symlink():
            return False, f"Temporärer Sicherheitspfad existiert bereits: {path.name}"

    try:
        print(f"+ {sys.executable} -m venv {temporary.name}")
        process = run_command([sys.executable, "-m", "venv", str(temporary)], cwd=project_root)
        if process.returncode != 0:
            return False, "Virtuelle Umgebung konnte nicht erstellt werden."

        temp_python = venv_python(temporary)
        commands = (
            [str(temp_python), "-m", "pip", "install", "--upgrade", "pip"],
            [
                str(temp_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--prefer-binary",
                "-r",
                str(project_root / "requirements.txt"),
            ],
        )
        for command in commands:
            print("+", " ".join(command))
            if run_command(command, cwd=project_root).returncode != 0:
                return False, "Abhängigkeiten konnten nicht vollständig installiert werden."

        if not can_import_module(temp_python, "PySide6"):
            return False, "PySide6-Importprüfung in der neuen Umgebung fehlgeschlagen."

        if existing.exists():
            existing.rename(backup)
        try:
            temporary.rename(existing)
        except OSError:
            if backup.exists() and not existing.exists():
                backup.rename(existing)
            raise

        if backup.exists():
            shutil.rmtree(backup)
        return True, "Lokale .venv atomar erstellt und PySide6 geprüft."
    except OSError as exc:
        return False, f"Dateisystemfehler während der Einrichtung: {exc}"
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Linux-Einrichtung für MULTIMODULTOOL2026 prüfen oder ausführen"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Nur prüfen, keinerlei Pakete oder Umgebungen einrichten.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bestätigungen für ausdrücklich angeforderte, kontrollierte Einrichtung annehmen.",
    )
    parser.add_argument(
        "--no-gui-dialogs",
        action="store_true",
        help="KDialog nicht verwenden; Bestätigungen im Terminal anzeigen.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    environ = os.environ
    checks = collect_checks()
    print_report(checks)

    failures = blocking_errors(checks)
    if failures:
        print("\nROT: Einrichtung blockiert. Es wurden keine dauerhaften Änderungen vorgenommen.")
        return 2

    if environment_ready(checks):
        print("\nGRÜN: Lokale Linux-Umgebung und PySide6 sind einsatzbereit.")
        return 0

    if args.check_only:
        print("\nGELB: Einrichtung ist unvollständig. Prüflauf hat nichts installiert.")
        return 3

    if not venv_module_available(sys.executable):
        if not install_system_venv_packages(
            assume_yes=args.yes,
            use_gui=not args.no_gui_dialogs,
            environ=environ,
        ):
            return 4

    setup_message = (
        "Eine neue lokale Python-Umgebung wird zuerst vollständig in einem temporären "
        "Ordner erstellt, geprüft und erst danach atomar als .venv aktiviert.\n\n"
        "Installiert wird ausschließlich requirements.txt. Eine bestehende .venv wird "
        "erst nach erfolgreicher Neuprüfung ersetzt."
    )
    if not confirm(
        "Projektumgebung einrichten",
        setup_message,
        assume_yes=args.yes,
        use_gui=not args.no_gui_dialogs,
        environ=environ,
    ):
        print("GELB: Projektumgebung nicht eingerichtet. Bestehende Daten bleiben unverändert.")
        return 5

    success, detail = create_atomic_environment()
    print(f"\n{state_prefix('green' if success else 'red')}: {detail}")
    if not success:
        return 6

    final_checks = collect_checks()
    print_report(final_checks)
    if not environment_ready(final_checks):
        print("\nROT: Nachprüfung fehlgeschlagen.")
        return 7

    print("\nGRÜN: Einrichtung vollständig. Starte anschließend mit ./start.sh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
