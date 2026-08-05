#!/usr/bin/env python3
"""Collect and verify the post-merge P3-009 signed release artifact."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from typing import Any, BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import zipfile

try:
    from .sign_release_artifacts import (
        BUNDLE_SUFFIX,
        MANIFEST_BUNDLE_NAME,
        MANIFEST_NAME,
        SigningContractError,
        verify_signed_release,
    )
except ImportError:  # pragma: no cover - direct execution
    from sign_release_artifacts import (  # type: ignore
        BUNDLE_SUFFIX,
        MANIFEST_BUNDLE_NAME,
        MANIFEST_NAME,
        SigningContractError,
        verify_signed_release,
    )

EXPECTED_FILE_COUNT = 14
EXPECTED_PRIMARY_COUNT = 6
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DEFAULT_API_BASE = "https://api.github.com"
DEFAULT_WORKFLOW_PATH = ".github/workflows/release-candidate.yml"
DEFAULT_ARTIFACT_NAME = "multimodultool2026-release-signed"
DEFAULT_IDENTITY_REGEXP = (
    r"^https://github.com/provoware/MULTIMODULTOOL2026/"
    r".github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$"
)
DEFAULT_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
MAX_ARCHIVE_BYTES = 4 * 1024 * 1024 * 1024
REDIRECT_CODES = frozenset({301, 302, 303, 307, 308})
USER_AGENT = "multimodultool2026-p3-009-evidence"


class EvidenceError(RuntimeError):
    """Raised when the main-branch evidence contract is violated."""


class _NoRedirect(HTTPRedirectHandler):
    """Expose GitHub's signed storage URL instead of forwarding credentials."""

    def redirect_request(  # type: ignore[override]
        self,
        req: Request,
        fp: BinaryIO,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _json_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{context} ist kein JSON-Objekt.")
    return value


def _api_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }


def _api_json(url: str, token: str) -> dict[str, Any]:
    request = Request(url, headers=_api_headers(token))
    try:
        with urlopen(request, timeout=60) as response:
            return _json_object(json.load(response), f"GitHub-Antwort {url}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"GitHub-API-Abfrage fehlgeschlagen: {url}: {exc}") from exc


def _redirect_target(url: str, token: str) -> str:
    """Resolve GitHub's artifact redirect without leaking its bearer token."""

    request = Request(url, headers=_api_headers(token))
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=60) as response:
            location = response.headers.get("Location")
            status = getattr(response, "status", 200)
            if status not in REDIRECT_CODES or not location:
                raise EvidenceError(
                    "GitHub-Artefaktendpunkt lieferte keinen signierten Download-Redirect."
                )
    except HTTPError as exc:
        if exc.code not in REDIRECT_CODES:
            raise EvidenceError(
                f"GitHub-Artefaktredirect konnte nicht aufgelöst werden: HTTP {exc.code}"
            ) from exc
        location = exc.headers.get("Location")
        if not location:
            raise EvidenceError("GitHub-Artefaktredirect enthält kein Location-Ziel.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise EvidenceError(f"GitHub-Artefaktredirect konnte nicht aufgelöst werden: {exc}") from exc

    parsed = urlsplit(location)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise EvidenceError("GitHub lieferte kein sicheres HTTPS-Artefaktziel.")
    return location


def _stream_download(url: str, target: Path) -> None:
    """Download the signed storage URL deliberately without Authorization."""

    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=120) as response, target.open("xb") as handle:
            total = 0
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > MAX_ARCHIVE_BYTES:
                    raise EvidenceError("Signaturartefakt überschreitet das Archivgrößenlimit.")
                handle.write(block)
    except EvidenceError:
        target.unlink(missing_ok=True)
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        target.unlink(missing_ok=True)
        raise EvidenceError(f"GitHub-Artefakt konnte nicht geladen werden: {exc}") from exc


def _download(url: str, token: str, target: Path) -> None:
    target.unlink(missing_ok=True)
    storage_url = _redirect_target(url, token)
    _stream_download(storage_url, target)


