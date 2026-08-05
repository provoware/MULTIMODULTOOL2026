"""Tests for P1-001 guided project, target and safety-mode validation."""
from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

from src.start_assistant import (
    MODE_PREVIEW_REPORT,
    MODE_PRODUCTIVE,
    MODE_READ_ONLY,
    revalidate_start_selection,
    validate_start_selection,
)


class StartAssistantValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.target = self.root / "Sortiert"
        self.root.mkdir()
        self.target.mkdir()
        (self.root / "source.txt").write_text("source", encoding="utf-8")

    def test_productive_selection_binds_project_target_and_mode_without_writes(self) -> None:
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        selection = validate_start_selection(self.root, self.target, MODE_PRODUCTIVE)
        after = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))

        self.assertEqual(before, after)
        self.assertFalse((self.root / ".multimodultool2026").exists())
        self.assertEqual(self.root, selection.project.root)
        self.assertEqual(self.target, selection.target_root)
        self.assertEqual("Sortiert", selection.target_relative)
        self.assertTrue(selection.allows_report)
        self.assertTrue(selection.allows_write)
        self.assertIn("GRÜN: Startauswahl vollständig vorvalidiert", selection.summary)
        self.assertIn("zweiten ausdrücklichen Bestätigung", selection.summary)

    def test_read_only_mode_blocks_report_and_file_writes(self) -> None:
        selection = validate_start_selection(self.root, self.target, MODE_READ_ONLY)
        self.assertFalse(selection.allows_report)
        self.assertFalse(selection.allows_write)
        self.assertIn("Dateiänderungen gesperrt", selection.summary)
        self.assertIn("Berichtsschreibzugriffe gesperrt", selection.summary)

    def test_preview_report_mode_allows_only_private_reports(self) -> None:
        selection = validate_start_selection(self.root, self.target, MODE_PREVIEW_REPORT)
        self.assertTrue(selection.allows_report)
        self.assertFalse(selection.allows_write)
        self.assertIn("Vorschau und Bericht", selection.summary)

    def test_project_and_target_must_be_distinct(self) -> None:
        with self.assertRaisesRegex(Exception, "getrennt"):
            validate_start_selection(self.root, self.root, MODE_PRODUCTIVE)

    def test_target_outside_project_is_blocked(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        with self.assertRaisesRegex(Exception, "innerhalb"):
            validate_start_selection(self.root, outside, MODE_PRODUCTIVE)

    def test_control_directory_is_never_a_target(self) -> None:
        control = self.root / ".multimodultool2026"
        control.mkdir()
        with self.assertRaisesRegex(Exception, "Steuerordner"):
            validate_start_selection(self.root, control, MODE_PRODUCTIVE)

    def test_symlink_component_is_blocked(self) -> None:
        real = self.root / "real-target"
        real.mkdir()
        linked = self.root / "linked-target"
        os.symlink(real, linked)
        with self.assertRaisesRegex(Exception, "Symbolische"):
            validate_start_selection(self.root, linked, MODE_PRODUCTIVE)

    def test_unknown_safety_mode_is_blocked(self) -> None:
        with self.assertRaisesRegex(Exception, "Unbekannter"):
            validate_start_selection(self.root, self.target, "unsafe")

    def test_revalidation_detects_replaced_target_directory(self) -> None:
        selection = validate_start_selection(self.root, self.target, MODE_PRODUCTIVE)
        old_target = self.root / "Sortiert.alt"
        self.target.rename(old_target)
        self.target.mkdir()
        with self.assertRaisesRegex(Exception, "ersetzt"):
            revalidate_start_selection(selection)


if __name__ == "__main__":
    unittest.main()
