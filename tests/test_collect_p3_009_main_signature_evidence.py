from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

from tools import collect_p3_009_main_signature_evidence as evidence


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MainSignatureEvidenceTests(unittest.TestCase):
    def test_selects_only_successful_main_push_for_exact_workflow_and_sha(self) -> None:
        sha_value = "a" * 40
        runs = [
            {
                "id": 1,
                "head_sha": sha_value,
                "event": "pull_request",
                "head_branch": "main",
                "path": evidence.DEFAULT_WORKFLOW_PATH,
                "status": "completed",
                "conclusion": "success",
            },
            {
                "id": 2,
                "head_sha": sha_value,
                "event": "push",
                "head_branch": "main",
                "path": evidence.DEFAULT_WORKFLOW_PATH + "@refs/heads/main",
                "status": "completed",
                "conclusion": "failure",
            },
            {
                "id": 3,
                "run_attempt": 2,
                "head_sha": sha_value,
                "event": "push",
                "head_branch": "main",
                "path": evidence.DEFAULT_WORKFLOW_PATH + "@refs/heads/main",
                "status": "completed",
                "conclusion": "success",
            },
        ]
        selected = evidence.select_main_run(
            runs,
            commit_sha=sha_value,
            workflow_path=evidence.DEFAULT_WORKFLOW_PATH,
        )
        self.assertEqual(selected["id"], 3)

    def test_requires_exactly_one_nonexpired_named_artifact(self) -> None:
        selected = evidence.select_signed_artifact(
            [{"id": 7, "name": evidence.DEFAULT_ARTIFACT_NAME, "expired": False}],
            name=evidence.DEFAULT_ARTIFACT_NAME,
        )
        self.assertEqual(selected["id"], 7)
        with self.assertRaises(evidence.EvidenceError):
            evidence.select_signed_artifact(
                [{"id": 7, "name": evidence.DEFAULT_ARTIFACT_NAME, "expired": True}],
                name=evidence.DEFAULT_ARTIFACT_NAME,
            )

    def test_safe_extract_rejects_symlink_and_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                for index in range(13):
                    bundle.writestr(f"file-{index}", b"x")
                info = zipfile.ZipInfo("link")
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                bundle.writestr(info, "target")
            with self.assertRaises(evidence.EvidenceError):
                evidence.safe_extract_archive(archive, root / "out")

    def test_inspection_records_all_14_file_and_bundle_digests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = []
            for index in range(6):
                name = f"artifact-{index}_save_.bin"
                subject = root / name
                subject.write_bytes(f"payload-{index}".encode())
                bundle_name = name + evidence.BUNDLE_SUFFIX
                (root / bundle_name).write_text(
                    json.dumps({"bundle": index}) + "\n",
                    encoding="utf-8",
                )
                artifacts.append(
                    {
                        "file": name,
                        "sha256": sha(subject),
                        "size": subject.stat().st_size,
                        "bundle": bundle_name,
                    }
                )
            manifest = {
                "status": "signed-release",
                "oidcIssuer": evidence.DEFAULT_OIDC_ISSUER,
                "certificateIdentityRegexp": evidence.DEFAULT_IDENTITY_REGEXP,
                "createdUtc": "2026-08-05T02:10:00Z",
                "artifacts": artifacts,
            }
            (root / evidence.MANIFEST_NAME).write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            (root / evidence.MANIFEST_BUNDLE_NAME).write_text(
                '{"bundle": "manifest"}\n',
                encoding="utf-8",
            )
            with mock.patch.object(evidence, "verify_signed_release") as verify:
                loaded, files = evidence.inspect_verified_directory(
                    root,
                    identity_regexp=evidence.DEFAULT_IDENTITY_REGEXP,
                    issuer=evidence.DEFAULT_OIDC_ISSUER,
                    cosign="cosign",
                )
            verify.assert_called_once()
            self.assertEqual(loaded["status"], "signed-release")
            self.assertEqual(len(files), 14)
            self.assertTrue(
                all(evidence.SHA256_PATTERN.fullmatch(item["sha256"]) for item in files)
            )
            self.assertEqual(
                sum(item["role"] == "primary-signature-bundle" for item in files),
                6,
            )


if __name__ == "__main__":
    unittest.main()
