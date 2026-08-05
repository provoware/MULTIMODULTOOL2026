from pathlib import Path
import os
import tempfile
import unittest

from src.productive_workflow import (
    RenameRule,
    analyze_project,
    execute_operation,
    find_duplicates,
    operation_snapshot,
    reconcile_operation,
    resume_operation,
    plan_mass_rename,
    plan_organization,
    undo_operation,
    validate_project_root,
    write_analysis_report,
)


class ProductiveWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        (self.root / "a.txt").write_text("same", encoding="utf-8")
        (self.root / "b.txt").write_text("same", encoding="utf-8")
        (self.root / "photo.jpg").write_bytes(b"image")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "note.md").write_text("note", encoding="utf-8")

    def test_validate_and_analyze(self):
        project = validate_project_root(self.root)
        self.assertEqual(self.root, project.root)
        snapshot = analyze_project(self.root)
        self.assertEqual(4, len(snapshot.files))
        self.assertEqual(1, len(snapshot.directories))
        self.assertEqual(0, snapshot.symlink_count)

    def test_duplicate_search_is_read_only(self):
        snapshot = analyze_project(self.root)
        result = find_duplicates(snapshot)
        self.assertEqual(1, len(result.groups))
        self.assertEqual(("a.txt", "b.txt"), result.groups[0].relative_paths)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertFalse((self.root / ".multimodultool2026").exists())

    def test_mass_rename_and_undo(self):
        snapshot = analyze_project(self.root)
        plan = plan_mass_rename(snapshot, ["a.txt", "b.txt"], RenameRule(prefix="renamed_", add_number=True))
        result = execute_operation(self.root, plan)
        self.assertEqual("completed", result.state)
        self.assertFalse((self.root / "a.txt").exists())
        self.assertTrue((self.root / "renamed_a_001.txt").exists())
        self.assertTrue((self.root / "renamed_b_002.txt").exists())
        plan2, checkpoint = operation_snapshot(self.root, plan.operation_id)
        self.assertEqual(plan.plan_hash, plan2.plan_hash)
        self.assertEqual((0, 1), checkpoint.completed_indices)
        undone = undo_operation(self.root, plan.operation_id)
        self.assertEqual("undone", undone.state)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertTrue((self.root / "b.txt").exists())
        self.assertFalse((self.root / "renamed_a_001.txt").exists())

    def test_organization_and_undo(self):
        snapshot = analyze_project(self.root)
        plan = plan_organization(snapshot, rule="category", destination_root="Sortiert")
        result = execute_operation(self.root, plan)
        self.assertEqual("completed", result.state)
        self.assertTrue((self.root / "Sortiert" / "Dokumente" / "a.txt").exists())
        self.assertTrue((self.root / "Sortiert" / "Bilder" / "photo.jpg").exists())
        undo_operation(self.root, plan.operation_id)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertTrue((self.root / "photo.jpg").exists())

    def test_interruption_after_move_is_reconciled_and_resumed(self):
        snapshot = analyze_project(self.root)
        plan = plan_mass_rename(snapshot, ["a.txt", "b.txt"], RenameRule(prefix="safe_"))
        triggered = False

        def failpoint(stage, item):
            nonlocal triggered
            if stage == "after-file-operation" and item.index == 0 and not triggered:
                triggered = True
                raise OSError("simulated interruption")

        with self.assertRaises(Exception):
            execute_operation(self.root, plan, failpoint=failpoint)
        checkpoint = reconcile_operation(self.root, plan.operation_id)
        self.assertEqual((0,), checkpoint.completed_indices)
        self.assertTrue((self.root / "safe_a.txt").exists())
        resumed = resume_operation(self.root, plan.operation_id)
        self.assertEqual("completed", resumed.state)
        self.assertTrue((self.root / "safe_b.txt").exists())
        undo_operation(self.root, plan.operation_id)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertTrue((self.root / "b.txt").exists())

    def test_target_conflict_blocks_without_change(self):
        (self.root / "renamed_a.txt").write_text("occupied", encoding="utf-8")
        snapshot = analyze_project(self.root)
        with self.assertRaises(Exception):
            plan_mass_rename(snapshot, ["a.txt"], RenameRule(prefix="renamed_"))
        self.assertEqual("same", (self.root / "a.txt").read_text(encoding="utf-8"))

    def test_source_change_after_preview_blocks(self):
        snapshot = analyze_project(self.root)
        plan = plan_mass_rename(snapshot, ["a.txt"], RenameRule(prefix="x_"))
        (self.root / "a.txt").write_text("changed-longer", encoding="utf-8")
        with self.assertRaises(Exception):
            execute_operation(self.root, plan)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertFalse((self.root / "x_a.txt").exists())

    def test_symlink_is_never_followed(self):
        target = Path(self.temp.name) / "outside.txt"
        target.write_text("outside", encoding="utf-8")
        os.symlink(target, self.root / "outside-link")
        snapshot = analyze_project(self.root)
        link = next(entry for entry in snapshot.entries if entry.relative_path == "outside-link")
        self.assertEqual("symlink", link.entry_type)
        self.assertNotIn("outside-link", [entry.relative_path for entry in snapshot.files])

    def test_analysis_report_uses_relative_paths(self):
        snapshot = analyze_project(self.root)
        duplicates = find_duplicates(snapshot)
        json_path, md_path = write_analysis_report(snapshot, duplicates)
        text = json_path.read_text(encoding="utf-8")
        self.assertNotIn(str(self.root), text)
        self.assertIn("a.txt", text)
        self.assertEqual(0o600, json_path.stat().st_mode & 0o777)
        self.assertEqual(0o600, md_path.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