def select_main_run(
    runs: list[dict[str, Any]], *, commit_sha: str, workflow_path: str
) -> dict[str, Any]:
    candidates = [
        run
        for run in runs
        if run.get("head_sha") == commit_sha
        and run.get("event") == "push"
        and run.get("head_branch") == "main"
        and str(run.get("path", "")).split("@", 1)[0] == workflow_path
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    if not candidates:
        raise EvidenceError("Kein erfolgreicher abgeschlossener main-Push-Lauf für das Merge-SHA gefunden.")
    candidates.sort(
        key=lambda item: (int(item.get("run_attempt") or 0), int(item.get("id") or 0)),
        reverse=True,
    )
    return candidates[0]


def select_signed_artifact(artifacts: list[dict[str, Any]], *, name: str) -> dict[str, Any]:
    matches = [
        artifact
        for artifact in artifacts
        if artifact.get("name") == name and not artifact.get("expired", False)
    ]
    if len(matches) != 1:
        raise EvidenceError(
            f"Exakt ein nicht abgelaufenes Artefakt {name!r} erforderlich; gefunden: {len(matches)}"
        )
    return matches[0]


def safe_extract_archive(archive: Path, destination: Path) -> tuple[str, ...]:
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(archive) as bundle:
            infos = bundle.infolist()
            if len(infos) != EXPECTED_FILE_COUNT:
                raise EvidenceError(
                    f"Signaturartefakt muss exakt {EXPECTED_FILE_COUNT} ZIP-Einträge besitzen; gefunden: {len(infos)}"
                )
            names: list[str] = []
            for info in infos:
                pure = PurePosixPath(info.filename)
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if (
                    info.is_dir()
                    or pure.is_absolute()
                    or len(pure.parts) != 1
                    or pure.name in {"", ".", ".."}
                    or any(part in {"", ".", ".."} for part in pure.parts)
                    or stat.S_ISLNK(unix_mode)
                ):
                    raise EvidenceError(f"Unsicherer ZIP-Eintrag im Signaturartefakt: {info.filename!r}")
                if pure.name in names:
                    raise EvidenceError(f"Doppelter ZIP-Eintrag im Signaturartefakt: {pure.name}")
                names.append(pure.name)
                target = destination / pure.name
                with bundle.open(info) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
            return tuple(sorted(names, key=str.casefold))
    except (zipfile.BadZipFile, OSError) as exc:
        raise EvidenceError(f"Signaturartefakt ist kein sicher lesbares ZIP-Archiv: {exc}") from exc


def _load_manifest(directory: Path) -> dict[str, Any]:
    path = directory / MANIFEST_NAME
    try:
        return _json_object(json.loads(path.read_text(encoding="utf-8")), MANIFEST_NAME)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"Signiertes Releasemanifest ist ungültig: {exc}") from exc


