"""Regression tests for the reproducible Debian release candidate builder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.build_deb_release import build_release


@unittest.skipUnless(shutil.which("dpkg-deb") and shutil.which("tar"), "dpkg-deb and tar required")
class ReleaseBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wheelhouse = self.root / "wheelhouse"
        self.wheelhouse.mkdir()
        for name in (
            "PySide6-6.9.2-cp39-abi3-manylinux_2_28_x86_64.whl",
            "PySide6_Addons-6.9.2-cp39-abi3-manylinux_2_28_x86_64.whl",
            "PySide6_Essentials-6.9.2-cp39-abi3-manylinux_2_28_x86_64.whl",
            "shiboken6-6.9.2-cp39-abi3-manylinux_2_28_x86_64.whl",
        ):
            (self.wheelhouse / name).write_bytes((name + "\n").encode("utf-8"))

    def test_two_builds_are_byte_identical(self) -> None:
        first = build_release("0.9.0~rc1", self.wheelhouse, self.root / "first", 1_700_000_000)
        second = build_release("0.9.0~rc1", self.wheelhouse, self.root / "second", 1_700_000_000)
        self.assertEqual(first.build_id, second.build_id)
        self.assertEqual(first.package_sha256, second.package_sha256)
        self.assertEqual(first.bundle_sha256, second.bundle_sha256)
        self.assertEqual(first.package_path.read_bytes(), second.package_path.read_bytes())
        self.assertEqual(first.bundle_path.read_bytes(), second.bundle_path.read_bytes())

    def test_package_metadata_build_info_and_file_manifest_are_consistent(self) -> None:
        result = build_release("0.9.0~rc1", self.wheelhouse, self.root / "out", 1_700_000_000)
        self.assertTrue(result.build_id.startswith("MMTBUILD-0.9.0~rc1-"))
        self.assertEqual(
            "multimodultool2026",
            subprocess.check_output(["dpkg-deb", "-f", result.package_path, "Package"], text=True).strip(),
        )
        self.assertEqual(
            "amd64",
            subprocess.check_output(["dpkg-deb", "-f", result.package_path, "Architecture"], text=True).strip(),
        )
        extract = self.root / "extract"
        subprocess.run(["dpkg-deb", "-x", result.package_path, extract], check=True)
        app_root = extract / "usr/lib/multimodultool2026/app"
        info = json.loads(
            (extract / "usr/lib/multimodultool2026/BUILD_INFO.json").read_text(encoding="utf-8")
        )
        self.assertEqual(result.build_id, info["buildId"])
        self.assertEqual("0.9.0~rc1", info["version"])
        manifest = extract / "usr/lib/multimodultool2026/FILE_MANIFEST.sha256"
        self.assertEqual(result.installed_manifest_sha256, hashlib.sha256(manifest.read_bytes()).hexdigest())
        completed = subprocess.run(
            ["sha256sum", "--quiet", "-c", str(manifest)],
            cwd=extract,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

        layout = json.loads((app_root / "layout-manifest.json").read_text(encoding="utf-8"))
        reference_path = layout["referenceAsset"]["path"]
        self.assertTrue((app_root / reference_path).is_file(), reference_path)
        for relative in layout["validation"]["documentation"]:
            self.assertTrue((app_root / relative).is_file(), relative)

    def test_release_payload_list_contains_manifest_dependencies(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        payload_entries = {
            line.strip()
            for line in (project_root / "release/package-files.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        required_roots = {
            "README.md",
            "AGENTS.md",
            "ANLEITUNG_TOOL.md",
            "CHANGELOG.md",
            "TODO.md",
            "SCHWACHSTELLEN.md",
            "UPGRADE_POOL.md",
            "ENTWICKLERDOKU.md",
            "assets/ui-reference",
            "docs",
            "standards",
            "layout-manifest.json",
            "requirements.txt",
            "src",
        }
        self.assertTrue(required_roots.issubset(payload_entries))

    def test_release_manager_verifies_package_and_rejects_changed_bytes(self) -> None:
        result = build_release("0.9.0~rc1", self.wheelhouse, self.root / "out", 1_700_000_000)
        manager = Path(__file__).resolve().parents[1] / "release/release-manager.sh"
        good = subprocess.run(
            ["bash", str(manager), "verify", str(result.package_path)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, good.returncode, good.stderr)
        changed = self.root / result.package_path.name
        changed.write_bytes(result.package_path.read_bytes() + b"changed")
        changed.with_suffix(changed.suffix + ".sha256").write_text(
            result.package_path.with_suffix(result.package_path.suffix + ".sha256").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        bad = subprocess.run(["bash", str(manager), "verify", str(changed)], text=True, capture_output=True)
        self.assertNotEqual(0, bad.returncode)


if __name__ == "__main__":
    unittest.main()
