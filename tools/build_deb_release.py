#!/usr/bin/env python3
"""Reproducible amd64 Debian release builder for MULTIMODULTOOL2026."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "multimodultool2026"
ARCHITECTURE = "amd64"
INSTALL_ROOT = Path("usr/lib/multimodultool2026")
SOURCE_ALLOWLIST = ROOT / "release/package-files.txt"
DEFAULT_VERSION_FILE = ROOT / "release/VERSION"
REQUIRED_WHEEL_PREFIXES = (
    "PySide6-",
    "PySide6_Addons-",
    "PySide6_Essentials-",
    "shiboken6-",
)
BUILD_ID_PATTERN = re.compile(r"^MMTBUILD-[A-Za-z0-9._~+-]+-[a-f0-9]{16}$")


@dataclass(frozen=True)
class BuildResult:
    version: str
    build_id: str
    package_path: Path
    package_sha256: str
    bundle_path: Path
    bundle_sha256: str
    installed_manifest_sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "buildId": self.build_id,
            "package": str(self.package_path),
            "packageSha256": self.package_sha256,
            "bundle": str(self.bundle_path),
            "bundleSha256": self.bundle_sha256,
            "installedManifestSha256": self.installed_manifest_sha256,
        }


def fail(message: str) -> RuntimeError:
    return RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_date_epoch(value: str | None) -> int:
    if value:
        epoch = int(value)
    elif os.environ.get("SOURCE_DATE_EPOCH"):
        epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    else:
        epoch = 1_700_000_000
    if epoch < 315532800:
        raise fail("SOURCE_DATE_EPOCH must be 1980-01-01 or newer.")
    return epoch


def read_version(value: str | None) -> str:
    version = (value or DEFAULT_VERSION_FILE.read_text(encoding="utf-8")).strip()
    if not re.fullmatch(r"[0-9][0-9A-Za-z.+:~_-]*", version):
        raise fail(f"Invalid Debian version: {version!r}")
    return version


def expand_allowlist() -> tuple[Path, ...]:
    files: list[Path] = []
    seen: set[str] = set()
    for raw in SOURCE_ALLOWLIST.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise fail(f"Unsafe release allowlist entry: {value}")
        source = ROOT / relative
        if source.is_symlink():
            raise fail(f"Release source may not be a symlink: {value}")
        if source.is_file():
            candidates = (source,)
        elif source.is_dir():
            candidates = tuple(
                item
                for item in sorted(source.rglob("*"))
                if item.is_file() and not item.is_symlink() and "__pycache__" not in item.parts
            )
        else:
            raise fail(f"Release allowlist target missing: {value}")
        for candidate in candidates:
            rel = candidate.relative_to(ROOT).as_posix()
            if rel in seen:
                raise fail(f"Duplicate release source: {rel}")
            seen.add(rel)
            files.append(candidate)
    if not files:
        raise fail("Release allowlist is empty.")
    return tuple(sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()))


def validate_wheelhouse(path: Path) -> tuple[Path, ...]:
    if not path.is_dir() or path.is_symlink():
        raise fail(f"Wheelhouse is missing or unsafe: {path}")
    wheels = tuple(sorted(path.glob("*.whl"), key=lambda item: item.name))
    names = {wheel.name for wheel in wheels}
    for prefix in REQUIRED_WHEEL_PREFIXES:
        if not any(name.startswith(prefix) for name in names):
            raise fail(f"Wheelhouse misses required package prefix: {prefix}")
    for wheel in wheels:
        if wheel.is_symlink() or not wheel.is_file():
            raise fail(f"Unsafe wheelhouse entry: {wheel}")
    return wheels


def pyside_version(wheels: tuple[Path, ...]) -> str:
    candidates = [wheel.name for wheel in wheels if wheel.name.startswith("PySide6-")]
    if len(candidates) != 1:
        raise fail("Wheelhouse must contain exactly one PySide6 metapackage wheel.")
    match = re.match(r"PySide6-([0-9][0-9A-Za-z.]*)-", candidates[0])
    if not match:
        raise fail("Could not parse PySide6 wheel version.")
    return match.group(1)


def canonical_source_manifest(files: tuple[Path, ...], wheels: tuple[Path, ...], version: str) -> bytes:
    entries: list[dict[str, object]] = []
    for source in files:
        entries.append(
            {
                "path": source.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(source),
                "size": source.stat().st_size,
            }
        )
    for wheel in wheels:
        entries.append(
            {
                "path": f"wheelhouse/{wheel.name}",
                "sha256": sha256_file(wheel),
                "size": wheel.stat().st_size,
            }
        )
    payload = {"schemaVersion": 1, "version": version, "files": entries}
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def set_tree_metadata(root: Path, epoch: int) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink():
            raise fail(f"Staging tree contains symlink: {path}")
        mode = 0o755 if path.is_dir() else 0o644
        if path.is_file() and (
            path.as_posix().endswith("/usr/bin/multimodultool2026")
            or path.as_posix().endswith("/usr/sbin/multimodultool2026-release-manager")
            or "/DEBIAN/" in path.as_posix()
        ):
            mode = 0o755
        os.chmod(path, mode)
        os.utime(path, (epoch, epoch), follow_symlinks=False)
    os.chmod(root, 0o755)
    os.utime(root, (epoch, epoch), follow_symlinks=False)


def copy_runtime_files(stage: Path, files: tuple[Path, ...]) -> None:
    app_root = stage / INSTALL_ROOT / "app"
    for source in files:
        relative = source.relative_to(ROOT)
        target = app_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def copy_wheels(stage: Path, wheels: tuple[Path, ...]) -> None:
    target_root = stage / INSTALL_ROOT / "wheelhouse"
    target_root.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for wheel in wheels:
        target = target_root / wheel.name
        shutil.copyfile(wheel, target)
        lines.append(f"{sha256_file(target)}  {wheel.name}")
    (target_root / "WHEELHOUSE.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def installed_file_manifest(stage: Path) -> tuple[str, str]:
    entries: list[str] = []
    for path in sorted((stage / "usr").rglob("*")):
        if not path.is_file() or path.name == "FILE_MANIFEST.sha256":
            continue
        relative = path.relative_to(stage).as_posix()
        entries.append(f"{sha256_file(path)}  {relative}")
    text = "\n".join(entries) + "\n"
    manifest = stage / INSTALL_ROOT / "FILE_MANIFEST.sha256"
    manifest.write_text(text, encoding="utf-8")
    return text, sha256_bytes(text.encode("utf-8"))


def package_control(version: str, installed_size_kib: int) -> str:
    return f"""Package: {PACKAGE_NAME}
