"""Regression: Der Startassistent muss Verzeichnis-Scans explizit schließen."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from src.start_assistant import MODE_READ_ONLY, validate_start_selection


class StartSelectionScandirTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Projekt"
        self.target = self.root / "Sortiert"
        self.root.mkdir()
        self.target.mkdir()
        (self.root / "Quelle.txt").write_text("Quelle", encoding="utf-8")

    def test_close_on_empty_and_nonempty_target(self):
        real_scandir = os.scandir

        class TrackedScan:
            closed = False
            def __init__(self, path):
                self.iterator = real_scandir(path)
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                self.closed = True
                self.iterator.close()
            def __next__(self):
                return next(self.iterator)

        for occupied in (False, True):
            with self.subTest(occupied=occupied):
                if occupied:
                    (self.target / "vorhanden.txt").write_text("X", encoding="utf-8")
                instances = []
                def wrapped(path):
                    if Path(path) == self.target:
                        obj = TrackedScan(path)
                        instances.append(obj)
                        return obj
                    return real_scandir(path)
                with mock.patch("src.start_assistant.os.scandir", side_effect=wrapped):
                    selection = validate_start_selection(self.root, self.target, MODE_READ_ONLY)
                self.assertEqual(selection.target_is_empty, not occupied)
                self.assertEqual(len(instances), 1)
                self.assertTrue(instances[0].closed)

    def test_close_after_scan_error(self):
        real_scandir = os.scandir

        class FailingScan:
            closed = False
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                self.closed = True
            def __next__(self):
                raise OSError("Simulierter Lesefehler")

        scan = FailingScan()
        def wrapped(path):
            return scan if Path(path) == self.target else real_scandir(path)
        with mock.patch("src.start_assistant.os.scandir", side_effect=wrapped):
            with self.assertRaisesRegex(Exception, "Zielinhalt"):
                validate_start_selection(self.root, self.target, MODE_READ_ONLY)
        self.assertTrue(scan.closed)


if __name__ == "__main__":
    unittest.main()
