#!/usr/bin/env python3
"""Create the final `_save_` release directory after successful lifecycle checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any

SAVE_SUFFIX = "_save_"
BUILD_RESULT_NAME = "CANDIDATE_BUILD_RESULT.json"
RELEASE_MANAGER_NAME = "release-manager.sh"
STATUS_POLICY_NAME = "release-status.json"


def fail(message: str) -> RuntimeError:
    return RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    source = source.resolve()
    output = output.resolve()
    policy_path = policy_path.resolve()
    if not source.is_dir() or source.is_symlink():
        raise fail(f"Source artifact directory is missing or unsafe: {source}")
    if output == source or source in output.parents:
        raise fail("Output directory must not be the source directory or a child of it.")
    if output.parent.is_symlink():
        raise fail(f"Output parent may not be a symlink: {output.parent}")
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
    bundle_sha = str(build_result.get("bundleSha256", ""))
    if not package_name.endswith(".deb") or not bundle_name.endswith(".tar.gz"):
        raise fail("Build result does not name a Debian package and release bundle.")
    if len(package_sha) != 64 or len(bundle_sha) != 64:
        raise fail("Build result contains invalid artifact hashes.")

    package = safe_file(source, package_name)
    sidecar = safe_file(source, f"{package_name}.sha256")
    bundle = safe_file(source, bundle_name)
    manager = safe_file(source, RELEASE_MANAGER_NAME)
    if sha256_file(package) != package_sha:
        raise fail("Candidate package does not match CANDIDATE_BUILD_RESULT.json.")
    if sha256_file(bundle) != bundle_sha:
        raise fail("Candidate bundle does not match CANDIDATE_BUILD_RESULT.json.")
    read_sidecar(sidecar, package_name, package_sha)

    staged = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        saved_package_name = save_name(package_name)
        saved_bundle_name = save_name(bundle_name)
        saved_manager_name = save_name(manager.name)
        saved_result_name = save_name(BUILD_RESULT_NAME)
        saved_status_name = save_name("RELEASE_STATUS.json")

        entries: list[dict[str, Any]] = []
        entries.append(copy_verified(package, staged / saved_package_name, package_sha))
        (staged / f"{saved_package_name}.sha256").write_text(
            f"{package_sha}  {saved_package_name}\n",
            encoding="utf-8",
        )
        os.chmod(staged / f"{saved_package_name}.sha256", 0o644)
        entries.append(
            {
                "file": f"{saved_package_name}.sha256",
                "sha256": sha256_file(staged / f"{saved_package_name}.sha256"),
                "size": (staged / f"{saved_package_name}.sha256").stat().st_size,
            }
        )
        entries.append(copy_verified(bundle, staged / saved_bundle_name, bundle_sha))
        manager_entry = copy_verified(manager, staged / saved_manager_name)
        os.chmod(staged / saved_manager_name, 0o755)
        manager_entry["mode"] = "0755"
        entries.append(manager_entry)

        normalized_result = dict(build_result)
        normalized_result.update(
            {
                "package": saved_package_name,
                "bundle": saved_bundle_name,
                "releaseManager": saved_manager_name,
                "releaseStatus": "ready-after-green-kubuntu-matrix",
                "releaseSuffix": SAVE_SUFFIX,
            }
        )
        (staged / saved_result_name).write_text(
            json.dumps(normalized_result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(staged / saved_result_name, 0o644)
        entries.append(
            {
                "file": saved_result_name,
                "sha256": sha256_file(staged / saved_result_name),
                "size": (staged / saved_result_name).stat().st_size,
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
        (staged / saved_status_name).write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(staged / saved_status_name, 0o644)

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
        staged = Path()
        return manifest
    finally:
        if staged and staged.exists():
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
        print(f"ROT: Release-Finalisierung fehlgeschlagen: {exc}")
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
