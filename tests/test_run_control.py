"""Regression tests for transactional long-run cancellation and restart."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import tempfile
import unittest

from src.error_events import SafeOperationError
from src.run_control import (
    CHECKPOINT_FILE_NAME,
    LOCK_FILE_NAME,
    create_run,
    inspect_run,
    request_cancel,
    resume_run,
)
from src.undo_redo import UndoRedoJournal


class RunControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir(mode=0o700)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _files(self, count: int) -> list[Path]:
        result: list[Path] = []
        for index in range(count):
            path = self.root / f"item-{index:02d}.txt"
            path.write_text(f"payload-{index}\n", encoding="utf-8")
            result.append(path)
        return result

    def test_create_run_has_private_immutable_plan_and_checkpoint(self) -> None:
        snapshot = create_run(self.root, self._files(2))
        before_plan = snapshot.paths.plan_file.read_bytes()
        before_checkpoint = snapshot.paths.checkpoint_file.read_bytes()
        inspected = inspect_run(self.root, snapshot.plan.run_id)
        self.assertEqual(snapshot.plan, inspected.plan)
        self.assertEqual(before_plan, snapshot.paths.plan_file.read_bytes())
        self.assertEqual(before_checkpoint, snapshot.paths.checkpoint_file.read_bytes())
        self.assertEqual(0o700, snapshot.paths.run_directory.stat().st_mode & 0o777)
        self.assertEqual(0o600, snapshot.paths.plan_file.stat().st_mode & 0o777)
        self.assertEqual(0o600, snapshot.paths.checkpoint_file.stat().st_mode & 0o777)

    def test_three_steps_complete_and_second_resume_is_idempotent(self) -> None:
        files = self._files(3)
        snapshot = create_run(self.root, files)
        first = resume_run(self.root, snapshot.plan.run_id)
        second = resume_run(self.root, snapshot.plan.run_id)
        self.assertEqual("completed", first.state)
        self.assertEqual(3, first.completed_count)
        self.assertEqual("completed", second.state)
        self.assertFalse(second.changed)
        self.assertTrue(all(not path.exists() for path in files))
        actions = UndoRedoJournal(self.root).inspect().actions
        self.assertEqual(3, len(actions))
        self.assertTrue(all(item.status == "trashed" and not item.pending_kind for item in actions))

    def test_step_limit_persists_and_resume_continues_without_duplicate(self) -> None:
        files = self._files(4)
        snapshot = create_run(self.root, files)
        partial = resume_run(self.root, snapshot.plan.run_id, max_steps=2)
        self.assertEqual("running", partial.state)
        self.assertEqual(2, partial.completed_count)
        completed = resume_run(self.root, snapshot.plan.run_id)
        self.assertEqual("completed", completed.state)
        self.assertEqual(4, len(UndoRedoJournal(self.root).inspect().actions))

    def test_cancel_is_acknowledged_only_between_steps_and_can_be_resumed(self) -> None:
        files = self._files(3)
        snapshot = create_run(self.root, files)
        partial = resume_run(self.root, snapshot.plan.run_id, max_steps=1)
        self.assertEqual(1, partial.completed_count)
        requested = request_cancel(self.root, snapshot.plan.run_id)
        self.assertTrue(requested.checkpoint.cancel_requested)
        cancelled = resume_run(self.root, snapshot.plan.run_id)
        self.assertEqual("cancelled", cancelled.state)
        self.assertEqual(1, cancelled.completed_count)
        unchanged = resume_run(self.root, snapshot.plan.run_id)
        self.assertFalse(unchanged.changed)
        completed = resume_run(self.root, snapshot.plan.run_id, allow_cancelled=True)
        self.assertEqual("completed", completed.state)
        self.assertEqual(3, completed.completed_count)
        self.assertTrue(all(not path.exists() for path in files))

    def test_plan_tampering_blocks_without_file_operation(self) -> None:
        source = self._files(1)[0]
        snapshot = create_run(self.root, [source])
        value = json.loads(snapshot.paths.plan_file.read_text(encoding="utf-8"))
        value["items"][0]["sourceRelativePath"] = "other.txt"
        snapshot.paths.plan_file.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(snapshot.paths.plan_file, 0o600)
        with self.assertRaises(SafeOperationError):
            resume_run(self.root, snapshot.plan.run_id)
        self.assertTrue(source.exists())

    def test_checkpoint_tampering_blocks_without_file_operation(self) -> None:
        source = self._files(1)[0]
        snapshot = create_run(self.root, [source])
        value = json.loads(snapshot.paths.checkpoint_file.read_text(encoding="utf-8"))
        value["nextIndex"] = 1
        snapshot.paths.checkpoint_file.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(snapshot.paths.checkpoint_file, 0o600)
        with self.assertRaises(SafeOperationError):
            resume_run(self.root, snapshot.plan.run_id)
        self.assertTrue(source.exists())

    def test_symlink_checkpoint_is_blocked(self) -> None:
        source = self._files(1)[0]
        snapshot = create_run(self.root, [source])
        target = snapshot.paths.run_directory / "outside.json"
        target.write_text("{}", encoding="utf-8")
        snapshot.paths.checkpoint_file.unlink()
        snapshot.paths.checkpoint_file.symlink_to(target)
        with self.assertRaises(SafeOperationError):
            inspect_run(self.root, snapshot.plan.run_id)
        self.assertTrue(source.exists())

    def test_cancel_request_does_not_compete_for_execution_lock(self) -> None:
        snapshot = create_run(self.root, self._files(2))
        lock_path = snapshot.paths.run_directory / LOCK_FILE_NAME
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            requested = request_cancel(self.root, snapshot.plan.run_id)
            self.assertTrue(requested.checkpoint.cancel_requested)
            self.assertTrue(snapshot.paths.cancel_file.is_file())
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def test_concurrent_run_lock_blocks_second_executor(self) -> None:
        snapshot = create_run(self.root, self._files(1))
        lock_path = snapshot.paths.run_directory / LOCK_FILE_NAME
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(SafeOperationError):
                resume_run(self.root, snapshot.plan.run_id)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def test_no_temporary_files_remain_after_completion(self) -> None:
        snapshot = create_run(self.root, self._files(2))
        resume_run(self.root, snapshot.plan.run_id)
        leftovers = [path for path in self.root.rglob("*") if path.name.startswith(".") and path.name.endswith(".tmp")]
        self.assertEqual([], leftovers)
        final = inspect_run(self.root, snapshot.plan.run_id)
        self.assertEqual("completed", final.checkpoint.state)
        self.assertIsNone(final.checkpoint.current_step)
        self.assertTrue((snapshot.paths.run_directory / CHECKPOINT_FILE_NAME).is_file())


if __name__ == "__main__":
    unittest.main()
