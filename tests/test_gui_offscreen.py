"""Qt-Offscreen-Smoke-Test für Layout, Diagnose und globale Fehlerfelder."""

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
        from src.main import ZONE_OBJECT_NAMES, build_window
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

    @classmethod
    def tearDownClass(cls) -> None:
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

    def test_unreleased_actions_are_disabled(self) -> None:
        locked = self.window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction")
        self.assertEqual(6, len(locked))
        self.assertTrue(all(not button.isEnabled() for button in locked))
        self.assertTrue(all(button.toolTip().strip() for button in locked))

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
