#!/usr/bin/env python3
"""Validate, manifest, and verify Sigstore keyless release signatures.

Signing itself is performed by the official ``cosign`` binary in GitHub Actions.
This helper provides strict subject selection, deterministic release metadata and
post-signing verification without storing any private signing key in the repo.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from uuid import uuid4

EXPECTED_PRIMARY_COUNT = 6
BUNDLE_SUFFIX = ".sigstore.json"
MANIFEST_NAME = "SIGNED_RELEASE_MANIFEST_save_.json"
MANIFEST_BUNDLE_NAME = MANIFEST_NAME + BUNDLE_SUFFIX
MAXIMUM_ARTIFACT_BYTES = 2 * 1024 * 1024 * 1024
MAXIMUM_BUNDLE_BYTES = 4 * 1024 * 1024
MAXIMUM_MANIFEST_BYTES = 512 * 1024
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class SigningContractError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_directory(path: Path) -> Path:
    root = path.expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).absolute()
    root = Path(os.path.abspath(os.fspath(root)))
    if root.is_symlink() or not root.is_dir():
        raise SigningContractError(f"Signaturverzeichnis fehlt, ist kein Ordner oder ist ein Symlink: {root}")
    return root


def _safe_regular(path: Path, *, maximum_bytes: int) -> os.stat_result:
    if path.is_symlink():
        raise SigningContractError(f"Symlink ist als Signatursubjekt verboten: {path.name}")
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise SigningContractError(f"Erwartete Datei fehlt: {path.name}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise SigningContractError(f"Erwartete reguläre Datei ist ungültig: {path.name}")
    if metadata.st_nlink != 1:
        raise SigningContractError(f"Datei besitzt zusätzliche Hardlinks: {path.name}")
    if metadata.st_size < 1 or metadata.st_size > maximum_bytes:
        raise SigningContractError(f"Dateigröße außerhalb des Vertrags: {path.name}: {metadata.st_size}")
    return metadata


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def primary_subjects(directory: Path) -> tuple[Path, ...]:
    root = _safe_directory(directory)
    subjects: list[Path] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() and not path.is_symlink():
            continue
        if path.name in {MANIFEST_NAME, MANIFEST_BUNDLE_NAME} or path.name.endswith(BUNDLE_SUFFIX):
            continue
        if "_save_" not in path.name:
            raise SigningContractError(f"Nicht finalisierte Datei im Signaturverzeichnis: {path.name}")
        _safe_regular(path, maximum_bytes=MAXIMUM_ARTIFACT_BYTES)
        subjects.append(path)
    if len(subjects) != EXPECTED_PRIMARY_COUNT:
        raise SigningContractError(
            f"Exakt {EXPECTED_PRIMARY_COUNT} fertige Primärdateien erforderlich; gefunden: {len(subjects)}"
        )
    return tuple(subjects)


def _read_bundle(path: Path) -> dict[str, object]:
    _safe_regular(path, maximum_bytes=MAXIMUM_BUNDLE_BYTES)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SigningContractError(f"Sigstore-Bundle ist nicht gültiges UTF-8-JSON: {path.name}: {exc}") from exc
    if not isinstance(value, dict) or not value:
        raise SigningContractError(f"Sigstore-Bundle besitzt keinen gültigen JSON-Aufbau: {path.name}")
    return value


def _atomic_write_json(path: Path, value: dict[str, object]) -> None:
    encoded = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAXIMUM_MANIFEST_BYTES:
        raise SigningContractError("Signaturmanifest überschreitet das Größenlimit.")
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o644)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("Manifest wurde nicht vollständig geschrieben.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(temporary, path)
        os.chmod(path, 0o644)
    except OSError as exc:
        raise SigningContractError(f"Signaturmanifest konnte nicht atomar geschrieben werden: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def create_signed_manifest(directory: Path, *, identity_regexp: str, issuer: str) -> Path:
    if not identity_regexp.strip() or not issuer.strip():
        raise SigningContractError("Signiereridentität und OIDC-Aussteller dürfen nicht leer sein.")
    root = _safe_directory(directory)
    artifacts: list[dict[str, object]] = []
    for subject in primary_subjects(root):
        bundle = subject.with_name(subject.name + BUNDLE_SUFFIX)
        _read_bundle(bundle)
        digest = _sha256(subject)
        if not SHA256_PATTERN.fullmatch(digest):
            raise SigningContractError(f"SHA-256 konnte nicht bestimmt werden: {subject.name}")
        artifacts.append(
            {
                "file": subject.name,
                "sha256": digest,
                "size": subject.stat().st_size,
                "bundle": bundle.name,
            }
        )
    manifest = {
        "schemaVersion": 1,
        "status": "signed-release",
        "signingMode": "sigstore-keyless-oidc",
        "bundleFormat": "sigstore-json",
        "createdUtc": _utc_now(),
        "oidcIssuer": issuer,
        "certificateIdentityRegexp": identity_regexp,
        "releaseSuffix": "_save_",
        "sourcePrivateKeyStored": False,
        "artifacts": artifacts,
    }
    path = root / MANIFEST_NAME
    if path.is_symlink():
        raise SigningContractError("Signaturmanifestziel darf kein Symlink sein.")
    _atomic_write_json(path, manifest)
    return path


def verify_signed_release(
    directory: Path,
    *,
    identity_regexp: str,
    issuer: str,
    cosign: str = "cosign",
) -> None:
    root = _safe_directory(directory)
    subjects = (*primary_subjects(root), root / MANIFEST_NAME)
    for subject in subjects:
        _safe_regular(subject, maximum_bytes=MAXIMUM_ARTIFACT_BYTES)
        bundle = subject.with_name(subject.name + BUNDLE_SUFFIX)
        _read_bundle(bundle)
        completed = subprocess.run(
            [
                cosign,
                "verify-blob",
                "--bundle",
                str(bundle),
                "--certificate-identity-regexp",
                identity_regexp,
                "--certificate-oidc-issuer",
                issuer,
                str(subject),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise SigningContractError(f"Cosign-Verifikation fehlgeschlagen: {subject.name}: {detail}")
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    expected = {path.name: _sha256(path) for path in primary_subjects(root)}
    declared = {
        entry.get("file"): entry.get("sha256")
        for entry in manifest.get("artifacts", [])
        if isinstance(entry, dict)
    }
    if declared != expected:
        raise SigningContractError("Signaturmanifest und aktuelle Primärdateien stimmen nicht überein.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sigstore-Schlüssel-los-Signaturvertrag für _save_-Releaseartefakte.")
    sub = parser.add_subparsers(dest="command", required=True)
    subjects = sub.add_parser("subjects", help="Exakt sechs geprüfte Primärdateien ausgeben.")
    subjects.add_argument("--directory", type=Path, required=True)
    manifest = sub.add_parser("manifest", help="Signiertes Releasemanifest nach vorhandenen Bundles erzeugen.")
    manifest.add_argument("--directory", type=Path, required=True)
    manifest.add_argument("--identity-regexp", required=True)
    manifest.add_argument("--issuer", required=True)
    verify = sub.add_parser("verify", help="Alle Bundles mit cosign verifizieren und Manifest abgleichen.")
    verify.add_argument("--directory", type=Path, required=True)
    verify.add_argument("--identity-regexp", required=True)
    verify.add_argument("--issuer", required=True)
    verify.add_argument("--cosign", default="cosign")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "subjects":
            for path in primary_subjects(args.directory):
                print(path.name)
        elif args.command == "manifest":
            print(create_signed_manifest(args.directory, identity_regexp=args.identity_regexp, issuer=args.issuer))
        else:
            verify_signed_release(
                args.directory,
                identity_regexp=args.identity_regexp,
                issuer=args.issuer,
                cosign=args.cosign,
            )
            print("GRÜN: Alle Sigstore-Bundles und das signierte Releasemanifest sind gültig.")
        return 0
    except SigningContractError as exc:
        print(f"ROT: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
