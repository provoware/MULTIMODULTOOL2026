"""Regression tests for append-only undo/redo journal."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from src.error_events import SafeOperationError
from src.project_trash import execute_trash_move, preview_trash_move, restore_transaction
from src.undo_redo import (
    PRIVATE_DIRECTORY_MODE,
    PRIVATE_FILE_MODE,
    UndoRedoJournal,
    create_action_id,
)


class UndoRedoJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = UndoRedoJournal(self.root)

    def make_preview(self, name: str, content: str = "data"):
        source = self.root / name
        source.write_text(content, encoding="utf-8")
        return preview_trash_move(self.root, source)

    def test_read_only_inspection_does_not_create_history(self) -> None:
        before = tuple(self.root.iterdir())
        snapshot = self.journal.inspect()
        self.assertEqual((), snapshot.events)
        self.assertEqual(before, tuple(self.root.iterdir()))
        self.assertFalse(self.journal.paths.history_directory.exists())

    def test_private_hash_chained_journal_and_idempotent_record(self) -> None:
        preview = self.make_preview("alpha.txt")
        action_id = create_action_id()
        first = self.journal.record_trash(preview, action_id=action_id)
        second = self.journal.record_trash(preview, action_id=action_id)
        self.assertTrue(first.changed)
        self.assertFalse(second.changed)
        self.assertEqual(first.action_id, second.action_id)
        snapshot = self.journal.inspect()
        self.assertEqual(["prepare", "apply"], [event.event_kind for event in snapshot.events])
        self.assertEqual(1, snapshot.applied_count)
        self.assertEqual(
            PRIVATE_DIRECTORY_MODE,
            self.journal.paths.history_directory.stat().st_mode & 0o777,
        )
        self.assertEqual(
            PRIVATE_FILE_MODE,
            self.journal.paths.journal_file.stat().st_mode & 0o777,
        )
        self.assertEqual(snapshot.events[0].event_hash, snapshot.events[1].previous_hash)

    def test_ten_actions_are_undone_reverse_and_redone_forward(self) -> None:
        action_ids: list[str] = []
        for index in range(10):
            result = self.journal.record_trash(
                self.make_preview(f"item-{index}.txt", str(index))
            )
            action_ids.append(result.action_id)

        self.assertEqual(10, self.journal.inspect().applied_count)
        undone = [self.journal.undo_last().action_id for _ in range(10)]
        self.assertEqual(list(reversed(action_ids)), undone)
        self.assertEqual(10, self.journal.inspect().undone_count)
        for index in range(10):
            self.assertTrue((self.root / f"item-{index}.txt").is_file())

        redone = [self.journal.redo_next().action_id for _ in range(10)]
        self.assertEqual(action_ids, redone)
        self.assertEqual(10, self.journal.inspect().applied_count)
        for index in range(10):
            self.assertFalse((self.root / f"item-{index}.txt").exists())

    def test_explicit_undo_and_redo_are_idempotent(self) -> None:
        applied = self.journal.record_trash(self.make_preview("beta.txt"))
        first_undo = self.journal.undo_action(applied.action_id)
        second_undo = self.journal.undo_action(applied.action_id)
        self.assertTrue(first_undo.changed)
        self.assertFalse(second_undo.changed)
        first_redo = self.journal.redo_action(applied.action_id)
        second_redo = self.journal.redo_action(applied.action_id)
        self.assertTrue(first_redo.changed)
        self.assertFalse(second_redo.changed)

    def test_stack_order_conflicts_are_blocked(self) -> None:
        first = self.journal.record_trash(self.make_preview("first.txt"))
        second = self.journal.record_trash(self.make_preview("second.txt"))
        with self.assertRaises(SafeOperationError):
            self.journal.undo_action(first.action_id)
        self.journal.undo_action(second.action_id)
        self.journal.undo_action(first.action_id)
        with self.assertRaises(SafeOperationError):
            self.journal.redo_action(second.action_id)

    def test_new_action_is_blocked_while_redo_tail_exists(self) -> None:
        applied = self.journal.record_trash(self.make_preview("old.txt"))
        self.journal.undo_action(applied.action_id)
        with self.assertRaises(SafeOperationError):
            self.journal.record_trash(self.make_preview("new.txt"))

    def test_hash_tampering_is_detected_without_file_change(self) -> None:
        self.journal.record_trash(self.make_preview("tamper.txt"))
        path = self.journal.paths.journal_file
        lines = path.read_text(encoding="utf-8").splitlines()
        payload = json.loads(lines[0])
        payload["stateAfter"] = "restored"
        lines[0] = json.dumps(payload, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
        before = path.read_bytes()
        with self.assertRaises(SafeOperationError):
            self.journal.inspect()
        self.assertEqual(before, path.read_bytes())

    def test_symlink_journal_is_blocked_without_touching_target(self) -> None:
        self.journal.paths.control_directory.mkdir(mode=0o700)
        self.journal.paths.history_directory.mkdir(mode=0o700)
        target = self.root / "target.txt"
        target.write_text("unchanged", encoding="utf-8")
        self.journal.paths.journal_file.symlink_to(target)
        before = target.read_bytes()
        with self.assertRaises(SafeOperationError):
            self.journal.inspect()
        self.assertEqual(before, target.read_bytes())

    def test_pending_apply_is_reconciled_from_transaction_manifest(self) -> None:
        preview = self.make_preview("pending-apply.txt")
        action_id = create_action_id()
        self.journal._append(
            kind="prepare",
            action_id=action_id,
            transaction_id=preview.transaction_id,
            original_relative_path=preview.original_relative_path,
        )
        execute_trash_move(preview)
        snapshot = self.journal.reconcile()
        state = next(item for item in snapshot.actions if item.action_id == action_id)
        self.assertEqual("trashed", state.status)
        self.assertTrue(snapshot.events[-1].recovered)

    def test_pending_undo_is_reconciled_after_restore(self) -> None:
        applied = self.journal.record_trash(self.make_preview("pending-undo.txt"))
        state = self.journal.inspect().actions[0]
        self.journal._append(
            kind="undo-intent",
            action_id=state.action_id,
            transaction_id=state.current_transaction_id,
            original_relative_path=state.original_relative_path,
        )
        restore_transaction(self.root, state.current_transaction_id)
        snapshot = self.journal.reconcile()
        self.assertEqual("restored", snapshot.actions[0].status)
        self.assertTrue(snapshot.events[-1].recovered)
        self.assertEqual(applied.action_id, snapshot.actions[0].action_id)


if __name__ == "__main__":
    unittest.main()