Version: {version}
Section: utils
Priority: optional
Architecture: {ARCHITECTURE}
Maintainer: provoware
Installed-Size: {installed_size_kib}
Depends: python3 (>= 3.10), python3-venv, python3-pip, util-linux, coreutils, libgl1, libegl1, libxkbcommon-x11-0, libxcb-cursor0, libdbus-1-3, libfontconfig1
Homepage: https://github.com/provoware/MULTIMODULTOOL2026
Description: Local safety-first Linux file organization desktop tool
 MULTIMODULTOOL2026 provides an offline-first PySide6 runtime, validated XDG
 storage, project trash, append-only undo/redo and transactional restart recovery.
"""


def maintainer_scripts() -> dict[str, str]:
    postinst = """#!/usr/bin/env bash
set -Eeuo pipefail
case "${1:-}" in
  configure)
    chmod 0755 /usr/bin/multimodultool2026 /usr/sbin/multimodultool2026-release-manager
    cd /
    sha256sum --quiet -c /usr/lib/multimodultool2026/FILE_MANIFEST.sha256
    python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)'
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database /usr/share/applications || true
    ;;
esac
exit 0
"""
    prerm = """#!/usr/bin/env bash
set -Eeuo pipefail
exit 0
"""
    postrm = """#!/usr/bin/env bash
