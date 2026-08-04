"""Regressionsprüfungen für Linux-, Manifest- und Repository-Vertrag."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.main import is_supported_platform
from src.manifest_validator import EXPECTED_ZONE_IDS, validate_manifest
from tools import validate_repository


class PlatformContractTests(unittest.TestCase):
    def test_linux_is_supported(self) -> None:
        self.assertTrue(is_supported_platform("linux"))
        self.assertTrue(is_supported_platform("linux2"))

    def test_non_linux_platforms_are_blocked(self) -> None:
        for platform_name in ("win32", "darwin", "cygwin", "ios", "android"):
            with self.subTest(platform=platform_name):
                self.assertFalse(is_supported_platform(platform_name))


class ManifestValidatorTests(unittest.TestCase):
    def test_current_manifest_is_valid(self) -> None:
        result = validate_manifest(ROOT / "layout-manifest.json", ROOT)
        self.assertTrue(result.is_valid, "\n".join(result.errors))

    def test_zone_contract_is_complete(self) -> None:
        result = validate_manifest(ROOT / "layout-manifest.json", ROOT)
        self.assertIsNotNone(result.data)
        zone_ids = tuple(zone["id"] for zone in result.data["zones"])
        self.assertEqual(EXPECTED_ZONE_IDS, zone_ids)

    def test_platform_contract_is_linux_only(self) -> None:
        result = validate_manifest(ROOT / "layout-manifest.json", ROOT)
        self.assertIsNotNone(result.data)
        policy = result.data["platformPolicy"]
        self.assertEqual(["linux"], policy["supportedOperatingSystems"])
        self.assertFalse(policy["browserOrPwaTarget"])
        self.assertFalse(policy["crossPlatformCompatibilityIsGoal"])

    def test_invalid_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            reference = temp_root / "reference.webp"
            reference.write_bytes(b"test")
            invalid = {
                "schemaVersion": "1.1.0",
                "project": {"name": "FALSCH"},
                "platformPolicy": {"supportedOperatingSystems": ["windows"]},
                "referenceAsset": {"path": "reference.webp"},
                "zones": [],
                "validation": {},
                "iterationPolicy": {},
                "preservationPolicy": {},
            }
            path = temp_root / "layout-manifest.json"
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = validate_manifest(path, temp_root)
            self.assertFalse(result.is_valid)
            self.assertGreater(len(result.errors), 5)


class RepositoryContractTests(unittest.TestCase):
    def test_progress_uses_todo_checkbox_counts_without_fixed_baseline(self) -> None:
        contents = {
            "TODO.md": "- [x] erledigt\n- [ ] offen\n",
            "README.md": (
                "Entwicklungsfortschritt: 50 %\n"
                "Erledigte Punkte: 1\nOffene Punkte: 1\nGesamtpunkte: 2\n"
            ),
            "src/main.py": (
                "DEVELOPMENT_PROGRESS = 50\n"
                "COMPLETED_POINTS = 1\nOPEN_POINTS = 1\n"
            ),
        }
        errors: list[str] = []

        with mock.patch.object(
            validate_repository,
            "text",
            side_effect=lambda path, _errors: contents[path],
        ):
            validate_repository.check_progress(errors)

        self.assertEqual([], errors)

    def test_repository_validator_passes(self) -> None:
        process = subprocess.run(
            [sys.executable, "tools/validate_repository.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
