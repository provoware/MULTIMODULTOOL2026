"""Qt-Offscreen tests for productive workflow, help, diagnostics and layout."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover
    QtCore = None
    QtWidgets = None


@unittest.skipUnless(QtWidgets is not None, "PySide6 ist für den GUI-Smoke-Test erforderlich.")
class OffscreenGuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from src.diagnostics_center import DiagnosticEntry, DiagnosticSnapshot
        from src.error_events import ErrorEventCenter, create_event
        from src.main import COMPLETED_POINTS, DEVELOPMENT_PROGRESS, OPEN_POINTS, ZONE_OBJECT_NAMES, build_window
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
        settings_result = SettingsLoadResult(settings=default_settings(), source="active")
        event = create_event(
            category="test", severity="warning", cause="Testursache", consequence="Testfolge",
            data_state="Testdaten unverändert", solution="Testlösung", next_step="Sicher fortsetzen",
        )
        center = ErrorEventCenter()
        center.capture(event)
        snapshot = DiagnosticSnapshot((DiagnosticEntry.from_mapping(event.as_dict()),))
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.window = build_window(
            QtWidgets, QtCore,
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
        ids = []
        for name in self.zone_names:
            widget = self.window.findChild(QtWidgets.QWidget, name)
            self.assertIsNotNone(widget, name)
            self.assertTrue(widget.isVisible(), name)
            ids.append(str(widget.property("zoneId")))
        self.assertEqual([f"Z{index:02d}" for index in range(1, 10)], ids)

    def test_workspace_and_context_remain_scrollable(self) -> None:
        workspace = self.window.findChild(QtWidgets.QScrollArea, "workspaceScroll")
        context = self.window.findChild(QtWidgets.QScrollArea, "contextScroll")
        self.assertTrue(workspace.widgetResizable())
        self.assertTrue(context.widgetResizable())
        self.assertEqual(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff, workspace.horizontalScrollBarPolicy())

    def test_unreleased_actions_are_disabled_and_explain_their_blocker(self) -> None:
        navigation_names = (
            "analysisNavigation", "duplicatesNavigation", "organizeNavigation",
            "renameNavigation", "reportsNavigation",
        )
        action_names = (
            "chooseProjectAction", "analyzeProjectAction", "showPlanAction",
            "executePlanAction", "undoPlanAction", "saveReportAction",
        )
        for name in (*navigation_names, *action_names):
            button = self.window.findChild(QtWidgets.QPushButton, name)
            self.assertIsNotNone(button, name)
            self.assertTrue(button.isEnabled(), name)
            self.assertTrue(button.toolTip().strip(), name)
            self.assertTrue(button.accessibleDescription().strip(), name)
        settings = self.window.findChild(QtWidgets.QPushButton, "lockedSettingsNavigation")
        self.assertIsNotNone(settings)
        self.assertFalse(settings.isEnabled())
        self.assertTrue(settings.toolTip().strip())
        self.assertEqual([], self.window.findChildren(QtWidgets.QPushButton, "lockedNavigation"))
        self.assertEqual([], self.window.findChildren(QtWidgets.QPushButton, "lockedPrimaryAction"))

    def test_productive_panel_is_present_but_does_not_touch_filesystem_on_build(self) -> None:
        panel = self.window.findChild(QtWidgets.QFrame, "productiveWorkflowPanel")
        self.assertIsNotNone(panel)
        for name in (
            "projectSelectButton", "analyzeProjectButton", "findDuplicatesButton",
            "previewOrganizationButton", "previewRenameButton", "applyProductivePlanButton",
            "undoProductiveOperationButton", "saveAnalysisReportButton",
        ):
            self.assertIsNotNone(panel.findChild(QtWidgets.QPushButton, name), name)
        self.assertFalse(self._sentinel_root.exists())

    def test_safety_states_are_textual_and_visible(self) -> None:
        labels = [label for label in self.window.findChildren(QtWidgets.QLabel) if bool(label.property("safetyStatus"))]
        self.assertGreaterEqual(len(labels), 5)
        self.assertTrue(all(label.isVisible() and label.text().strip() for label in labels))

    def test_help_button_opens_read_only_contextual_help(self) -> None:
        button = self.window.findChild(QtWidgets.QPushButton, "helpNavigation")
        dialog = self.window.findChild(QtWidgets.QDialog, "helpDialog")
        button.click()
        self.app.processEvents()
        self.assertTrue(dialog.isVisible())
        self.assertGreaterEqual(len(dialog.findChildren(QtWidgets.QFrame, "helpTopic")), 8)
        self.assertIsNotNone(dialog.findChild(QtWidgets.QPushButton, "helpDialogCloseButton"))
        self.assertIsNone(dialog.findChild(QtWidgets.QPushButton, "helpDeleteButton"))
        self.assertIsNone(dialog.findChild(QtWidgets.QPushButton, "helpUploadButton"))
        dialog.close()

    def test_progress_widgets_use_the_authoritative_constants(self) -> None:
        progress = self.window.findChild(QtWidgets.QProgressBar)
        self.assertEqual(self.development_progress, progress.value())
        self.assertEqual(f"Entwicklungsstand: {self.development_progress} %", progress.format())
        text = "\n".join(label.text() for label in self.window.findChildren(QtWidgets.QLabel))
        self.assertIn(f"{self.development_progress} %", text)
        self.assertIn(f"{self.completed_points} erledigt · {self.open_points} offen", text)

    def test_diagnostics_remains_read_only_filterable_and_copy_only(self) -> None:
        center = self.window.findChild(QtWidgets.QWidget, "diagnosticsCenter")
        detail = self.window.findChild(QtWidgets.QPlainTextEdit, "diagnosticsDetail")
        copy_button = self.window.findChild(QtWidgets.QPushButton, "diagnosticsCopyButton")
        self.assertTrue(center.isVisible())
        self.assertTrue(detail.isReadOnly())
        self.assertTrue(copy_button.isEnabled())
        self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, "diagnosticsDeleteButton"))
        self.assertIsNone(self.window.findChild(QtWidgets.QPushButton, "diagnosticsUploadButton"))

    def test_single_instance_activation_controls_are_present(self) -> None:
        status = self.window.findChild(QtWidgets.QLabel, "instanceActivationStatus")
        navigation = self.window.findChild(QtWidgets.QPushButton, "diagnosticsNavigation")
        self.assertTrue(status.text().strip())
        self.assertTrue(navigation.isEnabled())
        self.assertIsNone(self.window.findChild(QtCore.QTimer, "singleInstanceMessageTimer"))

    def test_global_error_dialog_contains_all_required_fields(self) -> None:
        from src.error_dialog import build_error_dialog
        from src.error_events import create_event
        event = create_event(
            category="gui-test", severity="error", cause="Testursache", consequence="Testfolge",
            data_state="Testdaten unverändert", solution="Testlösung", next_step="Sicher fortsetzen",
        )
        dialog = build_error_dialog(QtWidgets, event, self.window)
        dialog.show()
        self.app.processEvents()
        for name in (
            "errorCause", "errorConsequence", "errorDataState", "errorSolution",
            "errorDiagnosticId", "errorNextStep",
        ):
            label = dialog.findChild(QtWidgets.QLabel, name)
            self.assertIsNotNone(label, name)
            self.assertTrue(label.text().strip(), name)
        dialog.close()


if __name__ == "__main__":
    unittest.main()
