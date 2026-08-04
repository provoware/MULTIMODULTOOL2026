"""Real SIGKILL process-abort matrix for transactional long runs."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

from src.run_control import create_run, inspect_run, resume_run
from src.undo_redo import UndoRedoJournal


STAGES = (
    "before-intent",
    "after-intent",
    "before-file-operation",
    "after-file-operation",
    "before-fsync",
    "after-fsync",
    "before-manifest-completion",
    "after-manifest-completion",
    "before-journal-completion",
    "after-journal-completion",
)


@unittest.skipUnless(sys.platform.startswith("linux"), "SIGKILL-Matrix ist Linux-spezifisch.")
class RunControlSigkillTests(unittest.TestCase):
    def test_all_abort_stages_resume_to_one_complete_operation(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        for stage in STAGES:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                project = base / "project"
                project.mkdir(mode=0o700)
                source = project / "payload.txt"
                source.write_text("stable payload\n", encoding="utf-8")
                snapshot = create_run(project, [source])
                marker = base / f"killed-{stage}.marker"
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "tests.helpers.run_control_worker",
                        str(project),
                        snapshot.plan.run_id,
                        stage,
                        str(marker),
                    ],
                    cwd=repository_root,
                    env={**os.environ, "PYTHONPATH": str(repository_root)},
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30,
                )
                self.assertEqual(-signal.SIGKILL, completed.returncode, completed.stderr.decode("utf-8", "replace"))
                self.assertEqual(stage, marker.read_text(encoding="ascii").strip())

                resumed = resume_run(project, snapshot.plan.run_id)
                self.assertEqual("completed", resumed.state)
                second = resume_run(project, snapshot.plan.run_id)
                self.assertFalse(second.changed)

                final = inspect_run(project, snapshot.plan.run_id)
                self.assertEqual("completed", final.checkpoint.state)
                self.assertEqual((0,), final.checkpoint.completed_indices)
                self.assertIsNone(final.checkpoint.current_step)
                self.assertFalse(source.exists())

                actions = UndoRedoJournal(project).inspect().actions
                self.assertEqual(1, len(actions))
                self.assertEqual("trashed", actions[0].status)
                self.assertFalse(actions[0].pending_kind)

                transaction_root = project / ".multimodultool2026" / "trash" / "transactions"
                transaction_directories = [path for path in transaction_root.iterdir() if path.is_dir()]
                self.assertEqual(1, len(transaction_directories))
                self.assertTrue((transaction_directories[0] / "payload").is_file())
                self.assertTrue((transaction_directories[0] / "manifest.json").is_file())
                self.assertFalse(any(path.name.endswith(".tmp") for path in project.rglob("*")))


if __name__ == "__main__":
    unittest.main()