set -Eeuo pipefail
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database /usr/share/applications || true
if [[ "${1:-}" == "purge" ]]; then
    rm -rf --one-file-system /var/lib/multimodultool2026
fi
exit 0
"""
    return {"postinst": postinst, "prerm": prerm, "postrm": postrm}


def build_stage(
    stage: Path,
    *,
    version: str,
    build_id: str,
    source_manifest: bytes,
    source_manifest_sha: str,
    files: tuple[Path, ...],
    wheels: tuple[Path, ...],
    epoch: int,
) -> tuple[str, str]:
    copy_runtime_files(stage, files)
    copy_wheels(stage, wheels)
    install_root = stage / INSTALL_ROOT
    install_root.mkdir(parents=True, exist_ok=True)
    pyside = pyside_version(wheels)
    (install_root / "requirements.lock").write_text(f"PySide6=={pyside}\n", encoding="utf-8")
    build_info = {
        "schemaVersion": 1,
        "package": PACKAGE_NAME,
        "version": version,
        "architecture": ARCHITECTURE,
        "buildId": build_id,
        "sourceManifestSha256": source_manifest_sha,
        "sourceDateEpoch": epoch,
        "builtUtc": datetime.fromtimestamp(epoch, timezone.utc).isoformat().replace("+00:00", "Z"),
        "pythonMinimum": "3.10",
        "pyside6": pyside,
    }
    (install_root / "BUILD_INFO.json").write_text(
        json.dumps(build_info, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (install_root / "SOURCE_MANIFEST.json").write_bytes(source_manifest)

    bin_dir = stage / "usr/bin"
    sbin_dir = stage / "usr/sbin"
    desktop_dir = stage / "usr/share/applications"
    bin_dir.mkdir(parents=True, exist_ok=True)
    sbin_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "release/multimodultool2026-launcher.sh", bin_dir / PACKAGE_NAME)
    shutil.copyfile(ROOT / "release/release-manager.sh", sbin_dir / f"{PACKAGE_NAME}-release-manager")
    shutil.copyfile(ROOT / "release/multimodultool2026.desktop", desktop_dir / f"{PACKAGE_NAME}.desktop")

    manifest_text, manifest_sha = installed_file_manifest(stage)
    installed_size = sum(path.stat().st_size for path in stage.rglob("*") if path.is_file()) // 1024 + 1
    debian = stage / "DEBIAN"
    debian.mkdir(parents=True, exist_ok=True)
    (debian / "control").write_text(package_control(version, installed_size), encoding="utf-8")
    for name, text in maintainer_scripts().items():
        (debian / name).write_text(text, encoding="utf-8")
    set_tree_metadata(stage, epoch)
    return manifest_text, manifest_sha


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def make_bundle(
    output: Path,
    package: Path,
    build_id: str,
    version: str,
    epoch: int,
    package_sha: str,
    installed_manifest_sha: str,
) -> tuple[Path, str]:
    bundle_root = output / f"{PACKAGE_NAME}-{version}-{ARCHITECTURE}"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True)
    shutil.copyfile(package, bundle_root / package.name)
    (bundle_root / f"{package.name}.sha256").write_text(
        f"{package_sha}  {package.name}\n", encoding="utf-8"
    )
    shutil.copyfile(ROOT / "release/release-manager.sh", bundle_root / "release-manager.sh")
    os.chmod(bundle_root / "release-manager.sh", 0o755)
    instructions = """MULTIMODULTOOL2026 – Releasekandidat

Prüfen:
  ./release-manager.sh verify ./multimodultool2026_*.deb

Installieren oder aktualisieren:
  sudo ./release-manager.sh install ./multimodultool2026_*.deb --yes
  sudo ./release-manager.sh upgrade ./multimodultool2026_*.deb --yes

Rollback:
  sudo ./release-manager.sh rollback --yes

