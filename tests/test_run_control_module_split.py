"""Vertrag für die getrennten Laufmodelle und Prüffunktionen."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src import run_control as public
from src import run_control_models as models
from src import run_control_validation as validate
from src.error_events import SafeOperationError


class RunControlSplitContract(unittest.TestCase):
    def test_existing_module_still_exports_the_exact_model_classes(self) -> None:
        for name in (
            "RunPaths", "RunItem", "RunPlan", "CurrentStep",
            "RunCheckpoint", "RunSnapshot", "RunResult",
        ):
            self.assertIs(getattr(public, name), getattr(models, name))
        self.assertIs(public._parse_plan, validate._parse_plan)
        self.assertIs(public._parse_checkpoint, validate._parse_checkpoint)
        self.assertEqual(public.RUN_SCHEMA_VERSION, 1)

    def test_original_plan_and_checkpoint_json_schema_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Projekt"
            root.mkdir(mode=0o700)
            source = root / "original.txt"
            source.write_text("Nutzdatei", encoding="utf-8")
            snapshot = public.create_run(root, [source])
            plan_data = json.loads(snapshot.paths.plan_file.read_text(encoding="utf-8"))
            checkpoint_data = json.loads(
                snapshot.paths.checkpoint_file.read_text(encoding="utf-8")
            )
            self.assertEqual(validate._parse_plan(plan_data), snapshot.plan)
            self.assertEqual(
                validate._parse_checkpoint(checkpoint_data, snapshot.plan),
                snapshot.checkpoint,
            )
            self.assertEqual(set(plan_data), {
                "schemaVersion", "runId", "operation", "createdUtc",
                "items", "planHash",
            })
            self.assertEqual(set(checkpoint_data), {
                "schemaVersion", "runId", "planHash", "state",
                "nextIndex", "completedIndices", "attemptCounts",
                "currentStep", "generation", "createdUtc", "updatedUtc",
                "cancelRequested", "message",
            })
            self.assertEqual(source.read_text(encoding="utf-8"), "Nutzdatei")

            plan_data["unexpectedField"] = "must fail closed"
            with self.assertRaises(SafeOperationError):
                validate._parse_plan(plan_data)
            checkpoint_data["nextIndex"] = True
            with self.assertRaises(SafeOperationError):
                validate._parse_checkpoint(checkpoint_data, snapshot.plan)
            self.assertTrue(source.exists())


if __name__ == "__main__":
    unittest.main()
