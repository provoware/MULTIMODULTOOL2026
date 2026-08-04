"""Failpoint-Matrix für atomare Einstellungszustände."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.settings_manager import (
    BACKUP_FILE_NAME,
    FAILPOINT_NAMES,
    SETTINGS_FILE_NAME,
    FailpointController,
    default_settings,
    load_or_recover_settings,
    validate_settings,
    write_settings,
)


class SettingsFailpointMatrixTests(unittest.TestCase):
    def _run_failpoint(self, name: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config" / "multimodultool2026"
            first = load_or_recover_settings(config)
            self.assertTrue(first.is_valid, first.errors)

            old_data = default_settings()
            new_data = default_settings()
            new_data["ui"]["fontScalePercent"] = 110
            active = config / SETTINGS_FILE_NAME
            self.assertEqual(old_data, json.loads(active.read_text(encoding="utf-8")))

            controller = FailpointController(name)
            result = write_settings(config, new_data, failpoint=controller)

            self.assertFalse(result.is_valid)
            self.assertEqual(name, result.failpoint)
            self.assertIn(name, controller.hits)
            self.assertTrue(active.is_file())
            active_data = json.loads(active.read_text(encoding="utf-8"))
            self.assertTrue(validate_settings(active_data).is_valid)
            self.assertIn(
                active_data["ui"]["fontScalePercent"],
                {old_data["ui"]["fontScalePercent"], new_data["ui"]["fontScalePercent"]},
            )

            backup = config / BACKUP_FILE_NAME
            if backup.exists():
                backup_data = json.loads(backup.read_text(encoding="utf-8"))
                self.assertTrue(validate_settings(backup_data).is_valid)
                self.assertIn(
                    backup_data["ui"]["fontScalePercent"],
                    {old_data["ui"]["fontScalePercent"], new_data["ui"]["fontScalePercent"]},
                )

            self.assertFalse(list(config.glob("*.tmp")))
            self.assertFalse(list(config.glob(".*.tmp")))

    def test_all_declared_failpoints_preserve_old_or_new_complete_state(self) -> None:
        self.assertEqual(
            (
                "before_temp_write",
                "after_temp_write",
                "before_fsync",
                "after_fsync",
                "before_backup",
                "after_backup",
                "before_replace",
                "after_replace",
                "before_postvalidate",
                "after_postvalidate",
            ),
            FAILPOINT_NAMES,
        )
        for name in FAILPOINT_NAMES:
            with self.subTest(failpoint=name):
                self._run_failpoint(name)


if __name__ == "__main__":
    unittest.main()
