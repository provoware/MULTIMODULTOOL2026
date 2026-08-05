#!/usr/bin/env python3
"""Create the final `_save_` release directory after successful lifecycle checks."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile
import tempfile
from typing import Any

SAVE_SUFFIX = "_save_"
BUILD_RESULT_NAME = "CANDIDATE_BUILD_RESULT.json"
RELEASE_MANAGER_NAME = "release-manager.sh"


def fail(message: str) -> RuntimeError:
    return RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_sha256(value: str) -> bool:
    return bool(len(value) == 64 and all(character in "0123456789abcdef" for character in value))


def save_name(name: str) -> str:
    """Append `_save_` before the effective release extension."""

    if SAVE_SUFFIX in name:
        raise fail(f"Artifact already contains {SAVE_SUFFIX}: {name}")
    if name.endswith(".tar.gz"):
        return f"{name[:-7]}{SAVE_SUFFIX}.tar.gz"
    path = Path(name)
    if not path.suffix:
        return f"{name}{SAVE_SUFFIX}"
    return f"{path.stem}{SAVE_SUFFIX}{path.suffix}"


def reject_symlink_components(path: Path, label: str) -> None:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.exists() and candidate.is_symlink():
            raise fail(f"{label} contains a symlink component: {candidate}")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise fail(f"JSON cannot be read safely: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise fail(f"JSON root must be an object: {path}")
    return payload


def safe_file(root: Path, name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or len(relative.parts) != 1 or ".." in relative.parts:
        raise fail(f"Unsafe artifact filename: {name}")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise fail(f"Required regular artifact is missing or unsafe: {path}")
    return path


def read_sidecar(sidecar: Path, expected_name: str, expected_sha: str) -> None:
    try:
        line = sidecar.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise fail(f"Checksum sidecar cannot be read: {sidecar}: {exc}") from exc
    fields = line.split()
    if len(fields) != 2 or fields[0] != expected_sha or fields[1] != expected_name:
        raise fail(f"Checksum sidecar is not bound to {expected_name}: {sidecar}")


def copy_verified(source: Path, target: Path, expected_sha: str | None = None) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    actual_sha = sha256_file(target)
    if expected_sha is not None and actual_sha != expected_sha:
        target.unlink(missing_ok=True)
        raise fail(f"Copied artifact hash changed: {source.name}")
    os.chmod(target, 0o644)
    return {"file": target.name, "sha256": actual_sha, "size": target.stat().st_size}


def _tar_info(name: str, *, mode: int, size: int = 0, directory: bool = False) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.mode = mode
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.size = size
    if directory:
        info.type = tarfile.DIRTYPE
    return info


def build_final_bundle(
    target: Path,
    *,
    root_name: str,
    package: Path,
    package_name: str,
    sidecar: Path,
    sidecar_name: str,
    manager: Path,
    manager_name: str,
) -> str:
    """Build a deterministic bundle whose internal release files all carry `_save_`."""

    if SAVE_SUFFIX not in root_name:
        raise fail("Final bundle root lacks the release suffix.")
    instructions_name = save_name("INSTALLIEREN.txt")
    instructions = f"""MULTIMODULTOOL2026 – geprüfte Releaseausgabe

Prüfen:
  ./{manager_name} verify ./{package_name}

Installieren oder aktualisieren:
  sudo ./{manager_name} install ./{package_name} --yes
  sudo ./{manager_name} upgrade ./{package_name} --yes

Rollback:
  sudo ./{manager_name} rollback --yes

Deinstallation mit Erhalt der Nutzerdaten:
  sudo ./{manager_name} uninstall --yes

Vollständige bestätigte Entfernung:
  sudo ./{manager_name} uninstall --purge-system-state --purge-current-user-data --yes