def inspect_verified_directory(
    directory: Path, *, identity_regexp: str, issuer: str, cosign: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        verify_signed_release(
            directory,
            identity_regexp=identity_regexp,
            issuer=issuer,
            cosign=cosign,
        )
    except SigningContractError as exc:
        raise EvidenceError(f"Kryptografische Cosign-Nachprüfung fehlgeschlagen: {exc}") from exc

    entries = sorted(directory.iterdir(), key=lambda path: path.name.casefold())
    if len(entries) != EXPECTED_FILE_COUNT or any(
        path.is_symlink() or not path.is_file() for path in entries
    ):
        raise EvidenceError("Entpacktes Signaturartefakt enthält nicht exakt 14 reguläre Dateien.")

    manifest = _load_manifest(directory)
    if manifest.get("status") != "signed-release":
        raise EvidenceError("Signiertes Releasemanifest besitzt nicht den Status signed-release.")
    if manifest.get("oidcIssuer") != issuer:
        raise EvidenceError("OIDC-Aussteller im Releasemanifest stimmt nicht mit dem Prüfvertrag überein.")
    if manifest.get("certificateIdentityRegexp") != identity_regexp:
        raise EvidenceError("Workflowidentität im Releasemanifest stimmt nicht mit dem Prüfvertrag überein.")

    declared = manifest.get("artifacts")
    if not isinstance(declared, list) or len(declared) != EXPECTED_PRIMARY_COUNT:
        raise EvidenceError("Signiertes Releasemanifest muss exakt sechs Primärdateien deklarieren.")

    files: list[dict[str, Any]] = []
    declared_names: set[str] = set()
    for item in declared:
        entry = _json_object(item, "Manifest-Artefakteintrag")
        name = entry.get("file")
        bundle_name = entry.get("bundle")
        digest = entry.get("sha256")
        size = entry.get("size")
        if not isinstance(name, str) or not isinstance(bundle_name, str):
            raise EvidenceError("Manifest-Artefakteintrag enthält ungültige Dateinamen.")
        if name in declared_names or bundle_name != name + BUNDLE_SUFFIX:
            raise EvidenceError("Manifest-Artefakteintrag ist doppelt oder besitzt eine falsche Bundle-Bindung.")
        declared_names.add(name)
        subject = directory / name
        bundle = directory / bundle_name
        actual_digest = _sha256(subject)
        if digest != actual_digest or not SHA256_PATTERN.fullmatch(actual_digest):
            raise EvidenceError(f"SHA-256-Abweichung für Primärdatei: {name}")
        if size != subject.stat().st_size:
            raise EvidenceError(f"Größenabweichung für Primärdatei: {name}")
        files.extend(
            [
                {
                    "name": name,
                    "role": "primary",
                    "size": subject.stat().st_size,
                    "sha256": actual_digest,
                    "bundle": bundle_name,
                },
                {
                    "name": bundle_name,
                    "role": "primary-signature-bundle",
                    "size": bundle.stat().st_size,
                    "sha256": _sha256(bundle),
                    "subject": name,
                },
            ]
        )

    manifest_path = directory / MANIFEST_NAME
    manifest_bundle = directory / MANIFEST_BUNDLE_NAME
    files.extend(
        [
            {
                "name": MANIFEST_NAME,
                "role": "signed-release-manifest",
                "size": manifest_path.stat().st_size,
                "sha256": _sha256(manifest_path),
                "bundle": MANIFEST_BUNDLE_NAME,
            },
            {
                "name": MANIFEST_BUNDLE_NAME,
                "role": "manifest-signature-bundle",
                "size": manifest_bundle.stat().st_size,
                "sha256": _sha256(manifest_bundle),
                "subject": MANIFEST_NAME,
            },
        ]
    )
    files.sort(key=lambda entry: str(entry["name"]).casefold())
    if len(files) != EXPECTED_FILE_COUNT:
        raise EvidenceError("Interne Evidenzliste besitzt nicht exakt 14 Dateien.")
    return manifest, files


def _write_evidence(output: Path, evidence: dict[str, Any]) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "P3_009_MAIN_SIGNATURE_EVIDENCE.json"
    markdown_path = output / "P3_009_MAIN_SIGNATURE_EVIDENCE.md"
    json_path.write_text(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    run = evidence["workflowRun"]
    artifact = evidence["artifact"]
    lines = [
        "# P3-009 Hauptzweig-Signaturnachweis",
        "",
        "## Abschlussstatus",
        "",
        "**GRÜN – der post-merge `main`-Lauf und das signierte Releaseartefakt wurden vollständig nachgewiesen.**",
        "",
        f"- Repository: `{evidence['repository']}`",
        f"- Merge-SHA: `{evidence['mainCommitSha']}`",
        f"- Workflow-Lauf: `{run['id']}` (Versuch {run['attempt']})",
        f"- Ereignis/Zweig: `{run['event']}` / `{run['headBranch']}`",
        f"- Ergebnis: `{run['status']}` / `{run['conclusion']}`",
        f"- Artefakt: `{artifact['name']}` (`{artifact['id']}`)",
        f"- Dateien: `{artifact['fileCount']}`",
        f"- Workflowidentität: `{evidence['verification']['certificateIdentityRegexp']}`",
        f"- OIDC-Aussteller: `{evidence['verification']['oidcIssuer']}`",
        "- Kryptografische Cosign-Verifikation: `bestanden`",
        "- Manifest- und Dateidigestprüfung: `bestanden`",
        "",
        "## Dateien und SHA-256",
        "",
        "| Rolle | Datei | Größe | SHA-256 |",
        "|---|---|---:|---|",
    ]
    for item in evidence["files"]:
        lines.append(
            f"| {item['role']} | `{item['name']}` | {item['size']} | `{item['sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Prüfvertrag",
            "",
            "Der Nachweis wählt ausschließlich einen erfolgreichen, abgeschlossenen `push`-Lauf auf `main` mit exakt dem Merge-SHA und dem Workflow `.github/workflows/release-candidate.yml`. Das nicht abgelaufene Artefakt muss exakt einmal vorhanden sein und genau 14 reguläre Dateien auf oberster Ebene enthalten. Alle sieben Sigstore-Bundles werden kryptografisch gegen Workflowidentität und OIDC-Aussteller verifiziert; Größen und SHA-256-Werte der sechs Primärdateien müssen mit dem signierten Releasemanifest übereinstimmen.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, markdown_path


def collect_evidence(
    *,
    repository: str,
    commit_sha: str,
    token: str,
    output_directory: Path,
    api_base: str,
    workflow_path: str,
    artifact_name: str,
    identity_regexp: str,
    issuer: str,
    cosign: str,
) -> tuple[Path, Path]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise EvidenceError("Merge-SHA muss aus exakt 40 kleinen Hexadezimalzeichen bestehen.")
    if repository.count("/") != 1 or not token.strip():
        raise EvidenceError("Repository oder GitHub-Token fehlt.")

    api_base = api_base.rstrip("/")
    repo_path = quote(repository, safe="/")
    run_payload = _api_json(
        f"{api_base}/repos/{repo_path}/actions/runs"
        f"?head_sha={commit_sha}&event=push&branch=main&per_page=100",
        token,
    )
    raw_runs = run_payload.get("workflow_runs")
    if not isinstance(raw_runs, list):
        raise EvidenceError("GitHub-Laufantwort enthält keine workflow_runs-Liste.")
    run = select_main_run(
        [_json_object(item, "Workflowlauf") for item in raw_runs],
        commit_sha=commit_sha,
        workflow_path=workflow_path,
    )

    run_id = int(run["id"])
    artifact_payload = _api_json(
        f"{api_base}/repos/{repo_path}/actions/runs/{run_id}/artifacts"
        f"?name={quote(artifact_name)}&per_page=100",
        token,
    )
    raw_artifacts = artifact_payload.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise EvidenceError("GitHub-Artefaktantwort enthält keine artifacts-Liste.")
    artifact = select_signed_artifact(
        [_json_object(item, "Workflowartefakt") for item in raw_artifacts],
        name=artifact_name,
    )

    with tempfile.TemporaryDirectory(prefix="p3-009-evidence-") as temporary:
        temp_root = Path(temporary)
        archive = temp_root / "signed-release.zip"
        extracted = temp_root / "signed-release"
        _download(
            f"{api_base}/repos/{repo_path}/actions/artifacts/{int(artifact['id'])}/zip",
            token,
            archive,
        )
        archive_digest = _sha256(archive)
        names = safe_extract_archive(archive, extracted)
        manifest, files = inspect_verified_directory(
            extracted,
            identity_regexp=identity_regexp,
            issuer=issuer,
            cosign=cosign,
        )

    evidence = {
        "schemaVersion": 1,
        "status": "verified",
        "generatedUtc": _utc_now(),
        "repository": repository,
        "mainCommitSha": commit_sha,
        "workflowRun": {
            "id": run_id,
            "attempt": int(run.get("run_attempt") or 1),
            "name": run.get("name"),
            "workflowPath": str(run.get("path", "")).split("@", 1)[0],
            "event": run.get("event"),
            "headBranch": run.get("head_branch"),
            "headSha": run.get("head_sha"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "createdAt": run.get("created_at"),
            "updatedAt": run.get("updated_at"),
            "htmlUrl": run.get("html_url"),
        },
        "artifact": {
            "id": int(artifact["id"]),
            "name": artifact.get("name"),
            "sizeInBytes": artifact.get("size_in_bytes"),
            "expired": artifact.get("expired", False),
            "createdAt": artifact.get("created_at"),
            "updatedAt": artifact.get("updated_at"),
            "expiresAt": artifact.get("expires_at"),
            "archiveSha256": archive_digest,
            "fileCount": len(names),
            "files": list(names),
        },
        "verification": {
            "cosignVerified": True,
            "exactFileCount": len(names) == EXPECTED_FILE_COUNT,
            "manifestDigestMatched": True,
            "certificateIdentityRegexp": identity_regexp,
            "oidcIssuer": issuer,
            "manifestCreatedUtc": manifest.get("createdUtc"),
            "manifestSha256": next(
                item["sha256"] for item in files if item["name"] == MANIFEST_NAME
            ),
            "manifestBundleSha256": next(
                item["sha256"] for item in files if item["name"] == MANIFEST_BUNDLE_NAME
            ),
        },
        "files": files,
    }
    return _write_evidence(output_directory, evidence)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Post-merge P3-009-Hauptzweigsignaturen vollständig nachweisen."
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--workflow-path", default=DEFAULT_WORKFLOW_PATH)
    parser.add_argument("--artifact-name", default=DEFAULT_ARTIFACT_NAME)
    parser.add_argument("--identity-regexp", default=DEFAULT_IDENTITY_REGEXP)
    parser.add_argument("--issuer", default=DEFAULT_OIDC_ISSUER)
    parser.add_argument("--cosign", default="cosign")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        json_path, markdown_path = collect_evidence(
            repository=args.repository,
            commit_sha=args.commit_sha,
            token=os.environ.get(args.token_env, ""),
            output_directory=args.output_directory,
            api_base=args.api_base,
            workflow_path=args.workflow_path,
            artifact_name=args.artifact_name,
            identity_regexp=args.identity_regexp,
            issuer=args.issuer,
            cosign=args.cosign,
        )
        print(f"GRÜN: P3-009-Hauptzweignachweis erzeugt: {json_path} und {markdown_path}")
        return 0
    except EvidenceError as exc:
        print(f"ROT: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
