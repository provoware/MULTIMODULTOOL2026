"""Test-first Sicherheitsbasis vor einer späteren Trennung von run_control.py.

Alle Schreib- und Störfälle verwenden ausschließlich temporäre Projektordner.
Der laufende Anwendungs-Code wird durch diesen Test nicht verändert.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from src.error_events import SafeOperationError
from src.run_control import (
    MAXIMUM_CHECKPOINT_BYTES,
    create_run,
    inspect_run,
    request_cancel,
    resume_run,
    run_paths,
)


class RunControlRefactorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "projekt"
        self.project.mkdir(mode=0o700)
        self.source = self.project / "datei.txt"
        self.source.write_text("unveränderte Nutzdaten", encoding="utf-8")

    def test_hardlinked_plan_blocks_inspection_and_preserves_source(self) -> None:
        snapshot = create_run(self.project, [self.source])
        link = snapshot.paths.run_directory / "zweiter-plan-link"
        os.link(snapshot.paths.plan_file, link)
        try:
            with self.assertRaises(SafeOperationError):
                inspect_run(self.project, snapshot.plan.run_id)
            self.assertEqual(self.source.read_text(encoding="utf-8"), "unveränderte Nutzdaten")
        finally:
            link.unlink()

    def test_oversized_checkpoint_is_blocked_before_any_file_operation(self) -> None:
        snapshot = create_run(self.project, [self.source])
        payload = snapshot.checkpoint.as_dict()
        payload["message"] = "x" * MAXIMUM_CHECKPOINT_BYTES
        oversized_json = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.assertGreater(len(oversized_json), MAXIMUM_CHECKPOINT_BYTES)
        self.assertEqual(json.loads(oversized_json), payload)
        snapshot.paths.checkpoint_file.write_bytes(oversized_json)
        with self.assertRaises(SafeOperationError):
            resume_run(self.project, snapshot.plan.run_id)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "unveränderte Nutzdaten")

    def test_invalid_cancel_request_blocks_without_trashing_source(self) -> None:
        snapshot = create_run(self.project, [self.source])
        request_cancel(self.project, snapshot.plan.run_id)
        snapshot.paths.cancel_file.write_text("{broken-json", encoding="utf-8")

        with self.assertRaises(SafeOperationError):
            resume_run(self.project, snapshot.plan.run_id)

        self.assertEqual(self.source.read_text(encoding="utf-8"), "unveränderte Nutzdaten")
        self.assertEqual(inspect_run(self.project, snapshot.plan.run_id).checkpoint.state, "blocked")

    def test_invalid_run_id_does_not_escapes_project(self) -> None:
        with self.assertRaises(SafeOperationError):
            run_paths(self.project, "../../anderes-projekt")
        self.assertTrue(self.source.is_file())


if __name__ == "__main__":
    unittest.main()
