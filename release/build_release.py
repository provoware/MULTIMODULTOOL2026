#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

APP = "multimodultool2026"
DEFAULT_VERSION = "0.9.0-rc1"
SOURCE_ROOT = Path(__file__).resolve().parents[1]
INCLUDE_PREFIXES = ("src/", "assets/", "standards/", "docs/")
INCLUDE_FILES = {
    "README.md",
    "ANLEITUNG_TOOL.md",
    "ENTWICKLERDOKU.md",
    "layout-manifest.json",
    "requirements.txt",
    "start.sh",
    "setup.sh",
    "VERSION",
}
EXCLUDE_PARTS = {".git", "dist", "__pycache__", ".pytest_cache", ".mypy_cache"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_files(root: Path) -> list[Path]:
    try:
        output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
        names = [item.decode() for item in output.split(b"\0") if item]
    except Exception:
        names = [
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        ]
    selected: list[Path] = []
    for name in names:
        relative = Path(name)
        if any(part in EXCLUDE_PARTS for part in relative.parts):
            continue
        if name in INCLUDE_FILES or name.startswith(INCLUDE_PREFIXES):
            selected.append(relative)
    return sorted(set(selected), key=lambda item: item.as_posix())


def normalized_mode(path: Path) -> int:
    if path.suffix == ".sh" or path.name in {"start.sh", "setup.sh"}:
        return 0o755
    return 0o644


def source_digest(root: Path, files: list[Path], version: str) -> str:
    digest = hashlib.sha256()
    digest.update(version.encode("utf-8") + b"\0")
    for relative in files:
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256(root / relative)))
    return digest.hexdigest()


def copy_payload(root: Path, stage: Path, files: list[Path]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    payload = stage / "payload"
    for relative in files:
        source = root / relative
        target = payload / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        mode = normalized_mode(relative)
        os.chmod(target, mode)
        records.append(
            {
                "path": f"payload/{relative.as_posix()}",
                "size": target.stat().st_size,
                "mode": f"{mode:04o}",
                "sha256": sha256(target),
            }
        )
    return records


def deterministic_tar(source: Path, target: Path, epoch: int) -> None:
    members = sorted(
        [path for path in source.rglob("*")],
        key=lambda path: path.relative_to(source).as_posix(),
    )
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as archive:
        root_info = tarfile.TarInfo(source.name)
        root_info.type = tarfile.DIRTYPE
        root_info.mode = 0o755
        root_info.uid = root_info.gid = 0
        root_info.uname = root_info.gname = "root"
        root_info.mtime = epoch
        archive.addfile(root_info)
        for path in members:
            relative = Path(source.name) / path.relative_to(source)
            info = tarfile.TarInfo(relative.as_posix())
            metadata = path.lstat()
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = epoch
            if path.is_dir():
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                archive.addfile(info)
            elif path.is_file():
                info.size = metadata.st_size
                info.mode = metadata.st_mode & 0o777
                info.type = tarfile.REGTYPE
                with path.open("rb") as handle:
                    archive.addfile(info, handle)
            else:
                raise RuntimeError(f"Nicht unterstützter Paketeintrag: {path}")
    raw.seek(0)
    with target.open("wb") as output, gzip.GzipFile(
        filename="", mode="wb", fileobj=output, mtime=epoch, compresslevel=9
    ) as compressed:
        shutil.copyfileobj(raw, compressed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=None)
    parser.add_argument("--output", type=Path, default=SOURCE_ROOT / "dist")
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--source-date-epoch",
        type=int,
        default=int(os.environ.get("SOURCE_DATE_EPOCH", "1704067200")),
    )
    args = parser.parse_args()
    version_file = SOURCE_ROOT / "VERSION"
    version = args.version or (
        version_file.read_text(encoding="utf-8").strip()
        if version_file.exists()
        else DEFAULT_VERSION
    )
    files = tracked_files(SOURCE_ROOT)
    digest = source_digest(SOURCE_ROOT, files, version)
    build_id = f"{version}+{digest[:16]}"
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        package = Path(temporary) / f"{APP}-{build_id}"
        package.mkdir()
        records = copy_payload(SOURCE_ROOT, package, files)
        for relative in ("release/release_manager.py", "release/launcher.sh"):
            source = SOURCE_ROOT / relative
            target = package / Path(relative).name
            shutil.copyfile(source, target)
            os.chmod(target, 0o755)
            records.append(
                {
                    "path": target.name,
                    "size": target.stat().st_size,
                    "mode": "0755",
                    "sha256": sha256(target),
                }
            )
        if args.wheelhouse:
            wheelhouse = package / "wheelhouse"
            shutil.copytree(args.wheelhouse, wheelhouse)
            for path in sorted(wheelhouse.rglob("*")):
                if path.is_file():
                    records.append(
                        {
                            "path": path.relative_to(package).as_posix(),
                            "size": path.stat().st_size,
                            "mode": "0644",
                            "sha256": sha256(path),
                        }
                    )
        metadata = {
            "schemaVersion": 1,
            "application": APP,
            "version": version,
            "buildId": build_id,
            "sourceDigest": digest,
            "sourceDateEpoch": args.source_date_epoch,
            "platform": {
                "os": "linux",
                "architectures": ["x86_64"],
                "distributions": ["Kubuntu 22.04 LTS", "Kubuntu 24.04 LTS"],
            },
            "files": sorted(records, key=lambda item: str(item["path"])),
        }
        metadata_path = package / "RELEASE-METADATA.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.chmod(metadata_path, 0o644)
        archive = args.output / f"{package.name}.tar.gz"
        deterministic_tar(package, archive, args.source_date_epoch)
        archive_hash = sha256(archive)
        Path(str(archive) + ".sha256").write_text(
            f"{archive_hash}  {archive.name}\n", encoding="utf-8"
        )
        (args.output / f"{package.name}.build.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "archive": str(archive),
                    "buildId": build_id,
                    "sha256": archive_hash,
                    "files": len(records),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