Deinstallation mit Erhalt der Nutzerdaten:
  sudo ./release-manager.sh uninstall --yes

Vollständige Entfernung inklusive Releasearchiv und Daten des aufrufenden Nutzers:
  sudo ./release-manager.sh uninstall --purge-system-state --purge-current-user-data --yes
"""
    (bundle_root / "INSTALLIEREN.txt").write_text(instructions, encoding="utf-8")
    release_manifest = {
        "schemaVersion": 1,
        "package": PACKAGE_NAME,
        "version": version,
        "architecture": ARCHITECTURE,
        "buildId": build_id,
        "packageFile": package.name,
        "packageSha256": package_sha,
        "installedManifestSha256": installed_manifest_sha,
        "sourceDateEpoch": epoch,
        "signatureStatus": "unsigned-rc-checksum-only",
    }
    (bundle_root / "RELEASE_MANIFEST.json").write_text(
        json.dumps(release_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    set_tree_metadata(bundle_root, epoch)
    bundle = output / f"{bundle_root.name}.tar.gz"
    if bundle.exists():
        bundle.unlink()
    env = dict(os.environ)
    env["GZIP"] = "-n"
    run(
        [
            "tar",
            "--sort=name",
            f"--mtime=@{epoch}",
            "--owner=0",
            "--group=0",
            "--numeric-owner",
            "-czf",
            str(bundle),
            bundle_root.name,
        ],
        cwd=output,
        env=env,
    )
    return bundle, sha256_file(bundle)


def build_release(version: str, wheelhouse: Path, output: Path, epoch: int) -> BuildResult:
    if sys.platform != "linux":
        raise fail("Release packages may only be built on Linux.")
    if shutil.which("dpkg-deb") is None or shutil.which("tar") is None:
        raise fail("dpkg-deb and tar are required.")
    files = expand_allowlist()
    wheels = validate_wheelhouse(wheelhouse)
    source_manifest = canonical_source_manifest(files, wheels, version)
    source_manifest_sha = sha256_bytes(source_manifest)
    build_id = f"MMTBUILD-{version}-{source_manifest_sha[:16]}"
    if not BUILD_ID_PATTERN.fullmatch(build_id):
        raise fail(f"Generated invalid build ID: {build_id}")
    output.mkdir(parents=True, exist_ok=True)
    package = output / f"{PACKAGE_NAME}_{version}_{ARCHITECTURE}.deb"
    with tempfile.TemporaryDirectory(prefix="mmt-deb-") as temp:
        stage = Path(temp) / "stage"
        stage.mkdir()
        _, installed_manifest_sha = build_stage(
            stage,
            version=version,
            build_id=build_id,
            source_manifest=source_manifest,
            source_manifest_sha=source_manifest_sha,
            files=files,
            wheels=wheels,
            epoch=epoch,
        )
        env = dict(os.environ)
        env["SOURCE_DATE_EPOCH"] = str(epoch)
        run(
            ["dpkg-deb", "--root-owner-group", "-Zxz", "-z9", "--build", str(stage), str(package)],
            env=env,
        )
    package_sha = sha256_file(package)
    (output / f"{package.name}.sha256").write_text(f"{package_sha}  {package.name}\n", encoding="utf-8")
    bundle, bundle_sha = make_bundle(
        output,
        package,
        build_id,
        version,
        epoch,
        package_sha,
        installed_manifest_sha,
    )
    result = BuildResult(version, build_id, package, package_sha, bundle, bundle_sha, installed_manifest_sha)
    (output / "BUILD_RESULT.json").write_text(
        json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version")
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-date-epoch")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_release(
            read_version(args.version),
            args.wheelhouse.resolve(),
            args.output.resolve(),
            source_date_epoch(args.source_date_epoch),
        )
    except (OSError, subprocess.CalledProcessError, RuntimeError, ValueError) as exc:
        print(f"ROT: Releasebau fehlgeschlagen: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
