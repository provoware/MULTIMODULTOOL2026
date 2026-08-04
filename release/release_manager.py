#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

APP = "multimodultool2026"


def fail(message: str) -> None:
    raise SystemExit(f"ROT: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_root() -> Path:
    return Path(__file__).resolve().parent


def metadata() -> dict[str, object]:
    return json.loads((package_root() / "RELEASE-METADATA.json").read_text(encoding="utf-8"))


def verify_package() -> dict[str, object]:
    root = package_root()
    release = metadata()
    for record in release["files"]:
        path = root / record["path"]
        if path.is_symlink() or not path.is_file():
            fail(f"Paketdatei fehlt oder ist unsicher: {record['path']}")
        if path.stat().st_size != record["size"] or sha256(path) != record["sha256"]:
            fail(f"Paketdatei wurde verändert: {record['path']}")
    return release


def install_paths(root: Path) -> tuple[Path, Path, Path]:
    return (
        root / "opt" / APP,
        root / "usr/local/bin" / APP,
        root / "usr/share/applications" / f"{APP}.desktop",
    )


def require_dependencies() -> None:
    if sys.version_info < (3, 10):
        fail("Python 3.10 oder neuer ist erforderlich.")
    if shutil.which("bash") is None or shutil.which("sha256sum") is None:
        fail("Die Basisabhängigkeiten bash und sha256sum sind erforderlich.")
    probe = subprocess.run(
        [sys.executable, "-m", "venv", "--help"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        fail("Das Python-Modul venv ist erforderlich.")


def atomic_symlink(target: str, link: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.with_name(f".{link.name}.new")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, link)


def install(root: Path, *, upgrade: bool) -> None:
    require_dependencies()
    release = verify_package()
    base, launcher, desktop = install_paths(root)
    releases = base / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    os.chmod(base, 0o755)
    os.chmod(releases, 0o755)
    build_id = str(release["buildId"])
    final = releases / build_id
    if final.exists():
        installed_metadata = final / "RELEASE-METADATA.json"
        if not installed_metadata.is_file():
            fail("Ziel-Build existiert ohne gültige Metadaten.")
        installed = json.loads(installed_metadata.read_text(encoding="utf-8"))
        if installed.get("buildId") != build_id:
            fail("Ziel-Build besitzt eine widersprüchliche Build-ID.")
    else:
        temporary = Path(tempfile.mkdtemp(prefix=".install-", dir=releases))
        try:
            shutil.copytree(package_root() / "payload", temporary / "app", dirs_exist_ok=True)
            shutil.copy2(
                package_root() / "RELEASE-METADATA.json",
                temporary / "RELEASE-METADATA.json",
            )
            subprocess.run([sys.executable, "-m", "venv", str(temporary / "venv")], check=True)
            wheelhouse = package_root() / "wheelhouse"
            command = [
                str(temporary / "venv/bin/python"),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
            ]
            if wheelhouse.exists():
                command.extend(["--no-index", "--find-links", str(wheelhouse)])
            command.extend(["-r", str(temporary / "app/requirements.txt")])
            subprocess.run(command, check=True)
            os.replace(temporary, final)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
    current = base / "current"
    previous = base / "previous"
    old_target = os.readlink(current) if current.is_symlink() else None
    if upgrade and old_target and old_target != f"releases/{build_id}":
        atomic_symlink(old_target, previous)
    atomic_symlink(f"releases/{build_id}", current)
    launcher.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package_root() / "launcher.sh", launcher)
    os.chmod(launcher, 0o755)
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=MULTIMODULTOOL2026\n"
        "Exec=/usr/local/bin/multimodultool2026\n"
        "Terminal=false\n"
        "Categories=Utility;FileTools;\n",
        encoding="utf-8",
    )
    state = {
        "schemaVersion": 1,
        "currentBuildId": build_id,
        "previousBuildId": Path(old_target).name if old_target else None,
    }
    (base / "install-state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"GRÜN: {'Upgrade' if upgrade else 'Installation'} aktiv: {build_id}")


def rollback(root: Path) -> None:
    base, _, _ = install_paths(root)
    current = base / "current"
    previous = base / "previous"
    if not current.is_symlink() or not previous.is_symlink():
        fail("Kein vollständiger Rollback-Zustand vorhanden.")
    current_target = os.readlink(current)
    previous_target = os.readlink(previous)
    atomic_symlink(previous_target, current)
    atomic_symlink(current_target, previous)
    print(f"GRÜN: Rollback aktiv: {Path(previous_target).name}")


def uninstall(root: Path) -> None:
    base, launcher, desktop = install_paths(root)
    launcher.unlink(missing_ok=True)
    desktop.unlink(missing_ok=True)
    if base.exists():
        shutil.rmtree(base)
    print("GRÜN: Programm vollständig entfernt; persönliche XDG-Daten blieben erhalten.")


def first_start_check(root: Path) -> None:
    base, _, _ = install_paths(root)
    python = base / "current/venv/bin/python"
    app = base / "current/app"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(app)
    subprocess.run(
        [str(python), "-m", "src.main", "--validate-only"],
        cwd=app,
        env=environment,
        check=True,
    )
    print("GRÜN: Erster Start validiert.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("verify", "install", "upgrade", "rollback", "first-start-check", "uninstall"),
    )
    parser.add_argument("--root", type=Path, default=Path("/"))
    args = parser.parse_args()
    root = args.root.resolve()
    if root == Path("/") and os.geteuid() != 0 and args.command != "verify":
        fail("Eine Systeminstallation benötigt root-Rechte.")
    if args.command == "verify":
        verify_package()
        require_dependencies()
        print("GRÜN: Paket und Basisabhängigkeiten sind gültig.")
    elif args.command == "install":
        install(root, upgrade=False)
    elif args.command == "upgrade":
        install(root, upgrade=True)
    elif args.command == "rollback":
        rollback(root)
    elif args.command == "first-start-check":
        first_start_check(root)
    elif args.command == "uninstall":
        uninstall(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
