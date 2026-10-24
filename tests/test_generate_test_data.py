"""P3-004: deterministische Testbestände ohne Berührung bestehender Daten."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from tools.generate_test_data import FILES, FixtureError, create_fixture


ROOT = Path(__file__).resolve().parents[1]


class ReproducibleFixtureTests(unittest.TestCase):
    def test_two_independent_runs_have_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            left, right = base / "links", base / "rechts"
            self.assertEqual(create_fixture(left), create_fixture(right))
            left_paths = sorted(p.relative_to(left) for p in left.rglob("*") if p.is_file())
            right_paths = sorted(p.relative_to(right) for p in right.rglob("*") if p.is_file())
            self.assertEqual(left_paths, right_paths)
            self.assertEqual(len(FILES) + 1, len(left_paths))
            for relative in left_paths:
                self.assertEqual((left / relative).read_bytes(), (right / relative).read_bytes())

    def test_manifest_contains_only_relative_verified_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "bestand"
            create_fixture(target)
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("MMT-P3-004-v1", manifest["fixtureId"])
            self.assertEqual(sorted(FILES), [item["path"] for item in manifest["files"]])
            for item in manifest["files"]:
                self.assertFalse(Path(item["path"]).is_absolute())
                self.assertNotIn("..", Path(item["path"]).parts)
                payload = (target / item["path"]).read_bytes()
                self.assertEqual(len(payload), item["bytes"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"])
            for first, second in manifest["duplicateGroups"]:
                self.assertEqual((target / first).read_bytes(), (target / second).read_bytes())
            first, second = manifest["collisionNames"]
            self.assertEqual(Path(first).name, Path(second).name)
            self.assertNotEqual((target / first).read_bytes(), (target / second).read_bytes())

    def test_existing_directory_is_not_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "bestand"
            target.mkdir()
            sentinel = target / "wichtige-daten.txt"
            sentinel.write_text("unverändert", encoding="utf-8")
            with self.assertRaises(FixtureError):
                create_fixture(target)
            self.assertEqual("unverändert", sentinel.read_text(encoding="utf-8"))
            self.assertEqual(["wichtige-daten.txt"], [p.name for p in target.iterdir()])

    def test_existing_file_and_dangling_symlink_are_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            file_target = base / "vorhanden"
            file_target.write_bytes(b"original")
            with self.assertRaises(FixtureError):
                create_fixture(file_target)
            self.assertEqual(b"original", file_target.read_bytes())
            link = base / "toter-link"
            link.symlink_to(base / "fehlend")
            with self.assertRaises(FixtureError):
                create_fixture(link)
            self.assertTrue(link.is_symlink())

    def test_symlinked_parent_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            real = base / "echt"
            real.mkdir()
            alias = base / "link"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaises(FixtureError):
                create_fixture(alias / "bestand")
            self.assertEqual([], list(real.iterdir()))

    def test_relative_and_source_tree_paths_are_blocked(self) -> None:
        with self.assertRaises(FixtureError):
            create_fixture(Path("relativer-testbestand"))
        with self.assertRaises(FixtureError):
            create_fixture(ROOT / "niemals-im-quellbaum-erzeugen")

    def test_private_modes_and_no_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "bestand"
            create_fixture(target)
            for item in (target, *target.rglob("*")):
                self.assertFalse(item.is_symlink())
                expected = 0o700 if item.is_dir() else 0o600
                self.assertEqual(expected, stat.S_IMODE(item.stat().st_mode))

    def test_cli_produces_manifest_and_refuses_second_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "bestand"
            command = [sys.executable, str(ROOT / "tools/generate_test_data.py"), "--output", str(target)]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(0, first.returncode, first.stderr)
            before = (target / "manifest.json").read_bytes()
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertNotEqual(0, second.returncode)
            self.assertIn("ROT", second.stderr)
            self.assertEqual(before, (target / "manifest.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
