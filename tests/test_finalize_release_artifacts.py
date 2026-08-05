"""Tests for atomic `_save_` release artifact finalization."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools.finalize_release_artifacts import SAVE_SUFFIX, finalize_release


class FinalizeReleaseArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.output = self.root / "ready"
        self.source.mkdir()
        self.package_name = "multimodultool2026_0.9.0~rc1_amd64.deb"
        self.bundle_name = "multimodultool2026-0.9.0~rc1-amd64.tar.gz"
        package = self.source / self.package_name
        bundle = self.source / self.bundle_name
        package.write_bytes(b"candidate-package\n")
        bundle.write_bytes(b"candidate-bundle\n")
        self.package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
        self.source_bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
        (self.source / f"{self.package_name}.sha256").write_text(
            f"{self.package_sha}  {self.package_name}\n",
            encoding="utf-8",
        )
        manager = self.source / "release-manager.sh"
        manager.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        os.chmod(manager, 0o755)
        (self.source / "CANDIDATE_BUILD_RESULT.json").write_text(
            json.dumps(
                {
                    "version": "0.9.0~rc1",
                    "buildId": "MMTBUILD-0.9.0~rc1-0123456789abcdef",
                    "package": f"dist/candidate-a/{self.package_name}",
                    "packageSha256": self.package_sha,
                    "bundle": f"dist/candidate-a/{self.bundle_name}",
                    "bundleSha256": self.source_bundle_sha,
                    "installedManifestSha256": "f" * 64,
                }
            ),
            encoding="utf-8",
        )
        self.policy = self.root / "release-status.json"
        self.policy.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "releaseSuffix": SAVE_SUFFIX,
                    "sourceRenameForbidden": True,
                    "testOnlyArtifacts": ["baseline package"],
                    "unfinished": ["guided project selection"],
                }
            ),
            encoding="utf-8",
        )

    def test_every_final_file_contains_save_suffix_and_hashes_remain_valid(self) -> None:
        manifest = finalize_release(self.source, self.output, self.policy)
        names = sorted(path.name for path in self.output.iterdir())
        self.assertEqual(6, len(names))
        self.assertTrue(all(SAVE_SUFFIX in name for name in names))
        self.assertIn("multimodultool2026_0.9.0~rc1_amd64_save_.deb", names)
        self.assertIn("multimodultool2026_0.9.0~rc1_amd64_save_.deb.sha256", names)
        self.assertIn("multimodultool2026-0.9.0~rc1-amd64_save_.tar.gz", names)
        sidecar = self.output / "multimodultool2026_0.9.0~rc1_amd64_save_.deb.sha256"
        expected_sha, expected_name = sidecar.read_text(encoding="utf-8").split()
        self.assertEqual("multimodultool2026_0.9.0~rc1_amd64_save_.deb", expected_name)
        self.assertEqual(
            expected_sha,
            hashlib.sha256((self.output / expected_name).read_bytes()).hexdigest(),
        )
        self.assertEqual("release-ready", manifest["status"])
        normalized = json.loads(
            (self.output / "CANDIDATE_BUILD_RESULT_save_.json").read_text(encoding="utf-8")
        )
        self.assertEqual("ready-after-green-kubuntu-matrix", normalized["releaseStatus"])
        self.assertEqual(self.source_bundle_sha, normalized["sourceBundleSha256"])
        final_bundle = self.output / normalized["bundle"]
        self.assertEqual(
            hashlib.sha256(final_bundle.read_bytes()).hexdigest(),
            normalized["bundleSha256"],
        )

    def test_final_bundle_is_deterministic_and_internal_files_are_suffixed(self) -> None:
        finalize_release(self.source, self.output, self.policy)
        bundle = self.output / "multimodultool2026-0.9.0~rc1-amd64_save_.tar.gz"
        first_bytes = bundle.read_bytes()
        with tarfile.open(bundle, "r:gz") as archive:
            members = archive.getmembers()
        self.assertTrue(members)
        self.assertTrue(all(SAVE_SUFFIX in Path(member.name).parts[0] for member in members))
        regular_names = [Path(member.name).name for member in members if member.isfile()]
        self.assertEqual(4, len(regular_names))
        self.assertTrue(all(SAVE_SUFFIX in name for name in regular_names))
        self.assertIn("INSTALLIEREN_save_.txt", regular_names)

        finalize_release(self.source, self.output, self.policy)
        self.assertEqual(first_bytes, bundle.read_bytes())

    def test_existing_generated_output_is_replaced_without_stale_files(self) -> None:
        self.output.mkdir()
        (self.output / "obsolete_save_.txt").write_text("obsolete", encoding="utf-8")
        finalize_release(self.source, self.output, self.policy)
        self.assertFalse((self.output / "obsolete_save_.txt").exists())
        self.assertFalse((self.root / ".ready.previous").exists())

    def test_symlinked_required_artifact_is_blocked(self) -> None:
        manager = self.source / "release-manager.sh"
        manager.unlink()
        target = self.root / "external-manager.sh"
        target.write_text("#!/bin/sh\n", encoding="utf-8")
        manager.symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, "missing or unsafe"):
            finalize_release(self.source, self.output, self.policy)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
