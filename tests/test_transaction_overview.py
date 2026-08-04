"""Read-only transaction overview regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from src.project_trash import execute_trash_move, preview_trash_move, restore_transaction, trash_paths
from src.transaction_overview import read_transaction_overview


class TransactionOverviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def create_transaction(self, name: str, *, restore: bool = False) -> str:
        source = self.root / name
        source.write_text(name, encoding="utf-8")
        preview = preview_trash_move(self.root, source)
        execute_trash_move(preview)
        paths = trash_paths(self.root)
        for directory in (
            paths.control_directory,
            paths.trash_root,
            paths.transactions_root,
            paths.transactions_root / preview.transaction_id,
        ):
            os.chmod(directory, 0o700)
        if restore:
            restore_transaction(self.root, preview.transaction_id)
        return preview.transaction_id

    def test_missing_transaction_root_is_empty_and_not_created(self) -> None:
        before = tuple(self.root.iterdir())
        snapshot = read_transaction_overview(self.root)
        self.assertEqual((), snapshot.entries)
        self.assertEqual(before, tuple(self.root.iterdir()))
        self.assertFalse(trash_paths(self.root).transactions_root.exists())

    def test_lists_trashed_restored_prepared_and_damaged_without_mutation(self) -> None:
        trashed = self.create_transaction("trashed.txt")
        restored = self.create_transaction("restored.txt", restore=True)
        prepared = self.create_transaction("prepared.txt")
        prepared_manifest = trash_paths(self.root).transactions_root / prepared / "manifest.json"
        value = json.loads(prepared_manifest.read_text(encoding="utf-8"))
        value["state"] = "prepared"
        prepared_manifest.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(prepared_manifest, 0o600)

        damaged_dir = trash_paths(self.root).transactions_root / "MMTTRASH-20260804T164200-ABCDEF123456"
        damaged_dir.mkdir(mode=0o700)
        (damaged_dir / "manifest.json").write_text("{broken", encoding="utf-8")
        os.chmod(damaged_dir / "manifest.json", 0o600)

        tracked = {
            path: path.read_bytes()
            for path in trash_paths(self.root).transactions_root.rglob("*")
            if path.is_file()
        }
        snapshot = read_transaction_overview(self.root)
        states = {entry.transaction_id: entry.state for entry in snapshot.entries}
        self.assertEqual("trashed", states[trashed])
        self.assertEqual("restored", states[restored])
        self.assertEqual("prepared", states[prepared])
        self.assertEqual("damaged", states[damaged_dir.name])
        self.assertTrue(snapshot.warnings)
        self.assertEqual(tracked, {path: path.read_bytes() for path in tracked})

    def test_filter_returns_only_requested_state(self) -> None:
        trashed = self.create_transaction("one.txt")
        restored = self.create_transaction("two.txt", restore=True)
        snapshot = read_transaction_overview(self.root)
        self.assertEqual(
            [trashed],
            [entry.transaction_id for entry in snapshot.filtered("trashed")],
        )
        self.assertEqual(
            [restored],
            [entry.transaction_id for entry in snapshot.filtered("restored")],
        )
        self.assertEqual((), snapshot.filtered("unknown"))

    def test_symlink_transaction_is_marked_damaged_without_following_target(self) -> None:
        transactions = trash_paths(self.root).transactions_root
        transactions.mkdir(parents=True, mode=0o700)
        os.chmod(transactions.parent.parent, 0o700)
        os.chmod(transactions.parent, 0o700)
        os.chmod(transactions, 0o700)
        target = self.root / "target"
        target.mkdir()
        link = transactions / "MMTTRASH-20260804T164200-123456ABCDEF"
        link.symlink_to(target, target_is_directory=True)
        before = tuple(target.iterdir())
        snapshot = read_transaction_overview(self.root)
        entry = next(item for item in snapshot.entries if item.transaction_id == link.name)
        self.assertEqual("damaged", entry.state)
        self.assertEqual(before, tuple(target.iterdir()))


if __name__ == "__main__":
    unittest.main()
