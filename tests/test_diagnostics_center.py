"""Tests der rein lesenden Diagnosezentrale."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from src.diagnostics_center import (
    DiagnosticEntry,
    filter_diagnostics,
    read_diagnostics,
)


def event(identifier: str, severity: str = "error") -> dict[str, str]:
    return {
        "timestamp_utc": "2026-08-04T12:00:00Z",
        "diagnostic_id": identifier,
        "category": "test",
        "severity": severity,
        "cause": "Testursache",
        "consequence": "Testfolge",
        "data_state": "Daten unverändert",
        "solution": "Testlösung",
        "next_step": "Sicher prüfen",
        "technical_detail": "",
    }


class DiagnosticReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "events.jsonl"

    def write_events(self, *values: dict[str, str]) -> None:
        self.path.write_text(
            "".join(json.dumps(value) + "\n" for value in values),
            encoding="utf-8",
        )
        os.chmod(self.path, 0o600)

    def test_missing_journal_is_empty_and_not_created(self) -> None:
        snapshot = read_diagnostics(self.path)
        self.assertEqual((), snapshot.entries)
        self.assertFalse(self.path.exists())

    def test_reader_is_read_only_and_keeps_bytes_unchanged(self) -> None:
        self.write_events(event("MMT-TEST-20260804-AAAA1111"))
        before = self.path.read_bytes()
        snapshot = read_diagnostics(self.path)
        self.assertEqual(1, len(snapshot.entries))
        self.assertEqual(before, self.path.read_bytes())

    def test_symlink_and_open_permissions_are_blocked(self) -> None:
        target = Path(self.temp.name) / "target.jsonl"
        target.write_text(json.dumps(event("MMT-TEST-20260804-BBBB2222")), encoding="utf-8")
        os.chmod(target, 0o600)
        self.path.symlink_to(target)
        with self.assertRaises(ValueError):
            read_diagnostics(self.path)
        self.path.unlink()
        self.write_events(event("MMT-TEST-20260804-CCCC3333"))
        os.chmod(self.path, 0o644)
        with self.assertRaises(ValueError):
            read_diagnostics(self.path)

    def test_invalid_lines_are_skipped_without_mutation(self) -> None:
        self.path.write_text(
            "{broken\n" + json.dumps(event("MMT-TEST-20260804-DDDD4444")) + "\n",
            encoding="utf-8",
        )
        os.chmod(self.path, 0o600)
        before = self.path.read_bytes()
        snapshot = read_diagnostics(self.path)
        self.assertEqual(1, len(snapshot.entries))
        self.assertEqual(1, len(snapshot.warnings))
        self.assertEqual(before, self.path.read_bytes())

    def test_filter_uses_severity_and_diagnostic_identifier(self) -> None:
        entries = (
            DiagnosticEntry.from_mapping(event("MMT-XDG-20260804-AAAA1111", "warning")),
            DiagnosticEntry.from_mapping(event("MMT-INSTANCE-20260804-BBBB2222", "error")),
        )
        self.assertEqual(1, len(filter_diagnostics(entries, severity="warning")))
        self.assertEqual(
            "MMT-INSTANCE-20260804-BBBB2222",
            filter_diagnostics(entries, diagnostic_query="instance")[0].diagnostic_id,
        )

    def test_record_limit_keeps_newest_complete_entries(self) -> None:
        self.write_events(
            event("MMT-TEST-20260804-AAAA1111"),
            event("MMT-TEST-20260804-BBBB2222"),
            event("MMT-TEST-20260804-CCCC3333"),
        )
        snapshot = read_diagnostics(self.path, maximum_records=2)
        self.assertTrue(snapshot.truncated)
        self.assertEqual(
            ["MMT-TEST-20260804-BBBB2222", "MMT-TEST-20260804-CCCC3333"],
            [item.diagnostic_id for item in snapshot.entries],
        )


if __name__ == "__main__":
    unittest.main()
