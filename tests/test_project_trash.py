from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from src.error_events import SafeOperationError
from src.project_trash import (
    PRIVATE_FILE_MODE,
    create_transaction_id,
    execute_trash_move,
    inspect_transaction,
    preview_trash_move,
    restore_transaction,
    trash_paths,
)


class ProjectTrashTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir(mode=0o700)
        os.chmod(self.project, 0o700)

    def source(self, name: str = "data.txt", content: str = "payload") -> Path:
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_preview_is_read_only_and_contains_unique_transaction(self) -> None:
        source = self.source()
        before = sorted(item.relative_to(self.project) for item in self.project.rglob("*"))
        preview = preview_trash_move(self.project, source)
        after = sorted(item.relative_to(self.project) for item in self.project.rglob("*"))
        self.assertEqual(before, after)
        self.assertTrue(preview.transaction_id.startswith("MMTTRASH-"))
        self.assertEqual("data.txt", preview.original_relative_path)
        self.assertFalse(preview.transaction_directory.exists())

    def test_move_is_atomic_private_manifested_and_restorable(self) -> None:
        source = self.source("folder/data.txt", "important")
        preview = preview_trash_move(self.project, source)
        result = execute_trash_move(preview)
        self.assertEqual("trashed", result.state)
        self.assertFalse(source.exists())
        self.assertEqual("important", result.payload_path.read_text(encoding="utf-8"))
        self.assertEqual(0o600, stat.S_IMODE(result.manifest_path.stat().st_mode))
        manifest = inspect_transaction(self.project, preview.transaction_id)
        self.assertEqual("trashed", manifest.state)
        self.assertEqual("folder/data.txt", manifest.original_relative_path)

        restored = restore_transaction(self.project, preview.transaction_id)
        self.assertEqual("restored", restored.state)
        self.assertEqual("important", source.read_text(encoding="utf-8"))
        self.assertFalse(result.payload_path.exists())
        self.assertEqual("restored", inspect_transaction(self.project, preview.transaction_id).state)

    def test_changed_source_after_preview_is_blocked(self) -> None:
        source = self.source(content="before")
        preview = preview_trash_move(self.project, source)
        source.write_text("after", encoding="utf-8")
        with self.assertRaises(SafeOperationError):
            execute_trash_move(preview)
        self.assertEqual("after", source.read_text(encoding="utf-8"))
        self.assertFalse(preview.transaction_directory.exists())

    def test_source_outside_project_is_blocked(self) -> None:
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("x", encoding="utf-8")
        with self.assertRaises(SafeOperationError):
            preview_trash_move(self.project, outside)
        self.assertTrue(outside.exists())

    def test_symlink_source_is_blocked_without_touching_target(self) -> None:
        target = self.source("target.txt", "safe")
        link = self.project / "link.txt"
        link.symlink_to(target)
        with self.assertRaises(SafeOperationError):
            preview_trash_move(self.project, link)
        self.assertEqual("safe", target.read_text(encoding="utf-8"))
        self.assertTrue(link.is_symlink())

    def test_hardlinked_file_is_blocked(self) -> None:
        source = self.source("one.txt", "same")
        second = self.project / "two.txt"
        os.link(source, second)
        with self.assertRaises(SafeOperationError):
            preview_trash_move(self.project, source)
        self.assertTrue(source.exists())
        self.assertTrue(second.exists())

    def test_cross_device_source_is_blocked(self) -> None:
        source = self.source()
        real_ismount = os.path.ismount

        def fake_ismount(path) -> bool:
            return Path(path) == source or real_ismount(path)

        with mock.patch("src.project_trash.os.path.ismount", side_effect=fake_ismount):
            with self.assertRaises(SafeOperationError):
                preview_trash_move(self.project, source)
        self.assertTrue(source.exists())

    def test_insufficient_free_space_is_blocked_without_creation(self) -> None:
        source = self.source()
        with mock.patch("src.project_trash.shutil.disk_usage") as usage:
            usage.return_value = type("Usage", (), {"free": 1})()
            with self.assertRaises(SafeOperationError):
                preview_trash_move(self.project, source)
        self.assertTrue(source.exists())
        self.assertFalse(trash_paths(self.project).control_directory.exists())

    def test_restore_name_conflict_is_blocked(self) -> None:
        source = self.source(content="original")
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        source.write_text("conflict", encoding="utf-8")
        with self.assertRaises(SafeOperationError):
            restore_transaction(self.project, preview.transaction_id)
        self.assertEqual("conflict", source.read_text(encoding="utf-8"))
        self.assertTrue(preview.payload_path.exists())

    def test_corrupt_manifest_blocks_restore_without_payload_change(self) -> None:
        source = self.source(content="original")
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        payload_before = preview.payload_path.read_bytes()
        preview.manifest_path.write_text("{broken", encoding="utf-8")
        os.chmod(preview.manifest_path, PRIVATE_FILE_MODE)
        with self.assertRaises(SafeOperationError):
            restore_transaction(self.project, preview.transaction_id)
        self.assertEqual(payload_before, preview.payload_path.read_bytes())
        self.assertFalse(source.exists())

    def test_prepared_manifest_with_payload_recovers(self) -> None:
        source = self.source(content="recover")
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        value = json.loads(preview.manifest_path.read_text(encoding="utf-8"))
        value["state"] = "prepared"
        value["completedUtc"] = ""
        preview.manifest_path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(preview.manifest_path, PRIVATE_FILE_MODE)
        restored = restore_transaction(self.project, preview.transaction_id)
        self.assertTrue(restored.recovered_prepared_state)
        self.assertEqual("recover", source.read_text(encoding="utf-8"))

    def test_directory_is_moved_as_one_object_and_restored(self) -> None:
        folder = self.project / "album"
        folder.mkdir()
        (folder / "track.txt").write_text("audio", encoding="utf-8")
        preview = preview_trash_move(self.project, folder)
        execute_trash_move(preview)
        self.assertFalse(folder.exists())
        self.assertEqual("audio", (preview.payload_path / "track.txt").read_text(encoding="utf-8"))
        restore_transaction(self.project, preview.transaction_id)
        self.assertEqual("audio", (folder / "track.txt").read_text(encoding="utf-8"))

    def test_private_trash_directories_use_0700(self) -> None:
        source = self.source()
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        paths = trash_paths(self.project)
        for directory in (
            paths.control_directory,
            paths.trash_root,
            paths.transactions_root,
            preview.transaction_directory,
        ):
            self.assertEqual(0o700, stat.S_IMODE(directory.stat().st_mode))

    def test_atomic_replace_failure_keeps_source_and_cleans_empty_transaction(self) -> None:
        source = self.source(content="unchanged")
        preview = preview_trash_move(self.project, source)
        real_replace = os.replace

        def fail_payload_replace(source_arg, target_arg):
            if Path(source_arg) == source and Path(target_arg) == preview.payload_path:
                raise OSError("simulierter rename-Fehler")
            return real_replace(source_arg, target_arg)

        with mock.patch("src.project_trash.os.replace", side_effect=fail_payload_replace):
            with self.assertRaises(SafeOperationError):
                execute_trash_move(preview)
        self.assertEqual("unchanged", source.read_text(encoding="utf-8"))
        self.assertFalse(preview.transaction_directory.exists())

    def test_missing_manifest_blocks_restore_and_keeps_payload(self) -> None:
        source = self.source(content="payload")
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        preview.manifest_path.unlink()
        with self.assertRaises(SafeOperationError):
            restore_transaction(self.project, preview.transaction_id)
        self.assertTrue(preview.payload_path.exists())
        self.assertFalse(source.exists())

    def test_modified_payload_blocks_restore(self) -> None:
        source = self.source(content="original")
        preview = preview_trash_move(self.project, source)
        execute_trash_move(preview)
        preview.payload_path.write_text("changed", encoding="utf-8")
        with self.assertRaises(SafeOperationError):
            restore_transaction(self.project, preview.transaction_id)
        self.assertEqual("changed", preview.payload_path.read_text(encoding="utf-8"))
        self.assertFalse(source.exists())

    def test_transaction_id_format(self) -> None:
        value = create_transaction_id()
        self.assertRegex(value, r"^MMTTRASH-\d{8}T\d{6}-[A-F0-9]{12}$")


if __name__ == "__main__":
    unittest.main()
