"""Regressionstests für zentrale Fehler- und Ereignisschicht."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest

from src.error_events import (
    EVENT_FILE_MODE,
    EVENT_LOG_FILE_NAME,
    ErrorEventCenter,
    EventJournal,
    SafeOperationError,
    create_event,
    event_from_exception,
    event_from_settings_result,
    format_event_for_user,
    install_exception_hooks,
    sanitize_text,
)
from src.settings_manager import SettingsLoadResult, default_settings


class ErrorEventContractTests(unittest.TestCase):
    def test_event_contains_all_required_user_fields(self) -> None:
        event = create_event(
            category="test",
            severity="error",
            cause="Ursache",
            consequence="Folge",
            data_state="Unverändert",
            solution="Lösung",
            next_step="Nächster Schritt",
        )
        self.assertEqual((), event.missing_required_fields())
        rendered = format_event_for_user(event)
        for label in (
            "Ursache:",
            "Folge:",
            "Datenstand:",
            "Lösung:",
            "Diagnosekennung:",
            "Sicherer nächster Schritt:",
        ):
            self.assertIn(label, rendered)
        self.assertRegex(event.diagnostic_id, r"^MMT-TEST-\d{8}T\d{6}-[A-F0-9]{8}$")

    def test_secret_and_home_path_are_redacted(self) -> None:
        home = Path("/home/testperson")
        text = sanitize_text(
            "/home/testperson/Documents password=supersecret ghp_123456789012345678901234",
            home=home,
        )
        self.assertNotIn("/home/testperson", text)
        self.assertNotIn("supersecret", text)
        self.assertNotIn("ghp_", text)
        self.assertIn("~/Documents", text)
        self.assertIn("[GESCHÜTZT]", text)

    def test_safe_operation_error_preserves_user_contract(self) -> None:
        exception = SafeOperationError(
            cause="Zieldatei ist bereits vorhanden.",
            consequence="Verschieben wurde nicht gestartet.",
            data_state="Quelle und Ziel sind unverändert.",
            solution="Anderen Zielnamen wählen.",
            next_step="Vorschau erneut erzeugen.",
        )
        event = event_from_exception(exception)
        self.assertEqual("file-operation", event.category)
        self.assertEqual("Quelle und Ziel sind unverändert.", event.data_state)

    def test_settings_recovery_becomes_warning_event(self) -> None:
        result = SettingsLoadResult(
            settings=default_settings(),
            source="backup",
            warnings=["aktive Datei war beschädigt"],
            recovered=True,
        )
        event = event_from_settings_result(result)
        self.assertEqual("settings-recovery", event.category)
        self.assertEqual("warning", event.severity)
        self.assertIn("Produktive Nutzerdaten blieben unverändert", event.data_state)


class EventJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.logs = Path(self.temp.name) / "logs"
        self.logs.mkdir(mode=0o700)

    def test_journal_writes_private_valid_json_line(self) -> None:
        event = create_event(
            category="journal",
            severity="warning",
            cause="Test",
            consequence="Keine",
            data_state="Unverändert",
            solution="Keine",
            next_step="Weiter",
        )
        result = EventJournal(self.logs).record(event)
        self.assertTrue(result.success, result.error)
        path = self.logs / EVENT_LOG_FILE_NAME
        self.assertEqual(EVENT_FILE_MODE, stat.S_IMODE(path.stat().st_mode))
        payload = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertEqual(event.diagnostic_id, payload["diagnostic_id"])
        self.assertEqual("Unverändert", payload["data_state"])

    def test_symlink_log_file_is_blocked_without_touching_target(self) -> None:
        outside = Path(self.temp.name) / "outside.log"
        outside.write_text("unverändert", encoding="utf-8")
        (self.logs / EVENT_LOG_FILE_NAME).symlink_to(outside)
        event = create_event(
            category="journal",
            severity="error",
            cause="Test",
            consequence="Keine",
            data_state="Unverändert",
            solution="Keine",
            next_step="Weiter",
        )
        result = EventJournal(self.logs).record(event)
        self.assertFalse(result.success)
        self.assertEqual("unverändert", outside.read_text(encoding="utf-8"))

    def test_center_keeps_bounded_memory_and_records(self) -> None:
        center = ErrorEventCenter(EventJournal(self.logs), maximum_memory_events=2)
        for index in range(3):
            center.capture(
                create_event(
                    category="memory",
                    severity="info",
                    cause=f"Ereignis {index}",
                    consequence="Keine",
                    data_state="Unverändert",
                    solution="Keine",
                    next_step="Weiter",
                )
            )
        self.assertEqual(2, len(center.events))
        self.assertIn("Ereignis 2", center.latest.cause)
        self.assertEqual("", center.last_journal_error)


class ExceptionHookTests(unittest.TestCase):
    def test_sys_hook_captures_unhandled_exception(self) -> None:
        center = ErrorEventCenter()
        previous_sys, previous_thread = install_exception_hooks(center)
        try:
            try:
                raise RuntimeError("simulierter Fehler")
            except RuntimeError as exc:
                import sys

                sys.excepthook(type(exc), exc, exc.__traceback__)
            self.assertEqual(1, len(center.events))
            self.assertEqual("unhandled-main-thread", center.latest.category)
            self.assertIn("simulierter Fehler", center.latest.cause)
        finally:
            import sys

            sys.excepthook = previous_sys
            if previous_thread is not None:
                threading.excepthook = previous_thread


if __name__ == "__main__":
    unittest.main()