""".encode("utf-8")
    members = (
        (package_name, package.read_bytes(), 0o644),
        (sidecar_name, sidecar.read_bytes(), 0o644),
        (manager_name, manager.read_bytes(), 0o755),
        (instructions_name, instructions, 0o644),
    )
    if any(SAVE_SUFFIX not in name for name, _, _ in members):
        raise fail("Final bundle contains an internal file without the release suffix.")

    with target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                archive.addfile(_tar_info(root_name, mode=0o755, directory=True))
                for name, payload, mode in members:
                    archive.addfile(
                        _tar_info(f"{root_name}/{name}", mode=mode, size=len(payload)),
                        io.BytesIO(payload),
                    )
    os.chmod(target, 0o644)
    return sha256_file(target)


def replace_directory_atomically(staged: Path, output: Path) -> None:
    backup = output.parent / f".{output.name}.previous"
    if backup.exists():
        if backup.is_symlink() or not backup.is_dir():
            raise fail(f"Unsafe previous-output path: {backup}")
        shutil.rmtree(backup)
    moved_previous = False
    try:
        if output.exists():
            if output.is_symlink() or not output.is_dir():
                raise fail(f"Unsafe output path: {output}")
            os.replace(output, backup)
            moved_previous = True
        os.replace(staged, output)
    except BaseException:
        if moved_previous and backup.exists() and not output.exists():
            os.replace(backup, output)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def finalize_release(source: Path, output: Path, policy_path: Path) -> dict[str, Any]:
    reject_symlink_components(source, "Source artifact directory")
    reject_symlink_components(output, "Output directory")
    reject_symlink_components(policy_path, "Release status policy")
    source = source.resolve()
    output = output.resolve()
    policy_path = policy_path.resolve()
    if not source.is_dir():
        raise fail(f"Source artifact directory is missing or unsafe: {source}")
    if output == source or source in output.parents:
        raise fail("Output directory must not be the source directory or a child of it.")
    output.parent.mkdir(parents=True, exist_ok=True)

    policy = read_json(policy_path)
    if policy.get("releaseSuffix") != SAVE_SUFFIX:
        raise fail("Release status policy has an unexpected suffix.")
    if policy.get("sourceRenameForbidden") is not True:
        raise fail("Release status policy must forbid source renaming.")

    build_result_path = safe_file(source, BUILD_RESULT_NAME)
    build_result = read_json(build_result_path)
    package_name = Path(str(build_result.get("package", ""))).name
    bundle_name = Path(str(build_result.get("bundle", ""))).name
    package_sha = str(build_result.get("packageSha256", ""))
    source_bundle_sha = str(build_result.get("bundleSha256", ""))
    if not package_name.endswith(".deb") or not bundle_name.endswith(".tar.gz"):
        raise fail("Build result does not name a Debian package and release bundle.")
    if not is_sha256(package_sha) or not is_sha256(source_bundle_sha):
        raise fail("Build result contains invalid artifact hashes.")

    package = safe_file(source, package_name)
    source_sidecar = safe_file(source, f"{package_name}.sha256")
    source_bundle = safe_file(source, bundle_name)
    manager = safe_file(source, RELEASE_MANAGER_NAME)
    if sha256_file(package) != package_sha:
        raise fail("Candidate package does not match CANDIDATE_BUILD_RESULT.json.")
    if sha256_file(source_bundle) != source_bundle_sha:
        raise fail("Candidate bundle does not match CANDIDATE_BUILD_RESULT.json.")
    read_sidecar(source_sidecar, package_name, package_sha)

    staged: Path | None = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent)
    )
    try:
        saved_package_name = save_name(package_name)
        saved_sidecar_name = f"{saved_package_name}.sha256"
        saved_bundle_name = save_name(bundle_name)
        saved_manager_name = save_name(manager.name)
        saved_result_name = save_name(BUILD_RESULT_NAME)
        saved_status_name = save_name("RELEASE_STATUS.json")

        entries: list[dict[str, Any]] = []
        saved_package = staged / saved_package_name
        entries.append(copy_verified(package, saved_package, package_sha))

        saved_sidecar = staged / saved_sidecar_name
        saved_sidecar.write_text(
            f"{package_sha}  {saved_package_name}\n",
            encoding="utf-8",
        )
        os.chmod(saved_sidecar, 0o644)
        entries.append(
            {
                "file": saved_sidecar.name,
                "sha256": sha256_file(saved_sidecar),
                "size": saved_sidecar.stat().st_size,
            }
        )

        saved_manager = staged / saved_manager_name
        manager_entry = copy_verified(manager, saved_manager)
        os.chmod(saved_manager, 0o755)
        manager_entry["mode"] = "0755"

        saved_bundle = staged / saved_bundle_name
        bundle_root_name = saved_bundle_name[:-7]
        saved_bundle_sha = build_final_bundle(
            saved_bundle,
            root_name=bundle_root_name,
            package=saved_package,
            package_name=saved_package_name,
            sidecar=saved_sidecar,
            sidecar_name=saved_sidecar_name,
            manager=saved_manager,
            manager_name=saved_manager_name,
        )
        entries.append(
            {
                "file": saved_bundle_name,
                "sha256": saved_bundle_sha,
                "size": saved_bundle.stat().st_size,
            }
        )
        entries.append(manager_entry)

        normalized_result = dict(build_result)
        normalized_result.update(
            {
                "package": saved_package_name,
                "packageSha256": package_sha,
                "bundle": saved_bundle_name,
                "bundleSha256": saved_bundle_sha,
                "sourceBundle": bundle_name,
                "sourceBundleSha256": source_bundle_sha,
                "releaseManager": saved_manager_name,
                "releaseStatus": "ready-after-green-kubuntu-matrix",
                "releaseSuffix": SAVE_SUFFIX,
            }
        )
        saved_result = staged / saved_result_name
        saved_result.write_text(
            json.dumps(normalized_result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(saved_result, 0o644)
        entries.append(
            {
                "file": saved_result_name,
                "sha256": sha256_file(saved_result),
                "size": saved_result.stat().st_size,
            }
        )

        manifest = {
            "schemaVersion": 1,
            "status": "release-ready",
            "releaseSuffix": SAVE_SUFFIX,
            "sourceRenamed": False,
            "buildId": build_result.get("buildId"),
            "version": build_result.get("version"),
            "artifacts": entries,
            "testOnlyArtifactsExcluded": policy.get("testOnlyArtifacts", []),
            "unfinished": policy.get("unfinished", []),
        }
        saved_status = staged / saved_status_name
        saved_status.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(saved_status, 0o644)

        for path in staged.iterdir():
            if path.is_symlink() or not path.is_file():
                raise fail(f"Unexpected final release entry: {path}")
            if SAVE_SUFFIX not in path.name:
                raise fail(f"Release-ready file lacks {SAVE_SUFFIX}: {path.name}")
            mode = stat.S_IMODE(path.stat().st_mode)
            expected_mode = 0o755 if path.name == saved_manager_name else 0o644
            if mode != expected_mode:
                raise fail(f"Unexpected mode for {path.name}: {mode:o}")

        replace_directory_atomically(staged, output)
        staged = None
        return manifest
    finally:
        if staged is not None and staged.exists():
            shutil.rmtree(staged)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create atomically validated release-ready files with the _save_ suffix."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "release/release-status.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = finalize_release(args.source, args.output, args.policy)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ROT: Release-Finalisierung fehlgeschlagen: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
