"""Qt-Offscreen-Smoke-Test für Layout, Diagnose, Hilfe und globale Fehlerfelder."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - CI installiert PySide6 ausdrücklich.
    QtCore = None
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Smoke-Test erforderlich.")
class OffscreenGuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.diagnostics_center import DiagnosticEntry, DiagnosticSnapshot
        from src.error_events import ErrorEventCenter, create_event
        from src.main import (
            COMPLETED_POINTS,
            DEVELOPMENT_PROGRESS,
            OPEN_POINTS,
            ZONE_OBJECT_NAMES,
            build_window,
        )
        from src.settings_manager import SettingsLoadResult, default_settings
        from src.xdg_paths import XDGPaths

        cls._temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._temp.cleanup)
        root = Path(cls._temp.name) / "must-remain-absent"
        cls._sentinel_root = root
        paths = XDGPaths(
            config=root / "config",
            data=root / "data",
            cache=root / "cache",
            state=root / "state",
            logs=root / "state" / "logs",
            backups=root / "data" / "backups",
        )
        settings_result = SettingsLoadResult(
            settings=default_settings(),
            source="active",
        )
        event = create_event(
            category="test",
            severity="warning",
            cause="Testursache",
            consequence="Testfolge",
            data_state="Testdaten unverändert",
            solution="Testlösung",
            next_step="Sicher fortsetzen",
        )
        center = ErrorEventCenter()
        center.capture(event)
        diagnostic = DiagnosticEntry.from_mapping(event.as_dict())
        snapshot = DiagnosticSnapshot((diagnostic,))

        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.window = build_window(
            QtWidgets,
            QtCore,
            validation_text="GRÜN: Manifest gültig.",
            path_text="GRÜN: XDG-Pfadplan gültig.",
            settings_text="GRÜN: Einstellungen gültig.",
            paths=paths,
            settings_result=settings_result,
            diagnostics=snapshot,
            event_center=center,
        )
        cls.window.show()
        cls.app.processEvents()
        cls.zone_names = ZONE_OBJECT_NAMES
        cls.development_progress = DEVELOPMENT_PROGRESS
        cls.completed_points = COMPLETED_POINTS
        cls.open_points = OPEN_POINTS

    @classmethod
    def tearDownClass(cls) -> None:
        help_dialog = cls.window.findChild(QtWidgets.QDialog, "helpDialog")
        if help_dialog is not None:
            help_dialog.close()
        cls.window.close()
        cls.app.processEvents()

    def test_all_nine_layout_zones_exist_and_are_visible(self) -> None:
        self.assertEqual(9, len(self.zone_names))
        zone_ids: list[str] = []
        for name in self.zone_names:
            widget = self.window.findChild(QtWidgets.QWidget, name)
            self.assertIsNotNone(widget, name)
            self.assertTrue(widget.isVisible(), name)
            zone_ids.append(str(widget.property("zoneId")))
        self.assertEqual([f"Z{index:02d}" for index in range(1, 10)], zone_ids)

    def test_workspace_and_context_remain_scrollable(self) -> None:
        workspace = self.window.findChild(QtWidgets.QScrollArea, "workspaceScroll")
        context = self.window.findChild(QtWidgets.QScrollArea, "contextScroll")
        self.assertIsNotNone(workspace)
        self.assertIsNotNone(context)
        self.assertTrue(workspace.widgetResizable())
        self.assertTrue(context.widgetResizable())
        self.assertEqual(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            workspace.horizontalScrollBarPolicy(),
        )

    def test_safety_states_are_textual_and_visible(self) -> None:
        labels = [
            label
            for label in self.window.findChildren(QtWidgets.QLabel)
            if bool(label.property("safetyStatus"))
        ]
        self.assertGreaterEqual(len(labels), 3)
        self.assertTrue(all(label.isVisible() and label.text().strip() for label in labels))

    def test_unreleased_actions_are_disabled_and_explain_their_blocker(self) -> None:
        locked = self.window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction")
        navigation = self.window.findChildren(QtWidgets.QPushButton, "lockedNavigation")
        self.assertEqual(6, len(locked))
        self.assertEqual(5, len(navigation))
        for button in (*locked, *navigation):
            self.assertFalse(button.isEnabled())
            self.assertTrue(button.toolTip().strip())
            self.assertTrue(button.statusTip().strip())
            self.assertTrue(button.accessibleDescription().strip())
            self.assertTrue(
                button.testAttribute(QtCore.Qt.WidgetAttribute.WA_AlwaysShowToolTips)
            )

    def test_help_button_opens_read_only_contextual_help(self) -> None:
        button = self.window.findChild(QtWidgets.QPushButton, "helpNavigation")
        dialog = self.window.findChild(QtWidgets.QDialog, "helpDialog")
        self.assertIsNotNone(button)
        self.assertIsNotNone(dialog)
        self.assertTrue(button.toolTip().strip())
        button.click()
        self.app.processEvents()
        self.assertTrue(dialog.isVisible())
        topics = dialog.findChildren(QtWidgets.QFrame, "helpTopic")
        self.assertGreaterEqual(len(topics), 6)
        self.assertIsNotNone(dialog.findChild(QtWidgets.QPushButton, "helpDialogCloseButton"))
        self.assertIsNone(dialog.findChild(QtWidgets.QPushButton, "helpDeleteButton"))
        self.assertIsNone(dialog.findChild(QtWidgets.QPushButton, "helpUploadButton"))
        dialog.close()
        self.app.processEvents()

    def test_progress_widgets_use_the_authoritative_constants(self) -> None:
        progress = self.window.findChild(QtWidgets.QProgressBar)
        self.assertIsNotNone(progress)
        self.assertEqual(self.development_progress, progress.value())
        self.assertEqual(
            f"Entwicklungsstand: {self.development_progress} %",
            progress.format(),
        )
        label_text = "\n".join(label.text() for label in self.window.findChildren(QtWidgets.QLabel))
        self.assertIn(f"{self.development_progress} %", label_text)
        self.assertIn(
            f"{self.completed_points} erledigt · {self.open_points} offen",
            label_text,
        )

    def test_diagnostics_center_is_read_only_filterable_and_copy_only(self) -> None:
        center = self.window.findChild(QtWidgets.QWidget, "diagnosticsCenter")
        severity = self.window.findChild(QtWidgets.QComboBox, "diagnosticsSeverityFilter")
        query = self.window.findChild(QtWidgets.QLineEdit, "diagnosticsIdFilter")
        listing = self.window.findChild(QtWidgets.QListWidget, "diagnosticsList")
        detail = self.window.findChild(QtWidgets.QPlainTextEdit, "diagnosticsDetail")
        copy_button = self.window.findChild(QtWidgets.QPushButton, "diagnosticsCopyButton")
        self.assertTrue(center.isVisible())
        self.assertIsNotNone(severity)
        self.assertIsNotNone(query)
        self.assertGreaterEqual(listing.count(), 1)
        self.assertTrue(detail.isReadOnly())
        self.assertTrue(copy_button.isEnabled())
        self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, "diagnosticsDeleteButton"))
        self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, "diagnosticsUploadButton"))
        self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, "diagnosticsExportButton"))

    def test_single_instance_activation_controls_are_present(self) -> None:
        status = self.window.findChild(QtWidgets.QLabel, "instanceActivationStatus")
        timer = self.window.findChild(QtCore.QTimer, "singleInstanceMessageTimer")
        navigation = self.window.findChild(QtWidgets.QPushButton, "diagnosticsNavigation")
        self.assertIsNotNone(status)
        self.assertTrue(status.text().strip())
        self.assertIsNone(timer)  # Timer entsteht erst im echten run_gui-Lebenszyklus.
        self.assertTrue(navigation.isEnabled())

    def test_global_error_dialog_contains_all_required_fields(self) -> None:
        from src.error_dialog import build_error_dialog
        from src.error_events import create_event

        event = create_event(
            category="gui-test",
            severity="error",
            cause="Testursache",
            consequence="Testfolge",
            data_state="Testdaten unverändert",
            solution="Testlösung",
            next_step="Sicher fortsetzen",
        )
        dialog = build_error_dialog(QtWidgets, event, self.window)
        dialog.show()
        self.app.processEvents()
        for object_name in (
            "errorCause",
            "errorConsequence",
            "errorDataState",
            "errorSolution",
            "errorDiagnosticId",
            "errorNextStep",
        ):
            label = dialog.findChild(QtWidgets.QLabel, object_name)
            self.assertIsNotNone(label, object_name)
            self.assertTrue(label.text().strip(), object_name)
        dialog.close()

    def test_window_build_does_not_touch_user_data_paths(self) -> None:
        self.assertFalse(self._sentinel_root.exists())


if __name__ == "__main__":
    unittest.main()
