"""Qt-Offscreen tests for guided start, productive workflow, help and layout."""

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
        for name in navigation_names:
            button = self.window.findChild(QtWidgets.QPushButton, name)
            self.assertIsNotNone(button, name)
            self.assertTrue(button.isEnabled(), name)
            self.assertTrue(button.toolTip().strip(), name)

        choose = self.window.findChild(QtWidgets.QPushButton, "chooseProjectAction")
        self.assertIsNotNone(choose)
        self.assertTrue(choose.isEnabled())
        self.assertIn("Startassistent", choose.text())
        self.assertTrue(choose.accessibleDescription().strip())

        for name in (
            "analyzeProjectAction", "showPlanAction", "executePlanAction",
            "undoPlanAction", "saveReportAction",
        ):
            button = self.window.findChild(QtWidgets.QPushButton, name)
            self.assertIsNotNone(button, name)
            self.assertFalse(button.isEnabled(), name)
            self.assertTrue(button.toolTip().strip(), name)

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
        self.assertTrue(panel.findChild(QtWidgets.QPushButton, "projectSelectButton").isEnabled())
        for name in (
            "analyzeProjectButton", "findDuplicatesButton", "previewOrganizationButton",
            "previewRenameButton", "applyProductivePlanButton", "undoProductiveOperationButton",
            "saveAnalysisReportButton",
        ):
            self.assertFalse(panel.findChild(QtWidgets.QPushButton, name).isEnabled(), name)
        self.assertFalse(self._sentinel_root.exists())

    def test_start_assistant_dialog_is_guided_and_read_only_on_build(self) -> None:
        from src.start_assistant import create_start_assistant_dialog

        dialog = create_start_assistant_dialog(QtWidgets, self.window)
        dialog.show()
        self.app.processEvents()
        self.assertEqual("startAssistantDialog", dialog.objectName())
        for name in (
            "assistantProjectField", "assistantTargetField", "assistantSafetyModeCombo",
            "assistantValidateButton", "assistantSummary", "assistantConfirmationCheck",
            "assistantAcceptButton", "assistantCancelButton",
        ):
            self.assertIsNotNone(dialog.findChild(QtWidgets.QWidget, name), name)
        self.assertTrue(dialog.findChild(QtWidgets.QLineEdit, "assistantProjectField").isReadOnly())
        self.assertTrue(dialog.findChild(QtWidgets.QLineEdit, "assistantTargetField").isReadOnly())
        self.assertTrue(dialog.findChild(QtWidgets.QPlainTextEdit, "assistantSummary").isReadOnly())
        self.assertEqual(3, dialog.findChild(QtWidgets.QComboBox, "assistantSafetyModeCombo").count())
        self.assertFalse(dialog.findChild(QtWidgets.QCheckBox, "assistantConfirmationCheck").isEnabled())
        self.assertFalse(dialog.findChild(QtWidgets.QPushButton, "assistantAcceptButton").isEnabled())
        self.assertFalse(self._sentinel_root.exists())
        dialog.close()

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
        self.assertGreaterEqual(len(dialog.findChildren(QtWidgets.QFrame, "helpTopic")), 9)
        text = "\n".join(label.text() for label in dialog.findChildren(QtWidgets.QLabel))
        self.assertIn("Startassistent", text)
        self.assertIn("Sicherheitsmodi", text)
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

    def test_z_safety_modes_gate_report_and_execution(self) -> None:
        from src.start_assistant import MODE_PRODUCTIVE, MODE_READ_ONLY, validate_start_selection

        panel = self.window.findChild(QtWidgets.QFrame, "productiveWorkflowPanel")
        project = Path(self._temp.name) / "assistant-project"
        target = project / "target"
        project.mkdir(exist_ok=True)
        target.mkdir(exist_ok=True)
        (project / "source.txt").write_text("source", encoding="utf-8")

        read_only = validate_start_selection(project, target, MODE_READ_ONLY)
        panel.apply_start_selection(read_only)
        self.assertTrue(panel.findChild(QtWidgets.QPushButton, "analyzeProjectButton").isEnabled())
        self.assertTrue(panel.findChild(QtWidgets.QPushButton, "previewOrganizationButton").isEnabled())
        self.assertFalse(panel.findChild(QtWidgets.QPushButton, "saveAnalysisReportButton").isEnabled())
        self.assertFalse(panel.findChild(QtWidgets.QPushButton, "applyProductivePlanButton").isEnabled())

        productive = validate_start_selection(project, target, MODE_PRODUCTIVE)
        panel.apply_start_selection(productive)
        self.assertTrue(panel.findChild(QtWidgets.QPushButton, "saveAnalysisReportButton").isEnabled())
        self.assertFalse(panel.findChild(QtWidgets.QPushButton, "applyProductivePlanButton").isEnabled())
        self.assertEqual("target", panel.target_relative)

        panel.start_selection = None
        panel.root = None
        panel.target_root = None
        panel.target_relative = ""
        panel._state(False)
        for name in (
            "analyzeProjectAction", "showPlanAction", "executePlanAction",
            "undoPlanAction", "saveReportAction",
        ):
            self.window.findChild(QtWidgets.QPushButton, name).setEnabled(False)


if __name__ == "__main__":
    unittest.main()
