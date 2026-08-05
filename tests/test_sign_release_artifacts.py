from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.sign_release_artifacts import (
    BUNDLE_SUFFIX,
    MANIFEST_BUNDLE_NAME,
    SigningContractError,
    create_signed_manifest,
    primary_subjects,
    verify_signed_release,
)


class SignedReleaseContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "release"
        self.root.mkdir()
        self.names = (
            "multimodultool2026_0.9.0~rc1_amd64_save_.deb",
            "multimodultool2026_0.9.0~rc1_amd64_save_.deb.sha256",
            "multimodultool2026-0.9.0~rc1-amd64_save_.tar.gz",
            "release-manager_save_.sh",
            "CANDIDATE_BUILD_RESULT_save_.json",
            "RELEASE_STATUS_save_.json",
        )
        for index, name in enumerate(self.names):
            (self.root / name).write_bytes(f"artifact-{index}".encode())
            (self.root / (name + BUNDLE_SUFFIX)).write_text(
                json.dumps({"mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.3"}),
                encoding="utf-8",
            )
        self.identity = r"^https://github.com/provoware/MULTIMODULTOOL2026/.github/workflows/release-candidate.yml@refs/(heads/main|tags/v.*)$"
        self.issuer = "https://token.actions.githubusercontent.com"

    def _fake_cosign(self) -> Path:
        path = Path(self.temp.name) / "cosign"
        path.write_text("#!/bin/sh\n[ \"$1\" = verify-blob ] || exit 9\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
        return path

    def test_exactly_six_primary_subjects_are_selected(self) -> None:
        expected = tuple(sorted(self.names, key=str.casefold))
        self.assertEqual(expected, tuple(path.name for path in primary_subjects(self.root)))

    def test_manifest_contains_only_relative_files_and_digests(self) -> None:
        manifest_path = create_signed_manifest(
            self.root,
            identity_regexp=self.identity,
            issuer=self.issuer,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("signed-release", manifest["status"])
        self.assertFalse(manifest["sourcePrivateKeyStored"])
        self.assertEqual(6, len(manifest["artifacts"]))
        self.assertNotIn(str(self.root), manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["artifacts"]:
            self.assertEqual(64, len(entry["sha256"]))
            self.assertFalse(Path(entry["file"]).is_absolute())

    def test_all_primary_and_manifest_bundles_are_verified(self) -> None:
        create_signed_manifest(self.root, identity_regexp=self.identity, issuer=self.issuer)
        (self.root / MANIFEST_BUNDLE_NAME).write_text(json.dumps({"bundle": True}), encoding="utf-8")
        verify_signed_release(
            self.root,
            identity_regexp=self.identity,
            issuer=self.issuer,
            cosign=str(self._fake_cosign()),
        )

    def test_changed_primary_after_manifest_is_blocked(self) -> None:
        create_signed_manifest(self.root, identity_regexp=self.identity, issuer=self.issuer)
        (self.root / MANIFEST_BUNDLE_NAME).write_text(json.dumps({"bundle": True}), encoding="utf-8")
        (self.root / self.names[0]).write_bytes(b"changed")
        with self.assertRaises(SigningContractError):
            verify_signed_release(
                self.root,
                identity_regexp=self.identity,
                issuer=self.issuer,
                cosign=str(self._fake_cosign()),
            )

    def test_symlinked_subject_is_blocked(self) -> None:
        victim = self.root / self.names[0]
        target = Path(self.temp.name) / "outside"
        target.write_bytes(victim.read_bytes())
        victim.unlink()
        os.symlink(target, victim)
        with self.assertRaises(SigningContractError):
            primary_subjects(self.root)

    def test_unsigned_or_extra_file_is_blocked(self) -> None:
        (self.root / "debug.log").write_text("not release", encoding="utf-8")
        with self.assertRaises(SigningContractError):
            primary_subjects(self.root)


if __name__ == "__main__":
    unittest.main()
