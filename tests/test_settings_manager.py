"""Regressionstests für versionierte, transaktionale Einstellungen."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from src.settings_manager import (
    BACKUP_FILE_NAME,
    FILE_MODE,
    SCHEMA_VERSION,
    SETTINGS_FILE_NAME,
    default_settings,
    inspect_settings,
    load_or_recover_settings,
    read_settings,
    settings_paths,
    validate_settings,
    validate_settings_paths,
    write_settings,
)


class SettingsValidationTests(unittest.TestCase):
    def test_defaults_are_valid_and_independent(self) -> None:
        first = default_settings()
        second = default_settings()
        self.assertTrue(validate_settings(first).is_valid)
        first["ui"]["fontScalePercent"] = 110
        self.assertEqual(100, second["ui"]["fontScalePercent"])

    def test_unknown_field_is_rejected(self) -> None:
        data = default_settings()
        data["unexpected"] = True
        result = validate_settings(data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("unbekannte Felder" in item for item in result.errors))

    def test_unknown_schema_version_is_rejected(self) -> None:
        data = default_settings()
        data["schemaVersion"] = SCHEMA_VERSION + 1
        result = validate_settings(data)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("nicht unterstützt" in item for item in result.errors))

    def test_types_ranges_and_safety_defaults_are_enforced(self) -> None:
        data = default_settings()
        data["ui"]["fontScalePercent"] = 250
        data["safety"]["defaultDryRun"] = False
        data["workflow"]["showAdvancedOptions"] = "yes"
        result = validate_settings(data)
        self.assertFalse(result.is_valid)
        joined = "\n".join(result.errors)
        self.assertIn("zwischen 80 und 200", joined)
        self.assertIn("muss im aktuellen Entwicklungsstand true bleiben", joined)
        self.assertIn("muss true oder false sein", joined)


class SettingsTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / "config" / "multimodultool2026"

    def test_read_only_inspection_does_not_create_files(self) -> None:
        result = inspect_settings(self.config)
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual("defaults-preview", result.source)
        self.assertFalse(self.config.exists())

    def test_read_only_inspection_reports_recovery_without_writing(self) -> None:
        self.assertTrue(load_or_recover_settings(self.config).is_valid)
        changed = default_settings()
        changed["ui"]["fontScalePercent"] = 110
        self.assertTrue(write_settings(self.config, changed).is_valid)
        active = self.config / SETTINGS_FILE_NAME
        active.write_text("{ invalid", encoding="utf-8")
        os.chmod(active, FILE_MODE)
        before = {item.name: item.read_bytes() for item in self.config.iterdir()}

        result = inspect_settings(self.config)

        self.assertTrue(result.is_valid)
        self.assertEqual("backup-preview", result.source)
        after = {item.name: item.read_bytes() for item in self.config.iterdir()}
        self.assertEqual(before, after)

    def test_first_start_creates_private_valid_settings(self) -> None:
        result = load_or_recover_settings(self.config)
        self.assertTrue(result.is_valid, result.errors)
        self.assertTrue(result.created)
        active = self.config / SETTINGS_FILE_NAME
        self.assertTrue(active.is_file())
        self.assertEqual(FILE_MODE, stat.S_IMODE(active.stat().st_mode))
        self.assertTrue(read_settings(self.config).is_valid)
        self.assertFalse(list(self.config.glob("*.tmp")))

    def test_save_creates_last_valid_backup_and_replaces_atomically(self) -> None:
        first = load_or_recover_settings(self.config)
        self.assertTrue(first.is_valid)
        updated = default_settings()
        updated["ui"]["fontScalePercent"] = 110
        result = write_settings(self.config, updated)
        self.assertTrue(result.is_valid, result.errors)

        active = json.loads((self.config / SETTINGS_FILE_NAME).read_text())
        backup = json.loads((self.config / BACKUP_FILE_NAME).read_text())
        self.assertEqual(110, active["ui"]["fontScalePercent"])
        self.assertEqual(100, backup["ui"]["fontScalePercent"])
        self.assertEqual(FILE_MODE, stat.S_IMODE((self.config / BACKUP_FILE_NAME).stat().st_mode))
        self.assertFalse(list(self.config.glob("*.tmp")))

    def test_invalid_new_data_never_changes_current_file(self) -> None:
        self.assertTrue(load_or_recover_settings(self.config).is_valid)
        active = self.config / SETTINGS_FILE_NAME
        before = active.read_bytes()
        invalid = default_settings()
        invalid["schemaVersion"] = 999
        result = write_settings(self.config, invalid)
        self.assertFalse(result.is_valid)
        self.assertEqual(before, active.read_bytes())
        self.assertFalse((self.config / BACKUP_FILE_NAME).exists())

    def test_corrupt_active_file_rolls_back_to_last_valid_backup(self) -> None:
        self.assertTrue(load_or_recover_settings(self.config).is_valid)
        changed = default_settings()
        changed["ui"]["fontScalePercent"] = 110
        self.assertTrue(write_settings(self.config, changed).is_valid)

        active = self.config / SETTINGS_FILE_NAME
        active.write_text("{ broken", encoding="utf-8")
        os.chmod(active, FILE_MODE)

        result = load_or_recover_settings(self.config)
        self.assertTrue(result.is_valid, result.errors)
        self.assertTrue(result.recovered)
        self.assertEqual("backup", result.source)
        self.assertEqual(100, result.settings["ui"]["fontScalePercent"])
        self.assertIsNotNone(result.quarantined)
        self.assertTrue(result.quarantined.is_file())
        self.assertTrue(read_settings(self.config).is_valid)

    def test_corrupt_active_without_backup_uses_safe_defaults(self) -> None:
        self.config.mkdir(parents=True)
        active = self.config / SETTINGS_FILE_NAME
        active.write_text("not-json", encoding="utf-8")
        os.chmod(active, FILE_MODE)

        result = load_or_recover_settings(self.config)
        self.assertTrue(result.is_valid, result.errors)
        self.assertTrue(result.recovered)
        self.assertEqual("defaults", result.source)
        self.assertEqual(default_settings(), result.settings)
        self.assertTrue(read_settings(self.config).is_valid)

    def test_symlinked_configuration_directory_is_blocked(self) -> None:
        real = Path(self.temp.name) / "real-config"
        real.mkdir()
        self.config.parent.mkdir(parents=True)
        self.config.symlink_to(real, target_is_directory=True)
        result = load_or_recover_settings(self.config)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Konfigurationsverzeichnis darf kein Symlink" in item for item in result.errors))
        self.assertEqual([], list(real.iterdir()))

    def test_symlink_is_blocked_without_following_target(self) -> None:
        self.config.mkdir(parents=True)
        outside = Path(self.temp.name) / "outside.json"
        outside.write_text(json.dumps(default_settings()), encoding="utf-8")
        os.chmod(outside, FILE_MODE)
        (self.config / SETTINGS_FILE_NAME).symlink_to(outside)

        result = load_or_recover_settings(self.config)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Symbolischer Link" in item for item in result.errors))
        self.assertEqual(json.dumps(default_settings()), outside.read_text(encoding="utf-8"))

    def test_overly_open_permissions_are_blocked(self) -> None:
        self.config.mkdir(parents=True)
        active = self.config / SETTINGS_FILE_NAME
        active.write_text(json.dumps(default_settings()), encoding="utf-8")
        os.chmod(active, 0o644)
        errors = validate_settings_paths(settings_paths(self.config))
        self.assertTrue(any("0600" in item for item in errors))

    def test_replace_failure_keeps_previous_active_file(self) -> None:
        self.assertTrue(load_or_recover_settings(self.config).is_valid)
        active = self.config / SETTINGS_FILE_NAME
        before = active.read_bytes()
        updated = default_settings()
        updated["ui"]["fontScalePercent"] = 110

        original_replace = os.replace

        def fail_active(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
            if Path(destination) == active:
                raise OSError("simulierter Austauschfehler")
            original_replace(source, destination)

        with mock.patch("src.settings_manager.os.replace", side_effect=fail_active):
            result = write_settings(self.config, updated)

        self.assertFalse(result.is_valid)
        self.assertEqual(before, active.read_bytes())
        self.assertFalse(list(self.config.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
